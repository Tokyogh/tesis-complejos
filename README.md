# Sistema de Estimación de Complejos PolideportivoPro

Plataforma web para estimations de construcción de canchas, pistas y complejos polideportivoPro en Ecuador: catálogo de materiales, calculadora de presupuestos, agendamiento de asesoría técnica y gestión de cotizaciones con autenticación y roles.

## Stack

- **Backend:** Python 3 + Flask
- **Base de datos:** SQLite mediante Flask-SQLAlchemy
- **Autenticación:** Flask-Login con Werkzeug (`generate_password_hash`)
- **Frontend:** HTML5 + Jinja2 + Tailwind CSS (CDN)
- **Entorno:** Visual Studio Code

## Estructura

```
complejos/
├── run.py                  # Punto de entrada
├── iniciar.py              # Prepara dependencias e inicia la aplicación
├── requirements.txt
├── instance/
│   └── database.db         # Base SQLite versionada (12 materiales de semilla)
├── app/
│   ├── __init__.py         # create_app, Flask-Login, blueprints, CLI
│   ├── models.py           # Material, User, Cotizacion, Cita
│   ├── migrations.py       # Migración idempotente de SQLite
│   ├── security.py         # admin_required, solo_registrados, destino_seguro
│   ├── static/             # css/custom.css, js/{main,calculator,modal-material}.js
│   ├── templates/          # base, index, materiales, calculadora, contacto, auth, paneles
│   └── routes/
│       ├── main_routes.py      # Inicio y catálogo
│       ├── calc_routes.py      # Calculadora de costos y áreas
│       ├── contact_routes.py   # Citas y asesoría
│       ├── auth_routes.py      # Registro, login y logout
│       ├── admin_routes.py     # Panel administrativo
│       └── panel_routes.py     # Historial del cliente
└── tests/                  # Suites de pruebas
```

## Inicio desde una descarga ZIP

Instala Python 3.9 o posterior en el computador y extrae el ZIP. Abre una terminal en la carpeta extraída y ejecuta el iniciador:

```powershell
py iniciar.py
```

En macOS o Linux:

```bash
python3 iniciar.py
```

El iniciador crea `.venv`, instala o actualiza las dependencias de `requirements.txt` cuando haga falta y arranca el sitio en `http://127.0.0.1:5000`. Requiere internet la primera vez para descargar dependencias y para cargar los recursos de Tailwind e imágenes. Flask crea las tablas, aplica las migraciones y siembra los materiales al iniciar. Detén el servidor con `Ctrl+C`.

## Cuenta administrativa

No se crea una cuenta administrativa con credenciales predeterminadas. Para crearla en Windows, inicia el asistente y luego ejecuta el comando indicado:

```powershell
py iniciar.py --crear-admin
```

También puedes crearla directamente:

```bash
flask --app run.py crear-admin --nombre "Nombre Apellido" --correo "correo@dominio.ec" --clave "ClaveSegura2026"
```

Las cuentas de cliente se registran solas en `/registro` y nunca reciben el rol de administrador.

## Comandos CLI

```bash
flask --app run.py init-db        # Crea tablas y aplica migraciones
flask --app run.py seed           # Siembra el catálogo de 12 materiales
flask --app run.py crear-admin    # Alta de administrador (interactivo)
```

## Rutas

| Ruta | Acceso | Descripción |
| --- | --- | --- |
| `/` | Público | Portada y portafolio |
| `/materiales` | Público | Catálogo con filtros y precios |
| `/calculadora` | Público | Áreas, costos, precios editables y CSV |
| `/contacto` | Lectura pública, envío con cuenta | Agenda de asesoría |
| `/registro`, `/register` | Público | Alta de cliente |
| `/login` | Público | Inicio de sesión |
| `/logout` | Con sesión | Cierre de sesión |
| `/mis-solicitudes` | Con sesión | Historial y detalle del cliente |
| `/admin` | Administrador | Cotizaciones, citas, estados y métricas |
| `/admin/materiales` | Administrador | CRUD del catálogo |
| `/admin/usuarios` | Administrador | Cuentas y roles |

## Roles y estados

- **Roles:** `admin` (gestiona todo) y `usuario` (solo sus solicitudes).
- **Estados de solicitud:** `Pendiente`, `En revisión`, `Aprobado`, `Rechazado`.
- Aprobar una cita la marca automáticamente como atendida.
- Los visitantes pueden calcular y descargar estimaciones; guardar una cotización en el historial requiere iniciar sesión.

## Base de datos y migraciones

La base se migra sola al iniciar. `db.create_all()` crea las tablas nuevas y `app/migrations.py` agrega por introspección las columnas faltantes (`estado`, `observaciones`, `user_id`) en cotizaciones y citas existentes, sin perder registros previos.

## Pruebas

```bash
python tests/run_all.py
```

Cubre catálogo, calculadora, Ecuador, portada, autenticación, roles, paneles y migraciones.

## Variables de entorno

| Variable | Descripción |
| --- | --- |
| `SECRET_KEY` | Clave de firmado de sesión. Sin valor se usa una clave de desarrollo. |
| `DATABASE_URL` | Ruta de SQLite. Por defecto `instance/database.db`. |
