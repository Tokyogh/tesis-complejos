from util import componentes_de_prueba, crear_app_de_pruebas

from app.models import Cita, Cotizacion, Material

app = crear_app_de_pruebas("calculadora")
cliente = app.test_client()

fallos = []


def revisar(nombre, condicion, detalle=""):
    estado = "OK " if condicion else "FAIL"
    print(f"[{estado}] {nombre} {detalle}")
    if not condicion:
        fallos.append(nombre)


with app.app_context():
    revisar("seed de materiales", Material.query.count() == 12, f"-> {Material.query.count()} materiales")
    revisar("precios positivos", all(m.precio_referencial > 0 for m in Material.query.all()))
    revisar("claves unicas", len({m.clave for m in Material.query.all()}) == Material.query.count())

respuesta = cliente.get("/")
revisar("GET /", respuesta.status_code == 200, f"-> {respuesta.status_code}, {len(respuesta.data)} bytes")
revisar("index con proyectos", b"Polideportivo Municipal" in respuesta.data)

respuesta = cliente.get("/materiales")
revisar("GET /materiales", respuesta.status_code == 200, f"-> {respuesta.status_code}")
revisar("catalogo muestra precios", b"Hormig" in respuesta.data)

respuesta = cliente.get("/materiales?categoria=Losas")
revisar("GET /materiales?categoria=Losas", respuesta.status_code == 200 and b"malla acanalada" in respuesta.data.lower())

respuesta = cliente.get("/materiales?categoria=Inexistente")
revisar("categoria inexistente -> listado completo", respuesta.status_code == 200)

respuesta = cliente.get("/calculadora")
revisar("GET /calculadora", respuesta.status_code == 200, f"-> {respuesta.status_code}")

datos = componentes_de_prueba(app)
datos["correo"] = "ana@ejemplo.cl"

respuesta = cliente.post("/calculadora", data=datos)
revisar("POST /calculadora", respuesta.status_code == 200, f"-> {respuesta.status_code}")
revisar("resultado con total", b"Total estimado" in respuesta.data)
revisar("area calculada 840 m2", b"840 m2" in respuesta.data)

with app.app_context():
    revisar("estimacion anonima no se persiste", Cotizacion.query.count() == 0)
    cotizacion = Cotizacion.query.first()
    revisar(
        "sin cotizacion anonima en historial",
        cotizacion is None,
    )

invalido = dict(datos)
invalido["largo"] = "0"
invalido["componentes"] = [c for c in datos["componentes"] if c != "hormigon_premezclado"]
respuesta = cliente.post("/calculadora", data=invalido)
revisar("validacion rechaza largo 0", b"mayores a cero" in respuesta.data and b"Total estimado" not in respuesta.data)

sin_componentes = dict(datos)
sin_componentes["componentes"] = []
respuesta = cliente.post("/calculadora", data=sin_componentes)
revisar("validacion exige componentes", b"al menos un componente" in respuesta.data)

api = cliente.post("/calculadora/api/estimar", json={
    "largo": 28, "ancho": 15, "altura": 8, "espesor_losa": 0.15,
    "num_canchas": 1, "indirectos": 18, "componentes": datos["componentes"],
})
revisar("API estimar", api.status_code == 200 and api.get_json()["ok"], f"-> {api.status_code}")
payload = api.get_json()["presupuesto"]
revisar("API entrega lineas", len(payload["lineas"]) == 12, f"-> {len(payload['lineas'])} lineas")
revisar(
    "total = directo + indirectos",
    payload["costo_total"] == payload["costo_directo"] + payload["monto_indirectos"],
)

api_invalido = cliente.post("/calculadora/api/estimar", json={"largo": -5, "componentes": []})
revisar("API rechaza datos inválidos", api_invalido.status_code == 400)

formulario = {
    "nombre": "Carlos Díaz",
    "correo": "carlos@municipal.cl",
    "telefono": "+56 9 1234 5678",
    "fecha": "2026-11-20",
    "tipo": "Visita a obra",
    "mensaje": "Necesitamos revisar un polideportivo de 900 m2 en Rancagua.",
}
respuesta = cliente.get("/contacto")
revisar("GET /contacto anonimo", respuesta.status_code == 200, f"-> {respuesta.status_code}")
respuesta = cliente.post("/contacto", data=formulario)
revisar(
    "POST /contacto anonimo redirige a login",
    respuesta.status_code == 302 and "/login" in respuesta.headers["Location"],
    f"-> {respuesta.headers.get('Location')}",
)

registro = {
    "nombre": "Carlos Díaz",
    "correo": "carlos@municipal.cl",
    "clave": "Polideportivo2026",
    "clave_confirmacion": "Polideportivo2026",
    "acepto": "1",
}
respuesta = cliente.post("/registro", data=registro, follow_redirects=True)
revisar("registro de cliente", "Bienvenido" in respuesta.text)

respuesta = cliente.post("/contacto", data=formulario, follow_redirects=True)
revisar("POST /contacto", respuesta.status_code == 200, f"-> {respuesta.status_code}")
revisar("confirmacion de cita", "Registramos tu solicitud" in respuesta.text)

with app.app_context():
    revisar("cita guardada", Cita.query.count() == 1)
    revisar("cita asociada al usuario", Cita.query.first().user_id is not None)

mal = dict(formulario)
mal["correo"] = "no-es-correo"
mal["fecha"] = "2020-01-01"
mal["mensaje"] = "corto"
respuesta = cliente.post("/contacto", data=mal)
revisar("validacion de cita", respuesta.status_code == 200 and b"correo electr" in respuesta.data)

respuesta = cliente.get("/ruta/inexistente")
revisar("404 personalizado", respuesta.status_code == 404 and b"P" in respuesta.data)

for activo in ("/static/css/custom.css", "/static/js/main.js", "/static/js/calculator.js", "/static/js/modal-material.js"):
    respuesta = cliente.get(activo)
    revisar(f"activo {activo}", respuesta.status_code == 200)

print()
if fallos:
    print(f"PRUEBAS FALLIDAS ({len(fallos)}): {fallos}")
    raise SystemExit(1)
print("TODAS LAS PRUEBAS PASARON")
