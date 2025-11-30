from odoo import api, SUPERUSER_ID

def create_perfiles_usuarios(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    User = env['res.users']
    Perfil = env['autenticacion.perfil.usuario']

    users = User.search([])
    for u in users:
        if not Perfil.search([('usuario_id', '=', u.id)]):
            Perfil.create({'usuario_id': u.id})