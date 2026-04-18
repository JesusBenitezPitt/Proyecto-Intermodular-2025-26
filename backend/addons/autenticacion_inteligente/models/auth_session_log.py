from odoo import models, fields, api
from sklearn.ensemble import IsolationForest
import pytz

class AuthenticationSessionLog(models.Model):
    _name = 'authentication.sesion.log'
    _description = 'Log de Auditoría de Seguridad'
    _order = 'x_fecha_inicio desc'

    # --- CAMPOS DEL MODELO ---
    partner_id = fields.Many2one('res.partner', string='Usuario', required=True, readonly=True)
    admin_id = fields.Many2one('res.users', string='Admin Responsable')

    x_fecha_inicio = fields.Datetime(string='Fecha Inicio', default=fields.Datetime.now, readonly=True)
    x_intentos_fallidos = fields.Integer(string='Intentos Fallidos', readonly=True)
    
    x_nivel_riesgo = fields.Selection([
        ('bajo', 'Bajo'),
        ('alto', 'Alto')
    ], string='Nivel de Riesgo', default='bajo')
    
    x_alerta_seguridad = fields.Char(string='Alertas o eventos de seguridad', readonly=True)
    x_ip = fields.Char(string='Dirección IP', readonly=True)
    x_navegador = fields.Char(string='Navegador', readonly=True)
    
    x_estado_intento = fields.Selection([
        ('exito', 'Éxito'),
        ('fallo', 'Fallo'),
        ('bloqueo', 'Bloqueado')
    ], string='Resultado', readonly=True)

    # Campo calculado para organizar los gráficos por horas del día
    x_franja_horaria = fields.Char(string="Franja Horaria", compute="_compute_franja_horaria", store=True)

    @api.depends('x_fecha_inicio')
    def _compute_franja_horaria(self):
        """ Asigna una etiqueta horaria basada en la hora de España """
        tz = pytz.timezone('Europe/Madrid')
        
        for record in self:
            if record.x_fecha_inicio:
                # Convertimos la fecha de Odoo (UTC) a la hora local española
                fecha_local = pytz.utc.localize(record.x_fecha_inicio).astimezone(tz)
                hora = fecha_local.hour

                # Clasificación de la hora para facilitar estadísticas
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

    @api.model
    def analizar_anomalia(self, partner_id, hora_actual, intentos):
        """ Motor de IA que detecta si un acceso es sospechoso comparándolo con el historial """
        tz = pytz.timezone('Europe/Madrid')

        # Obtenemos los accesos pasados del usuario para aprender su patrón
        logs_previos = self.search_read([('partner_id', '=', partner_id)], ['x_fecha_inicio', 'x_intentos_fallidos'])
        
        # Necesitamos un mínimo de 5 registros para que la IA tenga datos suficientes
        if len(logs_previos) < 5:
            return 'bajo'

        # Preparamos la lista de datos (Hora e Intentos) para la IA
        X = []
        for l in logs_previos:
            if l['x_fecha_inicio']:
                # Aseguramos que la IA aprenda de horas locales, no UTC
                fecha_local = pytz.utc.localize(l['x_fecha_inicio']).astimezone(tz)
                X.append([fecha_local.hour, l['x_intentos_fallidos']])
        
        # Configuramos el modelo de detección (Isolation Forest)
        clf = IsolationForest(contamination=0.1, random_state=42)
        clf.fit(X)
        
        # Predecimos si el acceso actual se aleja mucho de lo normal
        prediccion = clf.predict([[hora_actual, intentos]])
        
        # Si la predicción es -1, es que ha detectado una anomalía
        return 'alto' if prediccion[0] == -1 else 'bajo'