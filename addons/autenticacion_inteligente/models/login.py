from odoo import models, api
from odoo.exceptions import AccessError
from odoo.http import request
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

INTENTOS = {}

# Heredamos el modelo res.users para agregar la funcionalidad de registro de intentos de inicio de sesión
class ResUsersLogin(models.Model):
    _inherit = 'res.users'

    @api.model
    def _parse_user_agent(self, ua_string):
        if not ua_string:
            return 'Desconocido'
        ua_string = str(ua_string) # Aseguramos que el user agent sea una cadena de texto para evitar errores al buscar subcadenas.
        if 'Odoo' in ua_string: return 'Odoo App'
        if 'Edg' in ua_string: return 'Edge'
        if 'Chrome' in ua_string: return 'Chrome'
        if 'Firefox' in ua_string: return 'Firefox'
        if 'Safari' in ua_string: return 'Safari'
        return ua_string[:50] # Cortamos para que quepa bien en el char.

    # Sobrescribimos el método _login para registrar los intentos de inicio de sesión
    @classmethod
    def _login(cls, db, login, password, user_agent_env=None):
        auth_result = False # Inicializamos el resultado de la autenticación como falso.
        error_auth = None # Variable para almacenar cualquier error que ocurra durante el proceso de autenticación.

        ip = request.httprequest.remote_addr or 'Desconocida'
        ua_raw = request.httprequest.user_agent.string or 'Desconocido'
        _logger.info("Intento de inicio de sesión. Usuario: '%s', IP: '%s', User Agent: '%s'", login, ip, ua_raw)

        # Parseamos el user agent.
        if 'Chrome' in ua_raw: navegador = 'Chrome'
        elif 'Firefox' in ua_raw: navegador = 'Firefox'
        elif 'Safari' in ua_raw: navegador = 'Safari'
        elif 'Edge' in ua_raw: navegador = 'Edge'
        else: navegador = ua_raw[:50]

        with cls.pool.cursor() as cr:
            env = api.Environment(cr, 1, {})
            user = env['res.users'].sudo().search([('login', '=', login)], limit=1)
            if user and user.partner_id.x_is_blocked:
                _logger.warning("El usuario '%s' esta bloqueado.", login)
                raise AccessError("La cuenta de este usuario está bloqueada debido a múltiples intentos de inicio de sesión fallidos. Por favor, contacte con el administrador para desbloquear su cuenta.")

        try:
            auth_result = super()._login(db, login, password, user_agent_env=user_agent_env)
        except Exception as e:
            auth_result = False # Si ocurre una excepción durante el proceso de autenticación, consideramos que el intento de inicio de sesión ha fallado.
            error_auth = e

        estado = 'exito' if auth_result else 'fallo' # Determinamos el estado del intento de inicio de sesión.

        if estado == 'fallo':
            INTENTOS[login] = INTENTOS.get(login, 0) + 1 # Incrementamos el contador de intentos fallidos para el usuario en memoria.
            _logger.info("Intento de inicio de sesión fallido para el usuario '%s'. Intentos fallidos: %d", login, INTENTOS[login])
            with cls.pool.cursor() as cr:
                env = api.Environment(cr, 1, {}) # Usamos el ID de usuario 1 (administrador) para realizar las operaciones en la base de datos
                user = env['res.users'].sudo().search([('login', '=', login)], limit=1)

                if user and INTENTOS[login] >= user.partner_id.x_limite_intentos: # Si el usuario existe y ha alcanzado el límite de intentos fallidos, bloqueamos la cuenta.
                    _logger.warning("El usuario '%s' ha alcanzado el límite de intentos fallidos. Bloqueando la cuenta.", login)
                    user.partner_id.write({
                        'x_is_blocked': True, # Marcamos la cuenta del usuario como bloqueada.
                        'x_timestamp_bloqueo': datetime.now(), # Guardamos la fecha y hora del bloqueo de la cuenta.
                    })

                    intentos_fallidos = INTENTOS.get(login, 0) # Obtenemos el número de intentos fallidos para el usuario desde memoria.
                    usuario = user.partner_id.id # Obtenemos el ID del partner relacionado con el usuario.
                    # ip = user_agent_env.get('REMOTE_ADDR', 'Desconocida') if user_agent_env else 'Desconocida' # Obtenemos la dirección IP del usuario.

                    env['autenticacion.sesion.log'].sudo().create({
                        'partner_id': usuario, # Relación con el modelo res.partner para identificar al usuario.
                        'x_ip': ip, # Dirección IP del usuario.
                        'x_navegador': navegador, # Navegador del usuario. # TODO: Extraer el navegador correctamente ya que ahora mismo sale siempre en Desconocido porque el user agent no lo almacena y hay que buscar alternativa.
                        'x_fecha_inicio': datetime.now(), # Fecha y hora del intento de inicio de sesión.
                        'x_estado_intento': estado, # Estado del intento de inicio de sesión (éxito o fallo).
                        'x_intentos_fallidos': intentos_fallidos, # Contador de intentos fallidos.
                    })

                    cr.commit() # Guardamos los cambios en la base de datos.
                    _logger.warning("La cuenta del usuario '%s' ha sido bloqueada debido a múltiples intentos de inicio de sesión fallidos.", login) 

                if error_auth:
                    raise error_auth # Si ocurrió un error durante la autenticación, lanzamos una excepción guardada en error_auth.
        else:
            try:
                with cls.pool.cursor() as cr:
                    env = api.Environment(cr, 1, {}) # Usamos el ID de usuario 1 (administrador) para realizar las operaciones en la base de datos
                    
                    # Declaramos variables a usar.
                    user = env['res.users'].sudo().search([('login', '=', login)], limit=1) # Buscamos el usuario en la tabla res.users.

                    # Si no se encuentra el usuario, no registramos el intento de inicio de sesión
                    if not user:
                        return auth_result
                    
                    intentos_fallidos = INTENTOS.get(login, 0) # Obtenemos el número de intentos fallidos para el usuario desde memoria.
                    usuario = user.partner_id.id # Obtenemos el ID del partner relacionado con el usuario.

                    _logger.info("=== LOGIN DEBUG ===")
                    _logger.info("Login: %s", login)
                    _logger.info("Auth result: %s", auth_result)
                    _logger.info("Estado: %s", estado)
                    _logger.info("Intentos fallidos: %s", intentos_fallidos)
                
                    user.partner_id.write({'x_ultima_conexion': datetime.now()}) # Actualizamos la fecha de la última conexión exitosa del usuario.

                    env['autenticacion.sesion.log'].sudo().create({
                        'partner_id': usuario, # Relación con el modelo res.partner para identificar al usuario.
                        'x_ip': ip, # Dirección IP del usuario.
                        'x_navegador': navegador, # Navegador del usuario. # TODO: Extraer el navegador correctamente ya que ahora mismo sale siempre en Desconocido porque el user agent no lo almacena y hay que buscar alternativa.
                        'x_fecha_inicio': datetime.now(), # Fecha y hora del intento de inicio de sesión.
                        'x_estado_intento': estado, # Estado del intento de inicio de sesión (éxito o fallo).
                        'x_intentos_fallidos': intentos_fallidos, # Contador de intentos fallidos.
                    })

                    cr.commit() # Guardamos los cambios en la base de datos.

                    if login in INTENTOS:
                        del INTENTOS[login] # Si el inicio de sesión fue exitoso, eliminamos el contador de intentos fallidos para ese usuario en memoria.

            # En caso de que ocurra algún error durante el proceso de registro del intento de inicio de sesión, simplemente lo ignoramos.
            except Exception as e:
                _logger.error("Error al registrar el intento de inicio de sesión: %s", e)

        return auth_result # Devolvemos el resultado del intento de inicio de sesión (éxito o fallo).