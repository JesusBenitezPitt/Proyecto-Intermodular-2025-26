from odoo import models, fields, api, tools

class InformeFranjasHorarias(models.Model):
    _name = 'informe.franjas.horarias'
    _description = 'Análisis de Patrones de Autenticación'
    _auto = False

    franja_horaria = fields.Char(string='Franja Horaria', readonly=True)
    total_accesos = fields.Integer(string='Total Accesos', readonly=True)
    alertas_ia = fields.Integer(string='Alertas de Riesgo Alto', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    row_number() OVER () AS id,
                    CASE 
                        WHEN EXTRACT(HOUR FROM x_fecha_inicio AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Madrid') BETWEEN 0 AND 6 THEN 'Madrugada (0-6)'
                        WHEN EXTRACT(HOUR FROM x_fecha_inicio AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Madrid') BETWEEN 7 AND 12 THEN 'Mañana (7-12)'
                        WHEN EXTRACT(HOUR FROM x_fecha_inicio AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Madrid') BETWEEN 13 AND 20 THEN 'Tarde (13-20)'
                        ELSE 'Noche (21-23)'
                    END AS franja_horaria,
                    COUNT(*) AS total_accesos,
                    SUM(CASE WHEN x_nivel_riesgo = 'alto' THEN 1 ELSE 0 END) AS alertas_ia
                FROM autenticacion_sesion_log
                GROUP BY franja_horaria
            )
        """ % self._table)