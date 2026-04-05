from odoo import models, fields, api, tools

class InformeFranjasHorarias(models.Model):
    _name = 'informe.franjas.horarias'
    _description = 'Análisis de Patrones de Autenticación'
    
    # Indicamos que este modelo no crea una tabla real, sino que se nutre de una vista SQL
    _auto = False

    # --- DEFINICIÓN DE CAMPOS (Solo lectura, ya que vienen del SQL) ---
    franja_horaria = fields.Char(string='Franja Horaria', readonly=True)
    total_accesos = fields.Integer(string='Total Accesos', readonly=True)
    alertas_ia = fields.Integer(string='Alertas de Riesgo Alto', readonly=True)

    def init(self):
        """ 
        Crea la vista SQL en la base de datos al instalar o actualizar el módulo.
        Calcula las franjas horarias y agrupa los resultados automáticamente.
        """
        # Elimina la vista si ya existe para evitar errores al actualizar
        tools.drop_view_if_exists(self.env.cr, self._table)
        
        # Ejecutamos la consulta SQL pura para construir el informe
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    row_number() OVER () AS id, -- Genera un ID único temporal para Odoo
                    CASE 
                        -- Convertimos la fecha de UTC a la zona horaria de Madrid para clasificar correctamente
                        WHEN EXTRACT(HOUR FROM x_fecha_inicio AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Madrid') BETWEEN 0 AND 6 THEN '1. Madrugada (0-6h)'
                        WHEN EXTRACT(HOUR FROM x_fecha_inicio AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Madrid') BETWEEN 7 AND 12 THEN '2. Mañana (7-12h)'
                        WHEN EXTRACT(HOUR FROM x_fecha_inicio AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Madrid') BETWEEN 13 AND 20 THEN '3. Tarde (13-20h)'
                        ELSE '4. Noche (21-23h)'
                    END AS franja_horaria,
                    COUNT(*) AS total_accesos, -- Cuenta el total de registros en cada franja
                    -- Sumamos 1 solo cuando el riesgo es alto para obtener el total de alertas
                    SUM(CASE WHEN x_nivel_riesgo = 'alto' THEN 1 ELSE 0 END) AS alertas_ia
                FROM autenticacion_sesion_log
                GROUP BY franja_horaria -- Agrupa los resultados por el nombre de la franja
            )
        """ % self._table)