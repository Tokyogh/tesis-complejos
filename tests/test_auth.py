import os
import sys
import tempfile

from util import crear_app_de_pruebas

from app import create_app, db
from app.models import Cita, Cotizacion, Material, User

app = crear_app_de_pruebas("auth")

fallos = []


def revisar(nombre, condicion, detalle=""):
    print(f"[{'OK ' if condicion else 'FAIL'}] {nombre} {detalle}")
    if not condicion:
        fallos.append(nombre)


def registrar(cliente, nombre, correo, clave="Polideportivo2026", **extra):
    datos = {
        "nombre": nombre,
        "correo": correo,
        "telefono": "+593 9 1111 2222",
        "organizacion": "Municipio de Quito",
        "clave": clave,
        "clave_confirmacion": clave,
        "acepto": "1",
    }
    datos.update(extra)
    return cliente.post("/registro", data=datos, follow_redirects=True)


def entrar(cliente, correo, clave="Polideportivo2026"):
    return cliente.post(
        "/login", data={"correo": correo, "clave": clave, "recordar": "1"}, follow_redirects=True
    )


def crear_admin(correo="admin@polideportivos.ec"):
    with app.app_context():
        usuario = User.query.filter_by(correo=correo).first()
        if usuario is None:
            usuario = User(nombre="Equipo PolideportivoPro", correo=correo, rol="admin")
            db.session.add(usuario)
        usuario.set_password("AdminSegura2026")
        db.session.commit()
        return usuario.id


def presupuesto(cliente, proyecto="Polideportivo Test", componentes=None):
    with app.app_context():
        claves = componentes or [m.clave for m in Material.query.all()]
    datos = {
        "proyecto": proyecto,
        "solicitante": "Ana Pérez",
        "correo": "ana@ejemplo.ec",
        "largo": "28",
        "ancho": "15",
        "altura": "8",
        "espesor_losa": "0.15",
        "num_canchas": "2",
        "indirectos": "18",
        "componentes": claves,
    }
    return cliente.post("/calculadora", data=datos)


print("=== 1. REGISTRO ===")
invitado = app.test_client()
respuesta = invitado.get("/registro")
revisar("GET /registro", respuesta.status_code == 200, f"-> {respuesta.status_code}")
revisar("formulario de registro", 'name="clave_confirmacion"' in respuesta.text and 'name="acepto"' in respuesta.text)

respuesta = registrar(invitado, "María Fernanda", "maria@ejemplo.ec")
revisar("registro exitoso", respuesta.status_code == 200 and "Bienvenido" in respuesta.text)
revisar("sesion iniciada tras registro", "María Fernanda" in respuesta.text)
revisar("redirige a mis solicitudes", "Mis solicitudes" in respuesta.text or "/mis-solicitudes" in respuesta.text)

with app.app_context():
    usuario = User.query.filter_by(correo="maria@ejemplo.ec").one()
    revisar("usuario creado", usuario is not None)
    revisar("rol asignado como cliente", usuario.rol == "usuario", f"-> {usuario.rol}")
    revisar("rol no escalable", usuario.role == "usuario")
    revisar("contraseña cifrada", usuario.clave_hash != "Polideportivo2026" and len(usuario.clave_hash) > 40)
    revisar("hash verificable", usuario.check_password("Polideportivo2026") and not usuario.check_password("otra"))
    revisar("nombre de organizacion", usuario.organizacion == "Municipio de Quito")
    revisar("iniciales calculadas", usuario.iniciales == "MF", f"-> {usuario.iniciales}")
    revisar("es_admin falso", usuario.es_admin is False)

print()
print("=== 2. VALIDACION DEL REGISTRO ===")
otro = app.test_client()
respuesta = registrar(otro, "María Fernanda", "maria@ejemplo.ec")
revisar("correo duplicado rechazado", "Ya existe una cuenta" in respuesta.text)

respuesta = registrar(otro, "Ab", "corto@ejemplo.ec")
revisar("nombre corto rechazado", "mínimo 3 caracteres" in respuesta.text)

respuesta = registrar(otro, "Carlos Díaz", "carlos@ejemplo.ec", clave="123")
revisar("clave corta rechazada", "al menos 8 caracteres" in respuesta.text)

respuesta = registrar(otro, "Carlos Díaz", "carlos@ejemplo.ec", clave="sololetraslargas")
revisar("sin numeros rechazada", "letras y números" in respuesta.text)

respuesta = registrar(
    otro, "Carlos Díaz", "carlos@ejemplo.ec", clave="Polideportivo2026", clave_confirmacion="Otra2026"
)
revisar("confirmacion distinta rechazada", "no coinciden" in respuesta.text)

respuesta = registrar(otro, "Carlos Díaz", "no-es-correo", clave="Polideportivo2026")
revisar("correo invalido rechazado", "correo electrónico válido" in respuesta.text)

respuesta = registrar(otro, "Carlos Díaz", "sin-termino@ejemplo.ec", clave="Polideportivo2026", acepto=None)
revisar("terminos obligatorios", "aceptar los términos" in respuesta.text.lower())

respuesta = registrar(otro, "Intruso Malicioso", "intruso@ejemplo.ec", clave="Polideportivo2026", rol="admin")
with app.app_context():
    revisar("no se puede auto-asignar admin", User.query.filter_by(correo="intruso@ejemplo.ec").one().rol == "usuario")

print()
print("=== 3. INICIO Y CIERRE DE SESION ===")
sesion = app.test_client()
respuesta = sesion.get("/login")
revisar("GET /login", respuesta.status_code == 200 and 'name="recordar"' in respuesta.text)

respuesta = sesion.post("/login", data={"correo": "maria@ejemplo.ec", "clave": "incorrecta"})
revisar("clave incorrecta rechazada", "no son correctos" in respuesta.text)

respuesta = sesion.post("/login", data={"correo": "nadie@ejemplo.ec", "clave": "Polideportivo2026"})
revisar("usuario inexistente rechazado", "no son correctos" in respuesta.text)

respuesta = entrar(sesion, "maria@ejemplo.ec")
revisar("login correcto", "Hola de nuevo" in respuesta.text)

with app.app_context():
    revisar("ultimo acceso registrado", User.query.filter_by(correo="maria@ejemplo.ec").one().ultimo_acceso is not None)

respuesta = sesion.get("/logout")
revisar("logout funciona", respuesta.status_code == 302)
respuesta = sesion.get("/mis-solicitudes")
revisar("sesion cerrada pierde acceso", respuesta.status_code == 302 and "/login" in respuesta.headers["Location"])

print()
print("=== 4. PROTECCION DE RUTAS ===")
anonimo = app.test_client()
for ruta_protegida in ["/admin", "/mis-solicitudes", "/admin/materiales", "/admin/usuarios"]:
    respuesta = anonimo.get(ruta_protegida)
    revisar(
        f"anonimo {ruta_protegida} redirige a login",
        respuesta.status_code == 302 and "/login" in respuesta.headers["Location"],
        f"-> {respuesta.status_code}",
    )

respuesta = anonimo.get("/contacto")
revisar("GET /contacto es publico", respuesta.status_code == 200, f"-> {respuesta.status_code}")
revisar("formulario visible sin sesion", 'name="mensaje"' in respuesta.text)
revisar("aviso de cuenta gratuita", "cuenta gratuita" in respuesta.text)
revisar("enlaces de acceso sin sesion", "/login" in respuesta.text and "/registro" in respuesta.text)
revisar("alias /register disponible", app.test_client().get("/register").status_code == 200)
revisar("sin datos precargados", 'name="nombre" value=""' in respuesta.text or 'value="" required placeholder="Ej.' in respuesta.text)

respuesta = anonimo.post("/contacto", data={"nombre": "X", "correo": "x@ejemplo.ec", "fecha": "2030-01-01", "tipo": "Visita a obra", "mensaje": "Mensaje de prueba largo"})
revisar(
    "envio de cita exige sesion",
    respuesta.status_code == 302 and "/login" in respuesta.headers["Location"] and "next=/contacto" in respuesta.headers["Location"],
    f"-> {respuesta.headers['Location']}",
)
with app.app_context():
    revisar("no se guardo cita anonima", Cita.query.count() == 0)

cliente_usuario = app.test_client()
registrar(cliente_usuario, "Luis Arroyo", "luis@ejemplo.ec")
respuesta = cliente_usuario.get("/admin")
revisar("cliente recibe 403 en /admin", respuesta.status_code == 403, f"-> {respuesta.status_code}")
revisar("plantilla 403 personalizada", "Acceso restringido" in respuesta.text)

print()
print("=== 5. CALCULADORA Y RELACION CON EL USUARIO ===")
respuesta = presupuesto(anonimo, "Proyecto invitado")
revisar("calculadora libre para invitados", respuesta.status_code == 200 and "Total estimado" in respuesta.text)
revisar("aviso de invitado", "calculando como invitado" in respuesta.text)
with app.app_context():
    cotizacion = Cotizacion.query.filter_by(proyecto="Proyecto invitado").one()
    revisar("cotizacion anonima guardada", cotizacion is not None)
    revisar("sin user_id", cotizacion.user_id is None)
    revisar("estado pendiente por defecto", cotizacion.estado == "Pendiente")

respuesta = presupuesto(cliente_usuario, "Proyecto de Luis")
revisar("calculadora con sesion", respuesta.status_code == 200)
revisar("aviso de cuenta", "Estimación guardada en tu cuenta" in respuesta.text)
with app.app_context():
    cotizacion = Cotizacion.query.filter_by(proyecto="Proyecto de Luis").one()
    usuario = User.query.filter_by(correo="luis@ejemplo.ec").one()
    revisar("user_id asociado", cotizacion.user_id == usuario.id, f"-> {cotizacion.user_id}")

print()
print("=== 6. HISTORIAL DEL CLIENTE ===")
presupuesto(cliente_usuario, "Segundo proyecto Luis")
otro_cliente = app.test_client()
registrar(otro_cliente, "Ana Ríos", "ana@ejemplo.ec")
presupuesto(otro_cliente, "Proyecto de Ana")

respuesta = cliente_usuario.get("/mis-solicitudes")
revisar("GET /mis-solicitudes", respuesta.status_code == 200)
revisar("ve su proyecto", "Proyecto de Luis" in respuesta.text)
revisar("ve su segundo proyecto", "Segundo proyecto Luis" in respuesta.text)
revisar("no ve proyectos ajenos", "Proyecto de Ana" not in respuesta.text)
revisar("resumen de cuenta", "Cotizaciones" in respuesta.text)

with app.app_context():
    con_usuario = Cotizacion.query.filter(Cotizacion.user_id.isnot(None)).count()
    revisar("todas las cotizaciones con user_id", con_usuario == 3, f"-> {con_usuario}")

respuesta = cliente_usuario.get("/cotizacion/9999")
revisar("detalle inexistente da 404", respuesta.status_code == 404)

with app.app_context():
    id_ajeno = Cotizacion.query.filter_by(proyecto="Proyecto de Ana").one().id
respuesta = cliente_usuario.get(f"/cotizacion/{id_ajeno}")
revisar("no puede ver cotizacion ajena", respuesta.status_code == 404, f"-> {respuesta.status_code}")

print()
print("=== 7. AGENDAMIENTO CON SESION ===")
respuesta = cliente_usuario.get("/contacto")
revisar("GET /contacto con sesion", respuesta.status_code == 200)
revisar("banner de sesion iniciada", "Sesión iniciada como" in respuesta.text)
revisar("datos precargados de la cuenta", 'name="correo" value="luis@ejemplo.ec"' in respuesta.text)
revisar("enlace a historial", "/mis-solicitudes" in respuesta.text)

respuesta = cliente_usuario.post(
    "/contacto",
    data={
        "nombre": "Luis Arroyo",
        "correo": "luis@ejemplo.ec",
        "telefono": "+593 9 1111 2222",
        "fecha": "2030-05-20",
        "tipo": "Visita a obra",
        "mensaje": "Necesitamos revisar un polideportivo de 900 m2 en Quito.",
    },
    follow_redirects=True,
)
revisar("cita registrada", "Registramos tu solicitud" in respuesta.text)
with app.app_context():
    cita = Cita.query.one()
    revisar("cita con user_id", cita.user_id is not None)
    revisar("cita pendiente", cita.estado == "Pendiente" and cita.atendida is False)

respuesta = otro_cliente.get("/mis-solicitudes")
revisar("cliente ve solo su cita", "Visita a obra" not in respuesta.text)
respuesta = cliente_usuario.get("/mis-solicitudes")
revisar("cliente ve su cita", "Visita a obra" in respuesta.text)

print()
print("=== 8. PANEL DE ADMINISTRACION ===")
crear_admin()
admin = app.test_client()
respuesta = entrar(admin, "admin@polideportivos.ec", "AdminSegura2026")
revisar("login de administrador", respuesta.status_code == 200)
with app.app_context():
    revisar("rol admin verificado", User.query.filter_by(correo="admin@polideportivos.ec").one().es_admin is True)

respuesta = admin.get("/admin")
revisar("GET /admin", respuesta.status_code == 200, f"-> {respuesta.status_code}")
revisar("lista cotizaciones", "Proyecto de Luis" in respuesta.text)
revisar("marca visitante anonimo", "Visitante anónimo" in respuesta.text)
revisar("resumen de inversion", "Inversión estimada" in respuesta.text)
revisar("enlace a materiales", "/admin/materiales" in respuesta.text)

respuesta = admin.get("/admin?seccion=citas")
revisar("seccion de citas", respuesta.status_code == 200 and "Citas y asesorías" in respuesta.text)
revisar("lista citas", "Luis Arroyo" in respuesta.text)
revisar("panel abre en cotizaciones", "Cotizaciones enviadas" in admin.get("/admin").get_data(as_text=True))
respuesta = admin.get("/admin?estado=Aprobado")
revisar("filtro por estado", respuesta.status_code == 200 and "No hay cotizaciones" in respuesta.text)
respuesta = admin.get("/admin?seccion=citas&estado=Pendiente")
revisar("filtro de citas pendiente", "Visita a obra" in respuesta.text)
respuesta = admin.get("/admin?q=Proyecto+de+Ana")
revisar("busqueda de cotizaciones", "Proyecto de Ana" in respuesta.text and "Proyecto de Luis" not in respuesta.text)

respuesta = admin.get("/admin/usuarios")
revisar("listado de cuentas", respuesta.status_code == 200 and "maria@ejemplo.ec" in respuesta.text)
revisar("badge de administrador", "Administrador" in respuesta.text)

print()
print("=== 9. CAMBIO DE ESTADO ===")
with app.app_context():
    id_cotizacion = Cotizacion.query.filter_by(proyecto="Proyecto de Luis").one().id
    id_cita = Cita.query.one().id

respuesta = admin.post(
    f"/admin/solicitudes/cotizacion/{id_cotizacion}/estado",
    data={"estado": "Aprobado", "observaciones": "Presupuesto validado en sitio."},
)
revisar("cambio de estado responde 302", respuesta.status_code == 302)
with app.app_context():
    cotizacion = db.session.get(Cotizacion, id_cotizacion)
    revisar("estado actualizado", cotizacion.estado == "Aprobado", f"-> {cotizacion.estado}")
    revisar("observaciones guardadas", cotizacion.observaciones == "Presupuesto validado en sitio.")

respuesta = admin.post(f"/admin/solicitudes/cita/{id_cita}/estado", data={"estado": "Aprobado"})
with app.app_context():
    cita = db.session.get(Cita, id_cita)
    revisar("cita aprobada", cita.estado == "Aprobado")
    revisar("cita marcada atendida", cita.atendida is True)

respuesta = admin.post(
    f"/admin/solicitudes/cotizacion/{id_cotizacion}/estado", data={"estado": "Inventado"}
)
with app.app_context():
    revisar("estado invalido rechazado", db.session.get(Cotizacion, id_cotizacion).estado == "Pendiente", "-> vuelve a Pendiente")

respuesta = admin.post("/admin/solicitudes/inventado/1/estado", data={"estado": "Aprobado"})
revisar("tipo de solicitud invalido", respuesta.status_code == 302)

respuesta = admin.post(f"/admin/solicitudes/cotizacion/9999/estado", data={"estado": "Aprobado"})
revisar("registro inexistente da 404", respuesta.status_code == 404)

print()
print("=== 10. GESTION DE MATERIALES ===")
respuesta = admin.get("/admin/materiales")
revisar("GET /admin/materiales", respuesta.status_code == 200)
revisar("formulario de alta", 'action="/admin/materiales"' in respuesta.text)
revisar("formularios de edicion", respuesta.text.count('name="precio"') >= 13, f"-> {respuesta.text.count('name=\"precio\"')}")

respuesta = admin.post(
    "/admin/materiales",
    data={
        "nombre": "Pintura acrílica sportiva",
        "clave": "pintura_sportiva",
        "unidad": "m2",
        "categoria": "Acabados",
        "precio": "12.50",
        "merma": "8",
        "descripcion": "Recubrimiento antideslizante para canchas.",
    },
    follow_redirects=True,
)
revisar("material creado", "Material agregado al catálogo" in respuesta.text)
with app.app_context():
    material = Material.query.filter_by(clave="pintura_sportiva").one()
    revisar("precio guardado", abs(material.precio_referencial - 12.5) < 0.01)
    revisar("clave normalizada", material.clave == "pintura_sportiva")
    id_material = material.id

respuesta = admin.post(
    "/admin/materiales",
    data={"nombre": "Otro", "clave": "pintura_sportiva", "unidad": "m2", "categoria": "Acabados", "precio": "1", "merma": "0", "descripcion": "x"},
    follow_redirects=True,
)
revisar("clave duplicada rechazada", "ya existe un material" in respuesta.text)
with app.app_context():
    revisar("no se duplico el material", Material.query.filter_by(clave="pintura_sportiva").count() == 1)

respuesta = admin.post(
    f"/admin/materiales/{id_material}",
    data={
        "nombre": "Pintura acrílica sportiva",
        "clave": "pintura_sportiva",
        "unidad": "m2",
        "categoria": "Acabados",
        "precio": "15.75",
        "merma": "10",
        "descripcion": "Recubrimiento antideslizante certificado.",
    },
    follow_redirects=True,
)
revisar("material actualizado", "actualizado" in respuesta.text)
with app.app_context():
    material = db.session.get(Material, id_material)
    revisar("precio actualizado", abs(material.precio_referencial - 15.75) < 0.01)
    revisar("merma actualizada", abs(material.merma_pct - 10.0) < 0.01)
    revisar("precio con merma", abs(material.precio_con_merma - 17.33) < 0.02, f"-> {material.precio_con_merma}")

respuesta = admin.post(
    f"/admin/materiales/{id_material}",
    data={"nombre": "X", "clave": "pintura_sportiva", "unidad": "m2", "categoria": "Acabados", "precio": "-5", "merma": "0", "descripcion": "x"},
    follow_redirects=True,
)
revisar("precio negativo rechazado", "no puede ser negativo" in respuesta.text)
with app.app_context():
    revisar("precio intacto", abs(db.session.get(Material, id_material).precio_referencial - 15.75) < 0.01)

respuesta = admin.post(f"/admin/materiales/{id_material}/eliminar", follow_redirects=True)
revisar("material eliminado", "eliminado del catálogo" in respuesta.text)
with app.app_context():
    revisar("material ya no existe", db.session.get(Material, id_material) is None)
    revisar("catalogo original intacto", Material.query.filter_by(clave="hormigon_premezclado").count() == 1)

print()
print("=== 11. NAVEGACION DINAMICA ===")
html_anonimo = anonimo.get("/").get_data(as_text=True)
revisar("anonimo ve iniciar sesion", "/login" in html_anonimo and "Iniciar sesión" in html_anonimo)
revisar("anonimo ve crear cuenta", "Crear cuenta" in html_anonimo)
revisar("anonimo no ve panel", "Panel de administración" not in html_anonimo)
revisar("anonimo no ve mis solicitudes", "Mis solicitudes" not in html_anonimo)

html_usuario = cliente_usuario.get("/").get_data(as_text=True)
revisar("cliente ve su nombre", "Luis Arroyo" in html_usuario)
revisar("cliente ve mis solicitudes", "Mis solicitudes" in html_usuario)
revisar("cliente no ve panel admin", "Panel de administración" not in html_usuario)
revisar("cliente ve badge Cliente", "Cliente" in html_usuario)
revisar("cliente no ve boton login", "Iniciar sesión" not in html_usuario)
revisar("menu movil con cierre", "/logout" in html_usuario)
revisar("iniciales en el menu", "LA" in html_usuario)

html_admin = admin.get("/").get_data(as_text=True)
revisar("admin ve panel", "Panel de administración" in html_admin)
revisar("admin ve gestion de materiales", "Gestionar materiales" in html_admin)
revisar("admin ve badge Administrador", "Administrador" in html_admin)

print()
print("=== 12. CLI Y MIGRACIONES ===")
resultado = app.test_cli_runner().invoke(args=["crear-admin", "--nombre", "CLI Admin", "--correo", "cli@polideportivos.ec", "--clave", "CliSegura2026"])
revisar("CLI crear-admin", resultado.exit_code == 0, f"-> {resultado.output.strip()}")
with app.app_context():
    creado = User.query.filter_by(correo="cli@polideportivos.ec").one()
    revisar("admin creado por CLI", creado.rol == "admin" and creado.check_password("CliSegura2026"))

resultado = app.test_cli_runner().invoke(args=["crear-admin", "--nombre", "CLI Admin", "--correo", "cli@polideportivos.ec", "--clave", "CliSegura2026"])
with app.app_context():
    revisar("CLI idempotente", User.query.filter_by(correo="cli@polideportivos.ec").count() == 1)

resultado = app.test_cli_runner().invoke(args=["init-db"])
revisar("CLI init-db", resultado.exit_code == 0 and "Migraciones" in resultado.output, f"-> {resultado.output.strip()}")

print()
print("=== 13. MIGRACION DE BASE EXISTENTE ===")
ruta_vieja = os.path.join(tempfile.mkdtemp(), "vieja.db")
import sqlite3

conexion = sqlite3.connect(ruta_vieja)
conexion.executescript(
    """
    CREATE TABLE cotizaciones (id INTEGER PRIMARY KEY, proyecto VARCHAR(150) NOT NULL,
        solicitante VARCHAR(120), correo VARCHAR(180), largo FLOAT NOT NULL, ancho FLOAT NOT NULL,
        altura FLOAT NOT NULL, num_canchas INTEGER NOT NULL, superficie FLOAT NOT NULL,
        costo_directo FLOAT NOT NULL, costo_total FLOAT NOT NULL, detalle_json TEXT NOT NULL,
        creada_en DATETIME NOT NULL);
    CREATE TABLE citas (id INTEGER PRIMARY KEY, nombre VARCHAR(120) NOT NULL, correo VARCHAR(180) NOT NULL,
        telefono VARCHAR(40), fecha DATE NOT NULL, tipo VARCHAR(40) NOT NULL, mensaje TEXT NOT NULL,
        atendida BOOLEAN NOT NULL, creada_en DATETIME NOT NULL);
    INSERT INTO cotizaciones (proyecto, largo, ancho, altura, num_canchas, superficie, costo_directo,
        costo_total, detalle_json, creada_en)
    VALUES ('Legacy', 10, 10, 6, 1, 100, 1000, 1180, '[]', '2024-01-01 10:00:00');
    """
)
conexion.commit()
conexion.close()

app_vieja = create_app({"SQLALCHEMY_DATABASE_URI": f"sqlite:///{ruta_vieja}", "TESTING": True})
with app_vieja.app_context():
    revisar("dato preexistente conservado", Cotizacion.query.filter_by(proyecto="Legacy").one().costo_total == 1180)
    revisar("estado por defecto en legado", Cotizacion.query.filter_by(proyecto="Legacy").one().estado == "Pendiente")
    revisar("user_id nulo en legado", Cotizacion.query.filter_by(proyecto="Legacy").one().user_id is None)
    revisar("tabla usuarios creada", User.query.count() == 0)

app_vieja_2 = create_app({"SQLALCHEMY_DATABASE_URI": f"sqlite:///{ruta_vieja}", "TESTING": True})
with app_vieja_2.app_context():
    revisar("migracion idempotente", Cotizacion.query.count() == 1)
    revisar("catalogo sembrado tras migrar", Material.query.count() == 12)

print()
print("=== 14. PERSISTENCIA DE SESION ===")
persistido = app.test_client()
entrar(persistido, "maria@ejemplo.ec")
respuesta = persistido.get("/mis-solicitudes")
revisar("sesion activa entre peticiones", respuesta.status_code == 200 and "María Fernanda" in respuesta.text)
cookie = persistido.get_cookie("session")
revisar("cookie de sesion presente", cookie is not None and cookie.http_only)

print()
if fallos:
    print(f"FALLOS ({len(fallos)}): {fallos}")
    sys.exit(1)
print("AUTENTICACION Y ROLES: TODO VERIFICADO")