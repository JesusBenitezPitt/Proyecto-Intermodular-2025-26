from odoo import models, fields, api, registry
from google.oauth2 import service_account
import google.auth.transport.requests
import requests, logging, os, json

_logger = logging.getLogger(__name__)

class NotificacionesMovil(models.Model):
    _name = 'notificaciones.movil'
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
    x_es_confirmacion_2fa = fields.Boolean(string='¿Es notificación de confirmación de 2FA?', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(NotificacionesMovil, self).create(vals_list)
        for rec in records:
            if rec.x_user_id.x_firebase_token:
                rec._enviar_a_firebase()
            else:
                _logger.warning(f"Usuario {rec.x_user_id.name} no tiene token de Firebase")
        return records

    def _get_access_token(self, json_path):
        
        try:
            scopes = ['https://www.googleapis.com/auth/firebase.messaging']
            creds = service_account.Credentials.from_service_account_file(json_path, scopes=scopes)
            
            # Refrescamos el token de acceso
            auth_request = google.auth.transport.requests.Request()
            creds.refresh(auth_request)
            
            return creds.token
        except Exception as e:
            _logger.error("❌ Error al generar el token de Firebase: %s", str(e))
            return False

    def _enviar_a_firebase(self):
        env_var = os.getenv('FIREBASE_JSON')
        ruta_json = env_var or '/var/lib/odoo/firebase_configs/firebase-sdk.json'

        if not os.path.exists(ruta_json):
            _logger.error("❌ ARCHIVO NO ENCONTRADO: %s", ruta_json)
            return False

        self.env.cr.flush() 

        token = self._get_access_token(ruta_json)
        if not token:
            return False

        try:
            with open(ruta_json, 'r') as f:
                config = json.load(f)
                project_id = config.get('project_id')

            url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            payload = {
                "message": {
                    "token": self.x_user_id.partner_id.x_firebase_token,
                    "notification": {
                        "title": self.x_titulo,
                        "body": self.x_mensaje
                    },
                    "data": {
                        "notification_id": str(self.id),
                        "log_id": str(self.x_log_id.id) if self.x_log_id else "",
                        "requires_action": "true" if self.x_estado_aprobacion == 'pending' else "false"
                    }
                }
            }

            response = requests.post(url, json=payload, headers=headers, timeout=5)

            if response.status_code == 200:
                _logger.info(f"Notificación enviada con éxito a {self.x_user_id.name}")
                return True
            else:
                _logger.error(f"❌ Error Firebase: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            _logger.error(f"❌ Error crítico en _enviar_a_firebase: {str(e)}")
            return False

    def write(self, vals):
        res = super(NotificacionesMovil, self).write(vals)
        
        for rec in self:
            if 'x_estado_aprobacion' in vals:
                if vals['x_estado_aprobacion'] == 'denied':
                    rec.x_user_id.partner_id.write({
                        'x_is_blocked': True,
                        'x_timestamp_bloqueo': fields.Datetime.now(),
                    })

                    if rec.x_log_id:
                        rec.x_log_id.write({
                            'x_estado_intento': 'bloqueo',
                            'x_alerta_seguridad': 'Acceso denegado desde la App. Usuario bloqueado por precaución.'
                        })
                    
                    _logger.warning(f"Usuario {rec.x_user_id.name} BLOQUEADO por denegar acceso")
                
                elif vals['x_estado_aprobacion'] == 'aproved':
                    if rec.x_log_id:
                        rec.x_log_id.write({
                            'x_alerta_seguridad': 'Acceso verificado por el usuario vía App.'
                        })
                    _logger.info(f"Usuario {rec.x_user_id.name} APROBÓ el acceso")
        
        return res