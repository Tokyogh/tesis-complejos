from util import crear_app_de_pruebas

from app.models import Material

app = crear_app_de_pruebas("visual")
cliente = app.test_client()

fallos = []


def revisar(nombre, condicion, detalle=""):
    print(f"[{'OK ' if condicion else 'FAIL'}] {nombre} {detalle}")
    if not condicion:
        fallos.append(nombre)


with app.app_context():
    claves = [m.clave for m in Material.query.all()]

datos = {
    "proyecto": "Polideportivo Comunal Norte",
    "solicitante": "Ana Pérez",
    "correo": "ana@ejemplo.cl",
    "largo": "28", "ancho": "15", "altura": "8",
    "espesor_losa": "0.15", "num_canchas": "2", "indirectos": "18",
    "componentes": claves,
}

marcadores_diseno = ["patron-plano", "bg-acero-700", "bg-arcilla-500", "cifra", "nav-enlace"]

paginas = {
    "/": None,
    "/materiales": ["shadow-card", "bg-arcilla-50", "border-b-2", "modal-material", "tarjeta-material"],
    "/calculadora": ["campo", "marca-esquina", "componente-check"],
    "/contacto": ["campo", "marca-esquina", "font-mono"],
    "/no-existe": None,
}

for ruta_pagina, extras in paginas.items():
    respuesta = cliente.get(ruta_pagina)
    revisar(f"GET {ruta_pagina}", respuesta.status_code in (200, 404), f"-> {respuesta.status_code}")
    html = respuesta.get_data(as_text=True)
    esperados = marcadores_diseno + (extras or [])
    faltantes = [m for m in esperados if m not in html]
    revisar(f"  diseño aplicado en {ruta_pagina}", not faltantes, f"faltan: {faltantes}" if faltantes else "")

respuesta = cliente.post("/calculadora", data=datos)
html = respuesta.get_data(as_text=True)
revisar("POST /calculadora con diseño", respuesta.status_code == 200 and "patron-plano" in html)
revisar("total con formato USD", "$215,866.00" in html, )
revisar("barra de partida presente", "barra-partida" in html)
revisar("data attributes para CSV", html.count("data-componente=") == 12, f"-> {html.count('data-componente=')} filas")
revisar("id res-total presente", 'id="res-total"' in html)
revisar("encabezado acero en tabla", "border-acero-700" in html or "bg-acero-700" in html)

respuesta = cliente.get("/materiales")
html = respuesta.get_data(as_text=True)
revisar("precios USD en catálogo", "$150.00" in html)
revisar("etiqueta de categoría naranja", "bg-arcilla-50" in html)
revisar("codigo de material", "M01" in html or "M12" in html)

cliente.post("/registro", data={
    "nombre": "Carlos Díaz", "correo": "carlos@municipal.cl",
    "clave": "Polideportivo2026", "clave_confirmacion": "Polideportivo2026", "acepto": "1",
}, follow_redirects=True)
respuesta = cliente.post("/contacto", data={
    "nombre": "Carlos Díaz", "correo": "carlos@municipal.cl", "telefono": "+56 9 1234 5678",
    "fecha": "2026-11-20", "tipo": "Visita a obra",
    "mensaje": "Necesitamos revisar un polideportivo de 900 m2 en Rancagua.",
}, follow_redirects=True)
html = respuesta.get_data(as_text=True)
revisar("aviso de éxito con diseño", respuesta.status_code == 200 and "Registramos tu solicitud" in html)

print()
if fallos:
    print(f"FALLOS ({len(fallos)}): {fallos}")
    raise SystemExit(1)
print("REDISEÑO VERIFICADO: TODAS LAS COMPROBACIONES PASARON")