from odoo import http, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class SecurityAppController(http.Controller):

    # Endpoint para login (Se mantiene igual, está perfecto)
    @http.route('/api/auth/login', type='json', auth='none', methods=['POST'], csrf=False)
    def login(self, **post):
        login = post.get('login')
        password = post.get('password')
        db = 'odoo' # Asegúrate de que este es el nombre de tu DB

        try:
            uid = request.session.authenticate(db, login, password)
            if not uid:
                return {'status': 'error', 'message': 'Credenciales inválidas'}

            user = request.env['res.users'].browse(uid)
            is_admin = user.has_group('base.group_system')
            partner = user.partner_id

            log_id = request.session.get('tfg_log_id')
            notif_id = request.session.get('tfg_notif_id')

            if partner.x_firebase_token:
                return {
                    'status': 'success',
                    'data': {
                        'user_id': user.id,
                        'partner_id': user.partner_id.id,
                        'name': user.name,
                        'is_admin': is_admin,
                        'session_id': request.session.sid,
                        'log_id': log_id,
                        'notification_id': notif_id,
                        'photo': user.partner_id.image_128.decode('utf-8') if user.partner_id.image_128 else None
                    }
                }
            else: 
                return {
                    'status': 'success',
                    'data': {
                        'user_id': user.id,
                        'partner_id': user.partner_id.id,
                        'name': user.name,
                        'is_admin': is_admin,
                        'session_id': request.session.sid,
                        'log_id': False,
                        'notification_id': notif_id,
                        'photo': user.partner_id.image_128.decode('utf-8') if user.partner_id.image_128 else None
                    }
                }
        except Exception as e:
            _logger.error("Error en login API: %s", str(e))
            return {'status': 'error', 'message': 'Error en el servidor'}

    # Endpoint para obtener los logs (Se mantiene igual)
    @http.route('/api/security/logs', type='json', auth='user', methods=['POST'], csrf=False)
    def get_logs(self, **post):
        user = request.env.user
        is_admin = user.has_group('base.group_system')
        
        domain = []
        if not is_admin:
            domain = [('partner_id', '=', user.partner_id.id)]

        logs = request.env['authentication.sesion.log'].sudo().search_read(
            domain, 
            ['x_fecha_inicio', 'x_intentos_fallidos', 'x_nivel_riesgo', 'x_estado_intento', 'x_ip', 'partner_id'],
            order='x_fecha_inicio desc'
        )

        result = []
        for log in logs:
            result.append({
                'id': log['id'],
                'fecha': log['x_fecha_inicio'],
                'intentos': log['x_intentos_fallidos'],
                'riesgo': log['x_nivel_riesgo'],
                'estado': log['x_estado_intento'],
                'usuario': log['partner_id'][1],
                'ip': log['x_ip']
            })

        return {'status': 'success', 'logs': result}

    @http.route('/api/security/notifications', type='json', auth='user', methods=['POST'], csrf=False)
    def get_notifications(self, **post):
        """ Obtiene las notificaciones reales de la tabla notificaciones.movil """
        user = request.env.user
        
        # Si es admin, ve todas. Si no, solo las suyas.
        domain = []
        if not user.has_group('base.group_system'):
            domain = [('x_user_id', '=', user.id)]
            
        notifications = request.env['notificaciones.movil'].sudo().search_read(
            domain, 
            ['x_titulo', 'x_mensaje', 'x_tipo_alerta', 'x_leida', 'create_date', 'x_log_id'],
            limit=20,
            order='create_date desc'
        )
        
        # Formateamos para que React Native lo procese limpio
        result = []
        for n in notifications:
            result.append({
                'id': n['id'],
                'titulo': n['x_titulo'],
                'mensaje': n['x_mensaje'],
                'tipo': n['x_tipo_alerta'],
                'leida': n['x_leida'],
                'fecha': n['create_date'],
                'log_id': n['x_log_id'][0] if n['x_log_id'] else None
            })
            
        return {'status': 'success', 'notifications': result}

    @http.route('/api/security/notifications/read', type='json', auth='user', methods=['POST'], csrf=False)
    def mark_notification_read(self, **post):
        """ Permite marcar una notificación como leída desde la App """
        notif_id = post.get('notification_id')
        if not notif_id:
            return {'status': 'error', 'message': 'ID no proporcionado'}
            
        notification = request.env['notificaciones.movil'].sudo().browse(notif_id)
        if notification.exists():
            notification.write({'x_leida': True})
            return {'status': 'success'}
        
        return {'status': 'error', 'message': 'Notificación no encontrada'}

    @http.route('/api/security/register_token', type='json', auth='user', methods=['POST'], csrf=False)
    def register_device_token(self, token, **post):
        user = request.env.user
        if user:
            user.sudo().write({
                'x_firebase_token': token,
                'x_2fa_enabled': True
            })
            return {'status': 'success', 'message': 'Token registrado correctamente'}
        return {'status': 'error', 'message': 'Usuario no autenticado'}

    @http.route('/api/security/validate_2fa', type='json', auth='user', methods=['POST'], csrf=False)
    def validate_2fa(self, notification_id, decision, **post):
        notif = request.env['notificaciones.movil'].sudo().browse(notification_id)
        if not notif or notif.x_user_id.id != request.env.user.id:
            return {'status': 'error', 'message': 'Notificación no encontrada'}

        notif.write({'x_estado_aprobacion': decision})

        if decision == 'denied':
            notif.x_user_id.partner_id.write({'x_is_blocked': True})
            notif.x_log_id.write({'x_alerta_seguridad': 'El usuario denegó el acceso desde la App.'})
            return {'status': 'blocked', 'message': 'Acceso denegado'}

        if decision == 'aproved':
            notif.x_log_id.write({'x_alerta_seguridad': 'Acceso verificado por el usuario vía App.'})
            return {'status': 'success', 'message': 'Acceso autorizado'}