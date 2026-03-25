from odoo import models, fields

class Usuario(models.Model):
    _inherit = 'res.partner' # Heredamos de res.partner

    # Configuración de los campos
    x_nivel_confianza = fields.Selection([
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto')
    ], string="Nivel de Confianza (IA)", default='medio') # Agregamos campo para establecer el nivel de confianza del usuario.

    x_limite_intentos = fields.Integer(string="Límite Intentos Máximos", default=3) # Agregamos campo de limite de intentos para el usuario.
    x_is_blocked = fields.Boolean(string="Bloqueo Manual/IA", default=False) # Agregamos campo para bloquear cuenta del usuario o desbloquearla.
    x_ultima_conexion = fields.Datetime(string="Última Conexión Exitosa") # Agregamos un campo para guardar la fecha de la última conexión exitosa.
    x_timestamp_bloqueo = fields.Datetime(string="Último Bloqueo de Cuenta.") # Agregamos un campo para guardar el tiempo en el que la cuenta fue bloqueada or última vez.
    
    x_session_log_ids = fields.One2many('autenticacion.sesion.log', 'partner_id', string="Logs de Acceso") # Relación para ver los logs desde la ficha del partner