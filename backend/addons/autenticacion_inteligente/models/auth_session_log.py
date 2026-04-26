from odoo import models, fields, api
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
import pytz, logging
from datetime import datetime
import numpy as np

_logger = logging.getLogger(__name__)

class AuthenticationSessionLog(models.Model):
    _name = 'authentication.sesion.log'
    _description = 'Log de Auditoría de Seguridad'
    _order = 'x_fecha_inicio desc'

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
    x_franja_horaria = fields.Char(string="Franja Horaria", compute="_compute_franja_horaria", store=True)
    x_localizacion = fields.Char(string='Localización', readonly=True)
    x_latitud = fields.Float(string='Latitud', digits=(10, 7), readonly=True)
    x_longitud = fields.Float(string='Longitud', digits=(10, 7), readonly=True)

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

    @api.model
    def analizar_anomalia(self, partner_id, hora_actual, intentos, lat, lng):
        
        tz = pytz.timezone('Europe/Madrid')
        
        logs_previos = self.search_read(
            [('partner_id', '=', partner_id), ('x_nivel_riesgo', '=', 'bajo')],
            ['x_fecha_inicio', 'x_intentos_fallidos', 'x_latitud', 'x_longitud'],
            limit=200
        )

        if len(logs_previos) < 7:
            return 'bajo'

        X = []
        for l in logs_previos:
            if l['x_fecha_inicio']:
                f_local = pytz.utc.localize(l['x_fecha_inicio']).astimezone(tz)
                h = f_local.hour
                X.append([
                    np.sin(2 * np.pi * h / 24),
                    np.cos(2 * np.pi * h / 24),
                    l['x_intentos_fallidos'],
                    l['x_latitud'] or 0.0,
                    l['x_longitud'] or 0.0
                ])
        
        X_train = np.array(X)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        clf = OneClassSVM(kernel='rbf', gamma='auto', nu=0.05)
        clf.fit(X_train_scaled)
        
        dato_hoy = np.array([[
            np.sin(2 * np.pi * hora_actual / 24),
            np.cos(2 * np.pi * hora_actual / 24),
            intentos,
            lat,
            lng
        ]])
        
        dato_hoy_scaled = scaler.transform(dato_hoy)
        score = clf.decision_function(dato_hoy_scaled)[0]
        
        resultado = 'alto' if score < -0.01 else 'bajo'
        
        _logger.info(f"Analisis | Score: {score:.4f} | Riesgo: {resultado.upper()}")
        return resultado

    @api.model
    def obtener_datos_geograficos(self, ip):
        import requests
        if not ip or ip in ['127.0.0.1', 'localhost']:
            return {'texto': 'Local (España)', 'lat': 40.41, 'lng': -3.70}
            
        try:
            res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
            if res.get('status') == 'success':
                loc_txt = f"{res.get('city')}, {res.get('country')}"
                return {
                    'texto': loc_txt,
                    'lat': res.get('lat'),
                    'lng': res.get('lon')
                }
        except:
            pass
        return {'texto': 'Desconocida', 'lat': 0.0, 'lng': 0.0}

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AuthenticationSessionLog, self).create(vals_list)
        
        for rec in records:
            self._preparar_notificaciones(rec)
            
        return records

    def _preparar_notificaciones(self, log_record):
        user_target = self.env['res.users'].sudo().search([('partner_id', '=', log_record.partner_id.id)], limit=1)
        
        admins = self.env['res.users'].sudo().search([
            ('groups_id', 'in', self.env.ref('base.group_system').id)
        ])

        for admin in admins:
            if admin.id != user_target.id:
                self.env['notificaciones.movil'].sudo().create({
                    'x_user_id': admin.id,
                    'x_titulo': "Se ha detectado un intento de inicio de sesión",
                    'x_mensaje': f"Se ha detectado un nuevo intento de inicio de sesión desde {log_record.x_localizacion} para el usuario: {log_record.partner_id.name}, nivel de riesgo: {log_record.x_nivel_riesgo}.",
                    'x_tipo_alerta': 'warning',
                    'x_log_id': log_record.id
                })