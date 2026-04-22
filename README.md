# 🔐 Autenticación Inteligente y Detección de Fraude

## Descripción
Módulo de Odoo 17 que registra y analiza los intentos de inicio de sesión de los usuarios
para detectar comportamientos sospechosos y prevenir accesos fraudulentos a la plataforma.

## Tecnologías utilizadas
- **Odoo 17** — Framework ERP
- **Python 3** — Lógica de negocio
- **PostgreSQL 15** — Base de datos
- **XML** — Definición de vistas e informes
- **Docker / Docker Compose** — Entorno de desarrollo
- **Scikit-Learning** — Motor de Machine Learning

## Requisitos previos
- Docker y Docker Compose instalado
- Git instalado

## Instrucciones de instalación
```bash
# Clonar el repositorio
git clone https://github.com/JesusBenitezPitt/Proyecto-Intermodular-2025-26

# Acceder al directorio
cd Proyecto-Intermodular-2025-26

# Levantar los contenedores
docker compose up -d
```

## Instrucciones de ejecución
Una vez levantados los contenedores de Odoo, accedemos a la plataforma e instalamos el módulo **Autenticación Inteligente** desde el menú de Aplicaciones.

![Instalacion del modulo](docs/instalacion_modulo/instalacion_modulo.gif)

## Funcionalidades Nuevas
### Informe de patrones temporales por franjas horarias global

![Informe Patrones Temporales](docs/capturas/informe_patrones_temporales.png)

### Informe de patrones temporales por franjas horarias individual

![Informe Patrones Temporales Individual](docs/capturas/informe_patrones_temporales_individual.png)

Pueden parecer identicos pero uno recuenta los inicios de sesión de forma global y el otro de manera individual, es decir, de cada contacto.

### Análisis de IA por franjas horarias y pequeño script de Python para generar datos de entrenamiento y test.

![Analisis de IA](docs/capturas/ia.png)

Como podemos observar los dos ultimos registros son exactamente en la madrugada justo donde rompe con la rutina de acceso al sistema.

Este es el script de python que he usado para generar los datos de entrenamiento y prueba

```py
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
```

## Funcionalidades
- [x] Registro automático de cada intento de inicio de sesión en la base de datos
- [x] Almacenamiento de IP, fecha, hora, estado del intento y navegador
- [x] Vista de lista del historial completo de sesiones con indicadores de riesgo
- [x] Pestaña de seguridad en la ficha de cada contacto
- [x] Informe PDF de seguridad por contacto
- [x] Consulta SQL de análisis de fraude en tiempo real
- [x] Vista de alertas críticas filtrada por nivel de riesgo alto y crítico
- [x] Detección y bloqueo automático tras N intentos fallidos
- [x] Extracción correcta del navegador del usuario
- [X] Cálculo automático del nivel de riesgo mediante IA
- [ ] Notificaciones al administrador ante accesos sospechosos
- [ ] Notificación al usuario de confirmación de acceso a la cuenta
- [ ] Cálculo del nivel de riesgo mediante geolocalización
- [x] Informe de patrones temporales por franja horaria

## Autor
**Jesús Benítez Pitt**
2º DAM — Curso 2025/2026
