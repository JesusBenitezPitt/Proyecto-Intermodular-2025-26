from odoo import models, fields
from datetime import datetime
import random
import logging

_logger = logging.getLogger(__name__)

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
        """ Simula 10 días de patrón normal + 1 día con actividad sospechosa """
        
        # Limpiar datos anteriores
        # self.env['authentication.sesion.log'].search([('partner_id', '=', self.id)]).unlink()
        
        from datetime import datetime, timedelta
        import random
        
        log_model = self.env['authentication.sesion.log']
        
        # ✅ SIMULAR 10 DÍAS DE TRABAJO NORMAL (Lunes a Viernes, 9am-6pm)
        _logger.info("\n=== GENERANDO PATRÓN DE 10 DÍAS ===")
        
        fecha_base = datetime.now() - timedelta(days=10)
        
        for dia in range(10):
            fecha_dia = fecha_base + timedelta(days=dia)
            dia_semana = fecha_dia.weekday()  # 0=Lunes, 6=Domingo
            
            # Solo trabajar de lunes a viernes
            if dia_semana < 5:  # 0-4 = Lunes a Viernes
                # Entrada por la mañana (entre 9am y 10am)
                hora_entrada = random.randint(9, 10)
                log_model.create({
                    'partner_id': self.id,
                    'x_fecha_inicio': fecha_dia.replace(hour=hora_entrada, minute=random.randint(0, 59)),
                    'x_ip': '192.168.1.50',  # Siempre misma IP (oficina)
                    'x_navegador': 'Chrome',
                    'x_intentos_fallidos': 0,  # Siempre acierta
                    'x_estado_intento': 'exito',
                    'x_nivel_riesgo': 'bajo',
                })
                
                # Salida por la tarde (entre 5pm y 6pm)
                hora_salida = random.randint(17, 18)
                log_model.create({
                    'partner_id': self.id,
                    'x_fecha_inicio': fecha_dia.replace(hour=hora_salida, minute=random.randint(0, 59)),
                    'x_ip': '192.168.1.50',
                    'x_navegador': 'Chrome',
                    'x_intentos_fallidos': 0,
                    'x_estado_intento': 'exito',
                    'x_nivel_riesgo': 'bajo',
                })
        
        _logger.info(f"✓ Generados {log_model.search_count([('partner_id', '=', self.id)])} accesos normales\n")
        
        # ✅ AHORA VIENEN LOS CASOS DE PRUEBA DEL DÍA 11
        _logger.info("=== PROBANDO CASOS DEL DÍA 11 ===\n")
        
        fecha_hoy = datetime.now()
        
        # CASO 1: Acceso normal en horario laboral
        _logger.info("→ CASO 1: Acceso normal (10am, 0 intentos)")
        riesgo_1 = log_model.analizar_anomalia(self.id, 10, 0)
        log_model.create({
            'partner_id': self.id,
            'x_fecha_inicio': fecha_hoy.replace(hour=10, minute=0),
            'x_ip': '192.168.1.50',
            'x_navegador': 'Chrome',
            'x_intentos_fallidos': 0,
            'x_estado_intento': 'exito',
            'x_nivel_riesgo': riesgo_1,
            'x_alerta_seguridad': 'Caso 1: Patrón normal',
        })
        _logger.info(f"   Resultado: {riesgo_1.upper()}\n")
        
        # CASO 2: Acceso en madrugada con muchos intentos (ATAQUE)
        _logger.info("→ CASO 2: Ataque en madrugada (3am, 5 intentos)")
        riesgo_2 = log_model.analizar_anomalia(self.id, 3, 5)
        log_model.create({
            'partner_id': self.id,
            'x_fecha_inicio': fecha_hoy.replace(hour=3, minute=0),
            'x_ip': '85.12.34.99',  # IP externa
            'x_navegador': 'Firefox',
            'x_intentos_fallidos': 5,
            'x_estado_intento': 'fallo',
            'x_nivel_riesgo': riesgo_2,
            'x_alerta_seguridad': 'Caso 2: Ataque madrugada',
        })
        _logger.info(f"   Resultado: {riesgo_2.upper()}\n")
        
        # CASO 3: Acceso en horario laboral pero con intentos fallidos
        _logger.info("→ CASO 3: Intentos fallidos en horario laboral (2pm, 4 intentos)")
        riesgo_3 = log_model.analizar_anomalia(self.id, 14, 4)
        log_model.create({
            'partner_id': self.id,
            'x_fecha_inicio': fecha_hoy.replace(hour=14, minute=0),
            'x_ip': '45.67.89.10',  # IP desconocida
            'x_navegador': 'Unknown',
            'x_intentos_fallidos': 4,
            'x_estado_intento': 'fallo',
            'x_nivel_riesgo': riesgo_3,
            'x_alerta_seguridad': 'Caso 3: Ataque horario laboral',
        })
        _logger.info(f"   Resultado: {riesgo_3.upper()}\n")
        
        # CASO 4: Trabajador necesita entrar de madrugada (sin intentos fallidos)
        _logger.info("→ CASO 4: Trabajador legítimo en madrugada (4am, 0 intentos)")
        riesgo_4 = log_model.analizar_anomalia(self.id, 4, 0)
        log_model.create({
            'partner_id': self.id,
            'x_fecha_inicio': fecha_hoy.replace(hour=4, minute=0),
            'x_ip': '192.168.1.50',  # Misma IP de siempre
            'x_navegador': 'Chrome',
            'x_intentos_fallidos': 0,
            'x_estado_intento': 'exito',
            'x_nivel_riesgo': riesgo_4,
            'x_alerta_seguridad': 'Caso 4: Trabajador legítimo fuera de horario',
        })
        _logger.info(f"   Resultado: {riesgo_4.upper()}\n")
        
        _logger.info("=== SIMULACIÓN COMPLETADA ===")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }