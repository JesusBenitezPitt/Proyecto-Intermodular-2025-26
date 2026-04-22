from odoo import models, fields, api, tools

class InformeSeguridad(models.Model):
    _name = 'authentication_inteligente.informe_seguridad'
    _description = 'Análisis de Fraude'
    
    # Indicamos que Odoo no cree una tabla física; usaremos una vista SQL dinámica
    _auto = False

    # --- CAMPOS EXTRAÍDOS DE LA CONSULTA SQL ---
    partner_id = fields.Many2one('res.partner', string='Contacto', readonly=True)
    x_ip = fields.Char(string='Dirección IP', readonly=True)
    total_fallos = fields.Integer(string='Total Fallos Acumulados', readonly=True)

    def init(self):
        """ 
        Define la vista SQL que agrupa los fallos de inicio de sesión. 
        Permite identificar qué IPs están intentando acceder de forma fallida a qué cuentas.
        """
        # Limpieza de la vista previa para evitar conflictos al actualizar el módulo
        tools.drop_view_if_exists(self.env.cr, self._table)
        
        # Ejecución del motor SQL de Odoo
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    -- Generamos un identificador único necesario para que Odoo muestre los datos
                    row_number() OVER () as id,
                    partner_id,
                    x_ip,
                    -- Contamos el número de registros que coinciden con el estado 'fallo'
                    count(*) as total_fallos
                FROM authentication_sesion_log
                WHERE x_estado_intento = 'fallo'
                -- Agrupamos para ver el total de fallos por cada combinación de Usuario e IP
                GROUP BY partner_id, x_ip
            )
        """ % self._table)