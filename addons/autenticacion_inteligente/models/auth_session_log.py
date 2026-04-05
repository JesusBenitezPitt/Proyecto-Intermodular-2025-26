from odoo import models, fields, api
from sklearn.ensemble import IsolationForest
import pytz

class AutenticacionSesionLog(models.Model):
    _name = 'autenticacion.sesion.log'
    _description = 'Log de Auditoría de Seguridad'
    _order = 'x_fecha_inicio desc'

    partner_id = fields.Many2one('res.partner', string='Usuario', required=True, readonly=True) # Relación para extraer el usuario.
    admin_id = fields.Many2one('res.users', string='Admin Responsable') # Relación para extraer el administrador que ha supervisado la sesión.

    x_fecha_inicio = fields.Datetime(string='Fecha Inicio', default=fields.Datetime.now, readonly=True) # Campo para guardar la fecha de inicio de sesión.
    
    x_intentos_fallidos = fields.Integer(string='Intentos Fallidos', readonly=True) # Campo para guardar los intentos fallidos.
    x_nivel_riesgo = fields.Selection([
        ('bajo', 'Bajo'),
        ('alto', 'Alto')
    ], string='Nivel de Riesgo', default='bajo') # Campo para guardar el nivel de riesgo de la cuenta.
    
    x_alerta_seguridad = fields.Char(string='Alertas o eventos de seguridad', readonly=True) # Campo para guardar las alertas o eventos asociados.
    
    x_ip = fields.Char(string='Dirección IP', readonly=True) # Campo para guardar la dirección IP
    x_navegador = fields.Char(string='Navegador', readonly=True) # Campo para guardar el navegador desde donde se inició sesión.
    x_estado_intento = fields.Selection([
        ('exito', 'Éxito'),
        ('fallo', 'Fallo'),
        ('bloqueo', 'Bloqueo IA')
    ], string='Resultado', readonly=True) # Campo para guardar el estado del intento.

    x_franja_horaria = fields.Char(string="Franja Horaria", compute="_compute_franja_horaria", store=True)

    @api.depends('x_fecha_inicio')
    def _compute_franja_horaria(self):
        tz = pytz.timezone('Europe/Madrid')
        
        for record in self:
            if record.x_fecha_inicio:
                fecha_local = pytz.utc.localize(record.x_fecha_inicio).astimezone(tz)
                hora = fecha_local.hour

                if 0 <= hora <= 6:
                    record.x_franja_horaria = '1. Madrugada (00-06h)'
                elif 7 <= hora <= 12:
                    record.x_franja_horaria = '2. Mañana (07-12h)'
                elif 13 <= hora <= 20:
                    record.x_franja_horaria = '3. Tarde (13-20h)'
                else:
                    record.x_franja_horaria = '4. Noche (21-23h)'
            else:
                record.x_franja_horaria = 'Sin fecha'

    # TODO: Integrar geolocalización.
    @api.model
    def analizar_anomalia(self, partner_id, hora_actual, intentos):
        
        tz = pytz.timezone('Europe/Madrid')

        logs_previos = self.search_read([('partner_id', '=', partner_id)], ['x_fecha_inicio', 'x_intentos_fallidos'])
        
        if len(logs_previos) < 5:
            return 'bajo'

        X = []
        for l in logs_previos:
            if l['x_fecha_inicio']:
                fecha_local = pytz.utc.localize(l['x_fecha_inicio']).astimezone(tz)
                X.append([fecha_local.hour, l['x_intentos_fallidos']])
        
        clf = IsolationForest(contamination=0.1, random_state=42)
        clf.fit(X)
        
        prediccion = clf.predict([[hora_actual, intentos]])
        
        return 'alto' if prediccion[0] == -1 else 'bajo'