from odoo import models, api
from datetime import datetime

# Heredamos el modelo res.users para agregar la funcionalidad de registro de intentos de inicio de sesión
class ResUsersLogin(models.Model):
    _inherit = 'res.users'

    # Sobrescribimos el método _login para registrar los intentos de inicio de sesión
    @classmethod
    def _login(cls, db, login, password, user_agent_env=None):
        auth_result = super()._login(db, login, password, user_agent_env=user_agent_env)

        try:
            with cls.pool.cursor() as cr:
                env = api.Environment(cr, 1, {}) # Usamos el ID de usuario 1 (administrador) para realizar las operaciones en la base de datos
                
                # Declaramos variables a usar.
                user = env['res.users'].sudo().search([('email', '=', login)], limit=1) # Buscamos el usuario en la tabla res.users.

                # Si no se encuentra el usuario, no registramos el intento de inicio de sesión
                if not user:
                    return auth_result
                
                usuario = user.partner_id.id # Obtenemos el ID del partner relacionado con el usuario.
                estado = 'exito' if auth_result else 'fallo' # Determinamos el estado del intento de inicio de sesión.
                ip = user_agent_env.get('REMOTE_ADDR', 'Desconocida') if user_agent_env else 'Desconocida' # Obtenemos la dirección IP del usuario.
                navegador = user_agent_env.get('HTTP_USER_AGENT', 'Desconocido') if user_agent_env else 'Desconocido' # Obtenemos el navegador del usuario. NO FUNCIONA, HAY QUE BUSCAR ALTERNATIVA.

                env['autenticacion.sesion.log'].sudo().create({
                    'partner_id': usuario, # Relación con el modelo res.partner para identificar al usuario.
                    'x_ip': ip, # Dirección IP del usuario.
                    'x_navegador': navegador, # Navegador del usuario. # TODO: Extraer el navegador correctamente ya que ahora mismo sale siempre en Desconocido porque el user agent no lo almacena y hay que buscar alternativa.
                    'x_fecha_inicio': datetime.now(), # Fecha y hora del intento de inicio de sesión.
                    'x_estado_intento': estado, # Estado del intento de inicio de sesión (éxito o fallo).
                    'x_intentos_fallidos': 0, # Contador de intentos fallidos. # TODO: Hacer que el contador incremente con cada intento de inicio de sesión fallido.
                })

                cr.commit() # Guardamos los cambios en la base de datos.

        # En caso de que ocurra algún error durante el proceso de registro del intento de inicio de sesión, simplemente lo ignoramos.
        except Exception:
            pass

        return auth_result # Devolvemos el resultado del intento de inicio de sesión (éxito o fallo).