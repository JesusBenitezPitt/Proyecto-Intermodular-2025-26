from odoo import models, fields, api
import requests, logging, os

_logger = logging.getLogger(__name__)

class NotificacionesMovil(models.Model):
    _name = 'notificaciones_movil'
    _description = 'Registro de Notificaciones Push'

    x_user_id = fields.Many2one('res.users', string='Usuario Destinatario', required=True)
    x_titulo = fields.Char(string='Título', required=True)
    x_mensaje = fields.Text(string='Mensaje', required=True)
    x_tipo_alerta = fields.Selection([
        ('info', 'Informativa'),
        ('warning', 'Advertencia'), 
        ('danger', 'Peligro')], string='Tipo')
    x_log_id = fields.Many2one('authentication.sesion.log', string='Log Origen')
    x_leida = fields.Boolean(string='Leída', default=False)
    x_estado_aprobacion = fields.Selection([
        ('pending', 'Esperando respuesta'),
        ('aproved', 'Aprobado'),
        ('denied', 'Denegado')
    ], default='pending')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(NotificacionesMovil, self).create(vals_list)
        for rec in records:
            if rec.x_user_id.x_firebase_token:
                rec._enviar_a_firebase()
        return records

    def _enviar_a_firebase(self):
        server_key = os.getenv('FIREBASE_KEY')
        if not server_key:
            _logger.error("FIREBASE_KEY no encontrada en el entorno.")
            return

        url = "https://fcm.googleapis.com/fcm/send"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"key={server_key}"
        }

        payload = {
            "to": self.x_user_id.x_firebase_token,
            "notification": {
                "title": self.x_titulo,
                "body": self.x_mensaje,
                "sound": "default"
            },
            "data": {
                "log_id": self.x_log_id.id if self.x_log_id else False,
                "tipo": self.x_tipo_alerta
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code != 200:
                _logger.error(f"Error Firebase: {response.text}")
        except Exception as e:
            _logger.error(f"Error de conexión con Firebase: {e}")