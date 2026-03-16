from odoo import models, fields

class AutenticacionSesionLog(models.Model):
    _name = 'autenticacion.sesion.log'
    _description = 'Log de Auditoría de Seguridad'
    _order = 'x_fecha_inicio desc'

    partner_id = fields.Many2one('res.partner', string='Usuario', required=True, readonly=True) # Relación para extraer el usuario.
    admin_id = fields.Many2one('res.users', string='Admin Responsable') # Relación para extraer el administrador que ha supervisado la sesión.

    x_session_token = fields.Char(string='Token de Sesión', readonly=True) # Campo para guardar el token de sesión.
    x_fecha_inicio = fields.Datetime(string='Fecha Inicio', default=fields.Datetime.now, readonly=True) # Campo para guardar la fecha de inicio de sesión.
    x_fecha_cierre = fields.Datetime(string='Fecha de Cierre', readonly=True) # Campo para guardar la fecha de cierre de la sesión.
    
    x_intentos_fallidos = fields.Integer(string='Intentos Fallidos', readonly=True) # Campo para guardar los intentos fallidos.
    x_nivel_riesgo = fields.Selection([
        ('muy_bajo', 'Muy Bajo'),
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('critico', 'Crítico')
    ], string='Nivel de Riesgo', default='muy_bajo') # Campo para guardar el nivel de riesgo de la cuenta.
    
    x_alerta_seguridad = fields.Char(string='Alertas o eventos de seguridad', readonly=True) # Campo para guardar las alertas o eventos asociados.
    
    x_ip = fields.Char(string='Dirección IP', readonly=True) # Campo para guardar la dirección IP
    x_navegador = fields.Char(string='Navegador', readonly=True) # Campo para guardar el navegador desde donde se inició sesión.
    x_estado_intento = fields.Selection([
        ('exito', 'Éxito'),
        ('fallo', 'Fallo'),
        ('bloqueo', 'Bloqueo IA')
    ], string='Resultado', readonly=True) # Campo para guardar el estado del intento.