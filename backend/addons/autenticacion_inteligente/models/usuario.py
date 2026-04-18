from odoo import models, fields
from datetime import datetime
import random

class Usuario(models.Model):
    _inherit = 'res.partner' # Extendemos el modelo de contactos de Odoo

    # --- CONFIGURACIÓN DE SEGURIDAD DEL USUARIO ---
    x_nivel_confianza = fields.Selection([
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto')
    ], string="Nivel de Confianza (IA)", default='medio')

    x_limite_intentos = fields.Integer(string="Límite Intentos Máximos", default=3)
    x_is_blocked = fields.Boolean(string="Bloqueo Manual/IA", default=False)
    x_ultima_conexion = fields.Datetime(string="Última Conexión Exitosa")
    x_timestamp_bloqueo = fields.Datetime(string="Último Bloqueo de Cuenta")
    
    # Relación inversa para mostrar los logs de este usuario específico
    x_session_log_ids = fields.One2many('authentication.sesion.log', 'partner_id', string="Logs de Acceso")

    def action_ver_analisis_horario_individual(self):
        """ Abre una vista de gráfico filtrada solo para los accesos de este usuario """
        return {
            'name': f'Análisis de accesos de: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'authentication.sesion.log',
            'view_mode': 'graph',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'graph_groupbys': ['x_franja_horaria'], # Agrupa por las franjas (Madrugada, Mañana...)
                'graph_measure': '__count__',           # Cuenta el número de registros
                'graph_mode': 'bar',                    # Gráfico de barras
            },
        }

    def action_simulacion_accesos(self):
        """ Genera datos de prueba para entrenar y testear el comportamiento de la IA """
        
        # 1. GENERACIÓN DE PATRÓN NORMAL (Entrenamiento)
        # Creamos 10 registros en horario laboral (9h a 18h)
        for i in range(10):
            hora_random = random.randint(9, 18)
            self.env['authentication.sesion.log'].create({
                'partner_id': self.id,
                'x_fecha_inicio': datetime.now().replace(hour=hora_random),
                'x_ip': f'127.0.0.{i}',
                'x_navegador': 'Safari',
                'x_intentos_fallidos': random.randint(0, 2),
                'x_estado_intento': 'exito',
                'x_nivel_riesgo': 'bajo',
            })

        # 2. PRUEBA DE FUEGO PARA LA IA
        log_model = self.env['authentication.sesion.log']

        # Caso A: Acceso dentro del horario habitual (Debe ser riesgo BAJO)
        riesgo_a = log_model.analizar_anomalia(self.id, 14, 0)
        log_model.create({
            'partner_id': self.id,
            'x_fecha_inicio': datetime.now().replace(hour=14, minute=0),
            'x_ip': '192.168.1.50',
            'x_navegador': 'Chrome (Test Normal)',
            'x_intentos_fallidos': 0,
            'x_estado_intento': 'exito',
            'x_nivel_riesgo': riesgo_a,
        })

        # Caso B: Acceso fuera de horario y con fallos (Debe ser riesgo ALTO)
        riesgo_b = log_model.analizar_anomalia(self.id, 3, 5)
        log_model.create({
            'partner_id': self.id,
            'x_fecha_inicio': datetime.now().replace(hour=3, minute=0),
            'x_ip': '85.12.34.56',
            'x_navegador': 'Firefox (Test Anomalía)',
            'x_intentos_fallidos': 5,
            'x_estado_intento': 'fallo',
            'x_nivel_riesgo': riesgo_b,
        })

        # Refresca la pantalla para mostrar los nuevos datos creados
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }