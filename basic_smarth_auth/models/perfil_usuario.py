from odoo import models, fields, api

class AutenticacionSesionLog(models.Model):
    _name = 'autenticacion.sesion.log'
    _description = 'Registro de Sesiones de Usuario'

    usuario_id = fields.Many2one(
        'res.users', 
        string='Usuario', 
        required=True, 
        ondelete='cascade',
        readonly=True
    )
    
    fecha_sesion = fields.Datetime(
        string='Fecha/Hora de Conexión', 
        default=fields.Datetime.now, 
        readonly=True
    )

    estado_revision = fields.Selection(
        [('pendiente', 'Pendiente de Revisión'),
         ('revisado', 'Revisado')],
        string='Estado de Revisión',
        default='pendiente',
        required=True,
    )
    
    notas_admin = fields.Text(string='Notas del Administrador')