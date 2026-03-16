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

## Funcionalidades
- [x] Registro automático de cada intento de inicio de sesión en la base de datos
- [x] Almacenamiento de IP, fecha, hora, estado del intento y navegador
- [x] Vista de lista del historial completo de sesiones con indicadores de riesgo
- [x] Pestaña de seguridad en la ficha de cada contacto
- [x] Informe PDF de seguridad por contacto
- [x] Consulta SQL de análisis de fraude en tiempo real
- [x] Vista de alertas críticas filtrada por nivel de riesgo alto y crítico
- [ ] Detección y bloqueo automático tras N intentos fallidos
- [ ] Extracción correcta del navegador del usuario
- [ ] Cálculo automático del nivel de riesgo mediante IA
- [ ] Notificaciones al administrador ante accesos sospechosos
- [ ] Informe de patrones temporales por franja horaria

## Autor
**Jesús Benítez Pitt**
2º DAM — Curso 2025/2026