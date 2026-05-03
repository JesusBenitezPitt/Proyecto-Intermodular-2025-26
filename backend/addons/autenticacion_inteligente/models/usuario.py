from odoo import models, fields
from datetime import datetime, timedelta
import random
import logging

_logger = logging.getLogger(__name__)

class Usuario(models.Model):
    _inherit = 'res.partner'

    x_nivel_confianza = fields.Selection([
        ('bajo', 'Bajo'),
        ('alto', 'Alto')
    ], string="Nivel de confianza del usuario", default='bajo')
    x_limite_intentos = fields.Integer(string="Límite Intentos Máximos", default=3)
    x_is_blocked = fields.Boolean(string="Bloqueo Manual/IA", default=False)
    x_ultima_conexion = fields.Datetime(string="Última Conexión Exitosa")
    x_timestamp_bloqueo = fields.Datetime(string="Último Bloqueo de Cuenta")
    x_session_log_ids = fields.One2many('authentication.sesion.log', 'partner_id', string="Logs de Acceso")
    x_2fa_enabled = fields.Boolean(string='2FA Activo en Móvil', default=False)
    x_firebase_token = fields.Char(string='Token de Firebase')

    def action_ver_analisis_horario_individual(self):
        """ Abre una vista de gráfico filtrada solo para los accesos de este usuario """
        return {
            'name': f'Análisis de accesos de: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'authentication.sesion.log',
            'view_mode': 'graph',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'graph_groupbys': ['x_franja_horaria'],
                'graph_measure': '__count__',
                'graph_mode': 'bar',
            },
        }

    def action_simulacion_accesos(self):
        """ Genera datos de entrenamiento y casos de prueba con Geolocalización """
        log_model = self.env['authentication.sesion.log']
        
        # 1. Limpiar logs previos
        log_model.search([('partner_id', '=', self.id)]).unlink()

        # Coordenadas "Normales" (Tu ubicación de desarrollo/Docker)
        # Usamos las coordenadas que definimos en el método obtener_datos_geograficos
        lat_normal = 37.3891
        lng_normal = -5.9845
        loc_normal = "Desarrollo Local (Sevilla, ES)"

        _logger.info("\n=== Generando histórico de 10 días con Localización Fija ===")
        fecha_base = datetime.now() - timedelta(days=10)
        
        for dia in range(10):
            fecha_dia = fecha_base + timedelta(days=dia)
            if fecha_dia.weekday() < 5:
                # Entrada mañana
                log_model.create({
                    'partner_id': self.id,
                    'x_fecha_inicio': fecha_dia.replace(hour=random.randint(8, 10), minute=random.randint(0, 59)),
                    'x_intentos_fallidos': 0,
                    'x_estado_intento': 'exito',
                    'x_nivel_riesgo': 'bajo',
                    'x_localizacion': loc_normal,
                    'x_latitud': lat_normal,
                    'x_longitud': lng_normal,
                })
                
                # Entrada mediodía
                log_model.create({
                    'partner_id': self.id,
                    'x_fecha_inicio': fecha_dia.replace(hour=random.randint(12, 13), minute=random.randint(0, 59)),
                    'x_intentos_fallidos': 0,
                    'x_estado_intento': 'exito',
                    'x_nivel_riesgo': 'bajo',
                    'x_localizacion': loc_normal,
                    'x_latitud': lat_normal,
                    'x_longitud': lng_normal,
                })

        self.env.cr.commit()

        _logger.info("=== Evaluando casos de prueba ===")
        fecha_hoy = datetime.now()
        
        # CASO 1: Acceso normal (Misma ubicación, hora normal)
        hora_test_1 = 10
        riesgo_1 = log_model.analizar_anomalia(self.id, hora_test_1, 0, lat_normal, lng_normal)
        
        log_model.create({
            'partner_id': self.id,
            'x_fecha_inicio': fecha_hoy.replace(hour=hora_test_1, minute=15),
            'x_intentos_fallidos': 0,
            'x_estado_intento': 'exito',
            'x_nivel_riesgo': riesgo_1,
            'x_localizacion': loc_normal,
            'x_latitud': lat_normal,
            'x_longitud': lng_normal,
            'x_alerta_seguridad': 'Acceso normal desde ubicación conocida',
        })

        # CASO 2: Ataque (Ubicación diferente, por ejemplo: Tokyo, incluso en horario normal)
        lat_ataque = 35.6895
        lng_ataque = 139.6917
        riesgo_2 = log_model.analizar_anomalia(self.id, 3, 5, lat_ataque, lng_ataque)
        
        log_model.create({
            'partner_id': self.id,
            'x_fecha_inicio': fecha_hoy.replace(hour=10, minute=0),
            'x_intentos_fallidos': 1,
            'x_estado_intento': 'fallo',
            'x_nivel_riesgo': riesgo_2,
            'x_localizacion': 'Tokyo, JP',
            'x_latitud': lat_ataque,
            'x_longitud': lng_ataque,
            'x_alerta_seguridad': 'ANOMALÍA: Ubicación remota e intentos fallidos',
        })
        
        return {
            'type': 'ir.actions.client', 
            'tag': 'reload'
        }