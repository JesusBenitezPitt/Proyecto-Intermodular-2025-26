from odoo import models, fields, api, tools

class InformeSeguridad(models.Model):
    _name = 'autenticacion_inteligente.informe_seguridad'
    _description = 'Análisis de Fraude por SQL'
    _auto = False  # Evita crear una tabla

    # Definimos los campos que extraerá la consulta
    partner_id = fields.Many2one('res.partner', string='Contacto', readonly=True)
    x_ip = fields.Char(string='Dirección IP', readonly=True)
    total_fallos = fields.Integer(string='Total Fallos Acumulados', readonly=True)

    def init(self):
        # Sentencia SQL la cual extrae toda la información para el informe.
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    row_number() OVER () as id,
                    partner_id,
                    x_ip,
                    count(*) as total_fallos
                FROM autenticacion_sesion_log
                WHERE x_estado_intento = 'fallo'
                GROUP BY partner_id, x_ip
            )
        """ % self._table)