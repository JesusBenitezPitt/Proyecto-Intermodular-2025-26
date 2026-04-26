from odoo import http
from odoo.http import request
import logging
import pytz

_logger = logging.getLogger(__name__)

class SecurityAppController(http.Controller):

    @http.route('/api/auth/login', type='json', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def login(self, **post):
        login = post.get('login')
        password = post.get('password')
        db = 'odoo'

        try:
            uid = request.session.authenticate(db, login, password)
            if not uid:
                return {'status': 'error', 'message': 'Credenciales inválidas'}

            user = request.env['res.users'].browse(uid)
            is_admin = user.has_group('base.group_system')
            partner = user.partner_id

            log_id = request.session.get('tfg_log_id')
            notif_id = request.session.get('tfg_notif_id')

            return {
                'status': 'success',
                'data': {
                    'user_id': user.id,
                    'partner_id': user.partner_id.id,
                    'name': user.name,
                    'is_admin': is_admin,
                    'session_id': request.session.sid,
                    'log_id': log_id if log_id else False,
                    'notification_id': notif_id if notif_id else False,
                    'photo': user.partner_id.image_128.decode('utf-8') if user.partner_id.image_128 else None
                }
            }
            
        except Exception as e:
            _logger.error("Error en login API: %s", str(e))
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/security/validate_2fa', type='json', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def validate_2fa(self, notification_id, decision, **post):
        """Valida la decisión del usuario sobre el acceso 2FA"""
        try:
            notif = request.env['notificaciones.movil'].sudo().browse(int(notification_id))
            
            if not notif.exists():
                return {'status': 'error', 'message': 'Notificación no encontrada'}

            # Actualizar estado
            notif.write({'x_estado_aprobacion': decision})
            
            _logger.info(f"Usuario {request.env.user.name} {decision} la notificación {notification_id}")

            if decision == 'denied':
                return {'status': 'blocked', 'message': 'Acceso denegado y cuenta bloqueada'}

            if decision == 'aproved':
                return {'status': 'success', 'message': 'Acceso autorizado correctamente'}
            
            return {'status': 'error', 'message': 'Decisión inválida'}
            
        except Exception as e:
            _logger.error(f"Error en validate_2fa: {e}")
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/security/notifications', type='json', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def get_notifications(self, **post):
        user = request.env.user
        
        domain = []
        if not user.has_group('base.group_system'):
            domain = [('x_user_id', '=', user.id)]
            
        notifications = request.env['notificaciones.movil'].sudo().search_read(
            domain, 
            ['x_titulo', 'x_mensaje', 'x_tipo_alerta', 'x_leida', 'create_date', 'x_log_id', 'x_estado_aprobacion', 'x_es_confirmacion_2fa'],
            limit=50,
            order='create_date desc'
        )
        
        result = []
        for n in notifications:
            result.append({
                'id': n['id'],
                'titulo': n['x_titulo'],
                'mensaje': n['x_mensaje'],
                'tipo': n['x_tipo_alerta'],
                'leida': n['x_leida'],
                'fecha': n['create_date'],
                'log_id': n['x_log_id'][0] if n['x_log_id'] else None,
                'estado_aprobacion': n['x_estado_aprobacion'],
                'es_confirmacion_2fa': n['x_es_confirmacion_2fa']
            })
            
        return {'status': 'success', 'notifications': result}

    @http.route('/api/security/register_token', type='json', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def register_device_token(self, token, **post):
        user = request.env.user
        if user:
            user.partner_id.sudo().write({'x_firebase_token': token})
            _logger.info(f"Token Firebase registrado para {user.name}")
            return {'status': 'success', 'message': 'Token registrado correctamente'}
        return {'status': 'error', 'message': 'Usuario no autenticado'}

    @http.route('/api/security/logs', type='json', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def get_logs(self, **post):
        try:
            user = request.env.user
            domain = []
            if not user.has_group('base.group_system'):
                domain = [('partner_id', '=', user.partner_id.id)]
            
            # Consultamos directamente el historial técnico de sesiones
            logs = request.env['authentication.sesion.log'].sudo().search(
                domain, 
                limit=50, 
                order='x_fecha_inicio desc'
            )
            
            tz = pytz.timezone('Europe/Madrid')

            logs_data = []
            for l in logs:
                # Riesgo: Solo alto o bajo
                riesgo_app = 'alto' if l.x_nivel_riesgo == 'alto' else 'bajo'
                
                # Estado simple: 'exito' o 'fallo'
                estado_app = 'exito' if l.x_estado_intento == 'exito' else 'fallo'

                fecha_utc = l.x_fecha_inicio
                fecha_madrid = pytz.utc.localize(fecha_utc).astimezone(tz)

                fecha_formateada = fecha_madrid.strftime('%d/%m/%Y %H:%M')

                logs_data.append({
                    'id': l.id,
                    'fecha': fecha_formateada,
                    'riesgo': riesgo_app,
                    'usuario': l.partner_id.name or 'Desconocido',
                    'ip': l.x_ip or '0.0.0.0',
                    'estado': estado_app, 
                })
                
            return {'status': 'success', 'logs': logs_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        
    @http.route('/api/security/notifications/read', type='json', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def mark_notification_as_read(self, **post):
        try:
            notification_id = post.get('notification_id')
            if not notification_id:
                return {'status': 'error', 'message': 'ID de notificación no proporcionado'}

            notification = request.env['notificaciones.movil'].sudo().browse(notification_id)
            
            if notification.exists():
                if notification.x_user_id.id != request.env.user.id:
                    return {'status': 'error', 'message': 'No tienes permiso para modificar esta notificación'}
                
                notification.write({'x_leida': True})
                
                return {
                    'status': 'success',
                    'message': 'Notificación marcada como leída'
                }
            else:
                return {'status': 'error', 'message': 'Notificación no encontrada'}

        except Exception as e:
            _logger.error(f"Error al marcar notificación como leída: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/security/logout', type='json', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def logout_cleanup(self, **post):
        try:
            user = request.env.user

            user.partner_id.sudo().write({
                'x_firebase_token': False,
                'x_2fa_enabled': False
            })
            return {'status': 'success', 'message': 'Token eliminado correctamente'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/security/notifications/count', type='json', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def get_unread_count(self, **post):
        try:
            count = request.env['notificaciones.movil'].sudo().search_count([
                ('x_user_id', '=', request.env.user.id),
                ('x_leida', '=', False)
            ])
            return {'status': 'success', 'unread_count': count}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        
    @http.route('/api/security/notification/details', type='json', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def get_notification_details(self, **post):
        params = request.params
        notif_id = params.get('notification_id')
        
        if not notif_id:
            return {'status': 'error', 'message': 'Falta el ID de notificación'}

        try:
            notif = request.env['notificaciones.movil'].sudo().browse(int(notif_id))
            
            if notif.exists() and notif.x_log_id:
                log = notif.x_log_id
                
                tz = pytz.timezone('Europe/Madrid')
                fecha_madrid = pytz.utc.localize(log.x_fecha_inicio).astimezone(tz)

                return {
                    'status': 'success',
                    'ip': log.x_ip or 'Desconocida',
                    'ubicacion': log.x_localizacion or 'Ubicación desconocida',
                    'navegador': log.x_navegador or 'Desconocido',
                    'fecha': fecha_madrid.strftime('%d/%m/%Y %H:%M')
                }
            
            return {'status': 'error', 'message': 'No se encontraron detalles del log'}
            
        except Exception as e:
            _logger.error(f"Error obteniendo detalles: {str(e)}")
            return {'status': 'error', 'message': str(e)}