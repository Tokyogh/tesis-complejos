
# AGENTS.MD - Arquitectura y Roadmap de Desarrollo

## 1. Stack Tecnológico Fijo
* **Backend:** Python con **Flask**
* **Base de Datos:** **SQLite** (vía Flask-SQLAlchemy)
* **Frontend:** HTML5, Jinja2 Templates, **Tailwind CSS** (vía CDN para diseño profesional y limpio con paleta corporativa: tonos pizarra, azul institucional y acentos en verde esmeralda para construcción/sostenibilidad).
* **Entorno:** Visual Studio Code

---

## 2. Arquitectura Modular (Estructura de Directorios)
Para evitar un `app.py` masivo, se divide la aplicación en Blueprints:

sistema_polideportivo/
│
├── run.py                  # Archivo de entrada principal (orquestador)
├── instance/               # Carpeta para SQLite
│   └── database.db
├── requirements.txt        # Flask, Flask-SQLAlchemy
│
├── app/                    # Paquete principal de la aplicación
│   ├── __init__.py         # Fábrica de la app (create_app) y configuración DB
│   ├── models.py           # Modelos SQLAlchemy (Materiales, Cotizaciones, Citas)
│   │
│   ├── static/             # Archivos estáticos (CSS custom, JS para la calculadora)
│   │   ├── css/
│   │   └── js/
│   │
│   ├── templates/          # Plantillas HTML con Jinja2
│   │   ├── base.html       # Layout global (Navbar, Footer, CDN Tailwind)
│   │   ├── index.html      # Hero section + Portafolio de proyectos base
│   │   ├── calculadora.html# Core: Interfaz de cálculo de áreas y costos
│   │   ├── materiales.html # Catálogo y precios referenciales de insumos
│   │   └── contacto.html   # Formulario de agendamiento de citas/asesoría
│   │
│   └── routes/             # Blueprints (Módulos independientes)
│       ├── __init__.py
│       ├── main_routes.py  # Rutas de inicio, portafolio y materiales
│       ├── calc_routes.py  # Lógica y procesamiento de la calculadora de costos
│       └── contact_routes.py# Gestión del formulario y agendamiento de citas

```

---

## 3. Roadmap de Desarrollo Autónomo

* **Fase 1: Configuración Base e Infraestructura**
* Inicializar entorno virtual, instalar dependencias y crear `requirements.txt`.
* Configurar la fábrica de la aplicación (`create_app`) en `app/__init__.py` utilizando Flask-SQLAlchemy.
* Definir modelos en `models.py`: `Material` (nombre, unidad, precio_referencial) y `Cita` (nombre, correo, fecha, mensaje).


* **Fase 2: Estructura Visual y Layout (`base.html`)**
* Crear la plantilla base con Tailwind CSS (barra de navegación fija, diseño responsivo, paleta profesional de colores grises/azules y tipografía limpia).
* Configurar la ruta principal en `main_routes.py` para renderizar el inicio y la sección de portafolio de proyectos previos.


* **Fase 3: Módulo de Catálogo de Materiales**
* Poblar datos iniciales en SQLite mediante un script de seed o inserción automática (hormigón, mallas, césped sintético, iluminación LED).
* Crear la vista para listar los materiales con sus precios referenciales.


* **Fase 4: Desarrollo del Núcleo (Calculadora de Costos y Áreas)**
* Desarrollar la interfaz en `calculadora.html` permitiendo ingresar dimensiones y seleccionar componentes (tipo de losa, cerramiento, etc.).
* Implementar la lógica en `calc_routes.py` para procesar los datos, multiplicar por los costos de los materiales de la base de datos y retornar un presupuesto preliminar desglosado.


* **Fase 5: Módulo de Contacto y Agendamiento**
* Implementar la vista y ruta en `contact_routes.py` para capturar solicitudes de asesoría o citas técnicas, guardándolas en SQLite.
* Pruebas finales de integración y diseño responsivo en la interfaz.



