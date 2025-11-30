from odoo import models, fields
import logging
try:
    from odoo.http import request
except Exception:
    request = None

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _login(self, credential, user_agent_env=None):
        auth_result = super(ResUsers, self)._login(credential, user_agent_env=user_agent_env)

        try:
            if not auth_result:
                return auth_result

            if isinstance(auth_result, dict):
                uid = auth_result.get('uid') or auth_result.get('user_id')
                auth_method = auth_result.get('auth_method')
                mfa = auth_result.get('mfa')
            else:
                uid = int(auth_result)
                auth_method = None
                mfa = None

            if not uid:
                _logger.warning("No se obtuvo uid válido de _login: %r", auth_result)
                return auth_result

            vals = {
                'usuario_id': uid,
                'fecha_sesion': fields.Datetime.now(),
                'estado_revision': 'pendiente',
            }

            log_model = self.env['autenticacion.sesion.log']
            log_model.sudo().create(vals)

        except Exception:
            _logger.exception("Error creando log de sesión para auth_result=%r", auth_result)

        return auth_result