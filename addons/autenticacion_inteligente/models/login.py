from odoo import models, api
from odoo.exceptions import AccessError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

INTENTOS = {}

# Heredamos el modelo res.users para agregar la funcionalidad de registro de intentos de inicio de sesión
class ResUsersLogin(models.Model):
    _inherit = 'res.users'

    # Sobrescribimos el método _login para registrar los intentos de inicio de sesión
    @classmethod
    def _login(cls, db, login, password, user_agent_env=None):
        auth_result = False # Inicializamos el resultado de la autenticación como falso.
        error_auth = None # Variable para almacenar cualquier error que ocurra durante el proceso de autenticación.

        try:
            auth_result = super()._login(db, login, password, user_agent_env=user_agent_env)
        except Exception as e:
            auth_result = False # Si ocurre una excepción durante el proceso de autenticación, consideramos que el intento de inicio de sesión ha fallado.
            error_auth = e

        estado = 'exito' if auth_result else 'fallo' # Determinamos el estado del intento de inicio de sesión.

        if estado == 'fallo':
            INTENTOS[login] = INTENTOS.get(login, 0) + 1 # Incrementamos el contador de intentos fallidos para el usuario en memoria.
            _logger.info("=== LOGIN DEBUG FALLO ===")
            _logger.info("Login: %s", login)
            _logger.info("Auth result: %s", auth_result)
            _logger.info("Estado: %s", estado)
            _logger.info("Intentos fallidos: %s", INTENTOS[login])
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
                    ip = user_agent_env.get('REMOTE_ADDR', 'Desconocida') if user_agent_env else 'Desconocida' # Obtenemos la dirección IP del usuario.
                    navegador = user_agent_env.get('HTTP_USER_AGENT', 'Desconocido') if user_agent_env else 'Desconocido' # Obtenemos el navegador del usuario. NO FUNCIONA, HAY QUE BUSCAR ALTERNATIVA.

                    _logger.info("=== LOGIN DEBUG ===")
                    _logger.info("Login: %s", login)
                    _logger.info("Auth result: %s", auth_result)
                    _logger.info("Estado: %s", estado)
                    _logger.info("Intentos fallidos: %s", intentos_fallidos)
                
                    # Comprobamos que el estado de inicio de sesión sea "fallo".
                    env['autenticacion.sesion.log'].sudo().create({
                        'partner_id': usuario, # Relación con el modelo res.partner para identificar al usuario.
                        'x_ip': ip, # Dirección IP del usuario.
                        'x_navegador': navegador, # Navegador del usuario. # TODO: Extraer el navegador correctamente ya que ahora mismo sale siempre en Desconocido porque el user agent no lo almacena y hay que buscar alternativa.
                        'x_fecha_inicio': datetime.now(), # Fecha y hora del intento de inicio de sesión.
                        'x_estado_intento': estado, # Estado del intento de inicio de sesión (éxito o fallo).
                        'x_intentos_fallidos': intentos_fallidos, # Contador de intentos fallidos. # TODO: Hacer que el contador incremente con cada intento de inicio de sesión fallido.
                    })

                    cr.commit() # Guardamos los cambios en la base de datos.

                    if login in INTENTOS:
                        del INTENTOS[login] # Si el inicio de sesión fue exitoso, eliminamos el contador de intentos fallidos para ese usuario en memoria.

            # En caso de que ocurra algún error durante el proceso de registro del intento de inicio de sesión, simplemente lo ignoramos.
            except Exception as e:
                _logger.error("Error al registrar el intento de inicio de sesión: %s", e)

        if error_auth:
            raise error_auth # Si ocurrió un error durante la autenticación, lanzamos una excepción guardada en error_auth.

        return auth_result # Devolvemos el resultado del intento de inicio de sesión (éxito o fallo).