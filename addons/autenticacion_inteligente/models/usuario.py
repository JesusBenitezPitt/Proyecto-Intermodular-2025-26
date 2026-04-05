from odoo import models, fields
from datetime import datetime
import random

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

    def action_ver_analisis_horario_individual(self):
        return {
            'name': f'Análisis de accesos de: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'autenticacion.sesion.log',
            'view_mode': 'graph',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'search_default_group_by_franja': 1,
                'graph_groupbys': ['x_franja_horaria'],
                'graph_measure': '__count__',
                'graph_mode': 'bar',
            },
        }

    def action_generar_datos_demo(self):
        for i in range(10):
            hora_random = random.randint(0, 23)
            intentos = random.randint(0, self.x_limite_intentos)
            self.env['autenticacion.sesion.log'].create({
                'partner_id': self.id,
                'x_fecha_inicio': datetime.now().replace(hour=hora_random),
                'x_ip': f'127.0.0.{i}',
                'x_navegador': 'Safari',
                'x_intentos_fallidos': intentos,
                'x_estado_intento': 'fallo' if intentos >= self.x_limite_intentos else 'exito',
                'x_nivel_riesgo': 'alto' if hora_random <= 8 or hora_random >= 21 else 'bajo',
            })
        return True