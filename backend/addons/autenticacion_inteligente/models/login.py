from odoo import models, api
from odoo.exceptions import AccessError
from odoo.http import request
from datetime import datetime
import logging
import time

_logger = logging.getLogger(__name__)

INTENTOS = {}

class ResUsersLogin(models.Model):
    _inherit = 'res.users'

    @api.model
    def _parse_user_agent(self, ua_string):
        if not ua_string:
            return 'Desconocido'
        ua_string = str(ua_string)
        if 'Odoo' in ua_string: return 'Odoo App'
        if 'okhttp' in ua_string.lower(): return 'App Móvil'  # Detecta la app React Native
        if 'Edg' in ua_string: return 'Edge'
        if 'Chrome' in ua_string: return 'Chrome'
        if 'Firefox' in ua_string: return 'Firefox'
        if 'Safari' in ua_string: return 'Safari'
        return ua_string[:50]

    @classmethod
    def _login(cls, db, login, password, user_agent_env=None):
        auth_result = False
        error_auth = None

        ip = request.httprequest.remote_addr or 'Desconocida'
        ua_raw = request.httprequest.user_agent.string or 'Desconocido'
        navegador = cls._parse_user_agent(cls, ua_raw)

        # Verificación de bloqueo
        with cls.pool.cursor() as cr:
            env = api.Environment(cr, 1, {})
            user = env['res.users'].sudo().search([('login', '=', login)], limit=1)
            if user and user.partner_id.x_is_blocked:
                _logger.warning("Acceso denegado: Usuario '%s' bloqueado.", login)
                raise AccessError("Cuenta bloqueada por seguridad. Contacte con el administrador.")

        # Autenticación original
        try:
            auth_result = super()._login(db, login, password, user_agent_env=user_agent_env)
        except Exception as e:
            auth_result = False
            error_auth = e

        estado = 'exito' if auth_result else 'fallo'

        # Gestión de fallos
        if estado == 'fallo':
            INTENTOS[login] = INTENTOS.get(login, 0) + 1
            
            with cls.pool.cursor() as cr:
                env = api.Environment(cr, 1, {})
                user = env['res.users'].sudo().search([('login', '=', login)], limit=1)

                if user and INTENTOS[login] >= user.partner_id.x_limite_intentos:
                    user.partner_id.write({
                        'x_is_blocked': True,
                        'x_timestamp_bloqueo': datetime.now(),
                    })

                    env['authentication.sesion.log'].sudo().create({
                        'partner_id': user.partner_id.id,
                        'x_ip': ip,
                        'x_navegador': navegador,
                        'x_fecha_inicio': datetime.now(),
                        'x_estado_intento': 'bloqueo',
                        'x_intentos_fallidos': INTENTOS[login],
                        'x_nivel_riesgo': 'alto',
                        'x_alerta_seguridad': 'CUENTA BLOQUEADA: Exceso de intentos.'
                    })
                    cr.commit()
                    if login in INTENTOS: del INTENTOS[login]

                if error_auth: raise error_auth
        else:
            # Login exitoso
            try:
                with cls.pool.cursor() as cr:
                    env = api.Environment(cr, 1, {})
                    user = env['res.users'].sudo().search([('login', '=', login)], limit=1)
                    partner = user.partner_id
                    if not user: return auth_result

                    # Determinar si es móvil o web
                    es_movil = "okhttp" in navegador.lower() or "app móvil" in navegador.lower()

                    # Si NO tiene token de Firebase y NO es móvil -> bloquear
                    if not partner.x_firebase_token and not es_movil:
                        _logger.warning("Acceso web denegado: El usuario '%s' no tiene la App vinculada.", login)
                        raise AccessError("Su cuenta requiere vinculación con la App móvil.\nContacte con el administrador o inicie sesión desde la App.")
                    
                    # Obtener geolocalización
                    datos_localizacion = env['authentication.sesion.log'].sudo().obtener_datos_geograficos(ip)
                    lat = datos_localizacion['lat']
                    lng = datos_localizacion['lng']
                    loc_nombre = datos_localizacion['texto']

                    intentos_previos = INTENTOS.get(login, 0)
                    hora_actual = datetime.now().hour
                    
                    log_obj = env['authentication.sesion.log'].sudo()
                    nivel_ia = log_obj.analizar_anomalia(user.partner_id.id, hora_actual, intentos_previos, lat, lng)

                    # Crear log de sesión
                    log_rec = log_obj.create({
                        'partner_id': user.partner_id.id,
                        'x_ip': ip,
                        'x_navegador': navegador,
                        'x_fecha_inicio': datetime.now(),
                        'x_estado_intento': 'exito',
                        'x_intentos_fallidos': intentos_previos,
                        'x_nivel_riesgo': nivel_ia,
                        'x_latitud': lat,
                        'x_longitud': lng,
                        'x_localizacion': loc_nombre,
                        'x_alerta_seguridad': f'Análisis IA ({nivel_ia}) en {loc_nombre}'
                    })

                    if es_movil:
                        _logger.info(f"Login desde App móvil para {login}, 2FA omitido")
                        request.session['tfg_log_id'] = False  # No requiere validación
                        request.session['tfg_notif_id'] = False
                        cr.commit()
                        if login in INTENTOS: del INTENTOS[login]
                        return auth_result

                    if partner.x_firebase_token:
                        notif_auth = env['notificaciones.movil'].sudo().create({
                            'x_user_id': user.id,
                            'x_titulo': 'Confirmación de Acceso',
                            'x_mensaje': f'Tienes que confirmar el acceso para entrar a Odoo desde {loc_nombre}',
                            'x_log_id': log_rec.id,
                            'x_tipo_alerta': 'warning',
                            'x_estado_aprobacion': 'pending',
                            'x_es_confirmacion_2fa': True
                        })

                        request.session['tfg_log_id'] = log_rec.id
                        request.session['tfg_notif_id'] = notif_auth.id
                        
                        cr.commit()

                        # **AQUÍ ESPERAMOS LA APROBACIÓN**
                        _logger.info(f"Esperando aprobación 2FA para {login}...")
                        aprobado = cls._esperar_aprobacion_2fa(env, notif_auth.id, timeout=120)
                        
                        if not aprobado:
                            _logger.warning(f"2FA rechazado o timeout para {login}")
                            raise AccessError("Acceso denegado: No se validó el inicio de sesión en la App.")

                        _logger.info(f"2FA aprobado para {login}")

                    if login in INTENTOS: del INTENTOS[login]

            except AccessError:
                raise  # Re-lanzar errores de acceso
            except Exception as e:
                _logger.error("Error en el registro de log: %s", e)

        return auth_result

    @classmethod
    def _esperar_aprobacion_2fa(cls, env, notif_id, timeout=120):

        inicio = time.time()
        _logger.info(f"Bucle de espera iniciado para Notif ID: {notif_id}")
        
        while time.time() - inicio < timeout:
            with cls.pool.cursor() as fresh_cr:
                fresh_cr.execute("""
                    SELECT x_estado_aprobacion 
                    FROM notificaciones_movil 
                    WHERE id = %s
                """, (notif_id,))
                
                result = fresh_cr.fetchone()
                if result:
                    estado = result[0]
                    _logger.info(f"Estado actual de la notif {notif_id}: {estado}")
                    
                    if estado == 'aproved':
                        return True
                    elif estado == 'denied':
                        return False
            
            time.sleep(2) 
        
        _logger.error(f"Timeout de 2FA alcanzado para notif {notif_id}")
        return False