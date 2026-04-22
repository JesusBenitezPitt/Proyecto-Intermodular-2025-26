from odoo import models, fields, api
from sklearn.ensemble import IsolationForest
import pytz, logging

_logger = logging.getLogger(__name__)

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
        tz = pytz.timezone('Europe/Madrid')
        
        logs_previos = self.search_read(
            [('partner_id', '=', partner_id)], 
            ['x_fecha_inicio', 'x_intentos_fallidos', 'x_ip', 'x_navegador'],
            limit=100,
            order='x_fecha_inicio desc'
        )

        if len(logs_previos) < 10:
            return 'bajo'

        # === FEATURES DEL MODELO ===
        X = []
        ips_conocidas = set()
        navegadores_conocidos = set()
        
        for l in logs_previos:
            if l['x_fecha_inicio']:
                fecha_local = pytz.utc.localize(l['x_fecha_inicio']).astimezone(tz)
                X.append([
                    fecha_local.hour,
                    fecha_local.weekday(),
                    l['x_intentos_fallidos']
                ])
                ips_conocidas.add(l['x_ip'])
                navegadores_conocidos.add(l['x_navegador'])
        
        # === ENTRENAR EL MODELO ===
        clf = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100
        )
        clf.fit(X)
        
        # === ANÁLISIS DEL ACCESO ACTUAL ===
        from datetime import datetime
        dia_semana = datetime.now().weekday()
        
        prediccion = clf.predict([[hora_actual, dia_semana, intentos]])
        score = clf.score_samples([[hora_actual, dia_semana, intentos]])[0]
        
        # === CRITERIOS DE RIESGO (AJUSTADOS) ===
        es_anomalia_patron = prediccion[0] == -1 or score < -0.3
        es_muchos_intentos = intentos >= 3  # 3+ intentos = alto riesgo
        es_madrugada = hora_actual <= 6 or hora_actual >= 22  # Fuera de horario
        
        _logger.info(
            f"✓ Usuario {partner_id} | Hora: {hora_actual}h | Intentos: {intentos} | "
            f"Score: {score:.3f} | Anomalía patrón: {es_anomalia_patron}"
        )
        
        # === LÓGICA FINAL DE DECISIÓN ===
        # ALTO RIESGO si: (muchos intentos + madrugada) O (anomalía de patrón + intentos)
        if (es_muchos_intentos and es_madrugada) or (es_anomalia_patron and intentos > 0):
            return 'alto'
        else:
            return 'bajo'