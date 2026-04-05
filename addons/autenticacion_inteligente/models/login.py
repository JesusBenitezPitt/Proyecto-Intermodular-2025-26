from odoo import models, api
from odoo.exceptions import AccessError
from odoo.http import request
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

# Diccionario global para contar fallos en memoria (evita consultas constantes a DB)
INTENTOS = {}

class ResUsersLogin(models.Model):
    _inherit = 'res.users'

    @api.model
    def _parse_user_agent(self, ua_string):
        """ Identifica el navegador del usuario para guardarlo en el log """
        if not ua_string:
            return 'Desconocido'
        ua_string = str(ua_string)
        if 'Odoo' in ua_string: return 'Odoo App'
        if 'Edg' in ua_string: return 'Edge'
        if 'Chrome' in ua_string: return 'Chrome'
        if 'Firefox' in ua_string: return 'Firefox'
        if 'Safari' in ua_string: return 'Safari'
        return ua_string[:50]

    @classmethod
    def _login(cls, db, login, password, user_agent_env=None):
        """ 
        Sobrescritura del método de login original de Odoo para añadir 
        nuestra capa de Inteligencia Artificial y Seguridad.
        """
        auth_result = False
        error_auth = None

        # Capturamos datos del entorno (IP y Navegador)
        ip = request.httprequest.remote_addr or 'Desconocida'
        ua_raw = request.httprequest.user_agent.string or 'Desconocido'
        navegador = cls._parse_user_agent(cls, ua_raw)

        # 1. VERIFICACIÓN PREVIA: ¿La cuenta ya está bloqueada?
        with cls.pool.cursor() as cr:
            env = api.Environment(cr, 1, {})
            user = env['res.users'].sudo().search([('login', '=', login)], limit=1)
            if user and user.partner_id.x_is_blocked:
                _logger.warning("Acceso denegado: Usuario '%s' bloqueado.", login)
                raise AccessError("Cuenta bloqueada por seguridad. Contacte con el administrador.")

        # 2. INTENTO DE AUTENTICACIÓN REAL
        try:
            auth_result = super()._login(db, login, password, user_agent_env=user_agent_env)
        except Exception as e:
            auth_result = False
            error_auth = e

        estado = 'exito' if auth_result else 'fallo'

        # 3. GESTIÓN DE FALLOS Y BLOQUEOS
        if estado == 'fallo':
            # Incrementamos contador de fallos en el diccionario global
            INTENTOS[login] = INTENTOS.get(login, 0) + 1
            
            with cls.pool.cursor() as cr:
                env = api.Environment(cr, 1, {})
                user = env['res.users'].sudo().search([('login', '=', login)], limit=1)

                # Si supera el límite configurado en la ficha del usuario, bloqueamos
                if user and INTENTOS[login] >= user.partner_id.x_limite_intentos:
                    user.partner_id.write({
                        'x_is_blocked': True,
                        'x_timestamp_bloqueo': datetime.now(),
                    })

                    # Registramos el log de bloqueo definitivo
                    env['autenticacion.sesion.log'].sudo().create({
                        'partner_id': user.partner_id.id,
                        'x_ip': ip,
                        'x_navegador': navegador,
                        'x_fecha_inicio': datetime.now(),
                        'x_estado_intento': 'bloqueo', # Usamos la clave definida en el modelo
                        'x_intentos_fallidos': INTENTOS[login],
                        'x_nivel_riesgo': 'alto',
                        'x_alerta_seguridad': 'CUENTA BLOQUEADA: Exceso de intentos.'
                    })
                    cr.commit()
                    if login in INTENTOS: del INTENTOS[login]

                if error_auth: raise error_auth
        
        # 4. GESTIÓN DE ÉXITO Y ANÁLISIS DE IA
        else:
            try:
                with cls.pool.cursor() as cr:
                    env = api.Environment(cr, 1, {})
                    user = env['res.users'].sudo().search([('login', '=', login)], limit=1)

                    if not user: return auth_result
                    
                    intentos_previos = INTENTOS.get(login, 0)
                    
                    # LLAMADA A LA IA: Analizamos si este éxito es una anomalía horaria
                    log_obj = env['autenticacion.sesion.log'].sudo()
                    nivel_ia = log_obj.analizar_anomalia(user.partner_id.id, datetime.now().hour, intentos_previos)

                    # Actualizamos última conexión y creamos el registro de éxito
                    user.partner_id.write({'x_ultima_conexion': datetime.now()})
                    log_obj.create({
                        'partner_id': user.partner_id.id,
                        'x_ip': ip,
                        'x_navegador': navegador,
                        'x_fecha_inicio': datetime.now(),
                        'x_estado_intento': 'exito',
                        'x_intentos_fallidos': intentos_previos,
                        'x_nivel_riesgo': nivel_ia,
                        'x_alerta_seguridad': 'Acceso validado por IA: Riesgo %s' % nivel_ia
                    })
                    cr.commit()

                    # Limpiamos intentos fallidos de la memoria tras el éxito
                    if login in INTENTOS: del INTENTOS[login]

            except Exception as e:
                _logger.error("Error en el registro de log post-login: %s", e)

        return auth_result