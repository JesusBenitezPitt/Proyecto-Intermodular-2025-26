from odoo import http, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class SecurityAppController(http.Controller):

    # Endpoint para login
    @http.route('/api/auth/login', type='json', auth='none', methods=['POST'], csrf=False)
    def login(self, **post):
        login = post.get('login')
        password = post.get('password')
        db = 'odoo'

        try:
            # Intentamos autenticar en Odoo
            uid = request.session.authenticate(db, login, password)
            if not uid:
                return {'status': 'error', 'message': 'Credenciales inválidas'}

            user = request.env['res.users'].browse(uid)
            
            # Verificamos permisos reales de administración
            # base.group_system es el grupo de 'Ajustes' de Odoo
            is_admin = user.has_group('base.group_system')

            return {
                'status': 'success',
                'data': {
                    'user_id': user.partner_id.id,
                    'name': user.name,
                    'is_admin': is_admin,
                    'session_id': request.session.sid,
                }
            }
        except Exception as e:
            _logger.error("Error en login API: %s", str(e))
            return {'status': 'error', 'message': 'Error en el servidor'}

    # Endpoint para obtener los logs
    @http.route('/api/security/logs', type='json', auth='user', methods=['POST'])
    def get_logs(self, **post):
        user = request.env.user
        is_admin = user.has_group('base.group_system')
        
        # Lógica de filtrado:
        # Si es admin, ve todos.
        # Si no es admin, filtramos solo los suyos.
        domain = []
        if not is_admin:
            domain = [('partner_id', '=', user.partner_id.id)]

        logs = request.env['authentication.sesion.log'].sudo().search_read(
            domain, 
            ['x_fecha_inicio', 'x_intentos_fallidos', 'x_nivel_riesgo', 'x_estado_intento', 'x_ip', 'partner_id'],
            order='x_fecha_inicio desc'
        )

        # Formateamos para que se lea más fácil desde el frontend
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

        return {
            'status': 'success',
            'logs': result
        }

    # Endpoint para obtener notificaciones de seguridad (ejemplo: alertas de riesgo alto)
    @http.route('/api/security/notification', type='json', auth='user', methods=['POST'])
    def get_notifications(self, **post):
        # Aquí buscaríamos logs con riesgo 'alto'
        user = request.env.user
        domain = [('x_nivel_riesgo', '=', 'alto')]
        
        if not user.has_group('base.group_system'):
            domain.append(('partner_id', '=', user.partner_id.id))
            
        alerts = request.env['authentication.sesion.log'].search_read(
            domain, 
            ['x_fecha_inicio', 'x_alerta_seguridad'],
            limit=10,
            order='x_fecha_inicio desc'
        )
        return {'status': 'success', 'alerts': alerts}