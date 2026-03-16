from odoo import models

class ResUsersLogin(models.Model):
    _inherit = 'res.users'

    def _login(self, credential, user_agent_env=None):
        auth_result = super(ResUsersLogin, self)._login(credential, user_agent_env=user_agent_env) # Llamada al metodo original.
        
        # Lógica de desarrollo proximamente.
        
        return auth_result