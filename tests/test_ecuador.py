import re

from util import crear_app_de_pruebas

from app.models import Material

app = crear_app_de_pruebas("ecuador")
cliente = app.test_client()

fallos = []


def revisar(nombre, condicion, detalle=""):
    print(f"[{'OK ' if condicion else 'FAIL'}] {nombre} {detalle}")
    if not condicion:
        fallos.append(nombre)


with app.app_context():
    claves = [m.clave for m in Material.query.all()]

html = cliente.get("/materiales").get_data(as_text=True)

tarjetas = re.findall(r'<article class="tarjeta-material.*?</article>', html, re.S)
revisar("12 tarjetas de material", len(tarjetas) == 12, f"-> {len(tarjetas)}")

imagenes = re.findall(r'<article class="tarjeta-material.*?<img src="([^"]+)"', html, re.S)
revisar("cada tarjeta tiene foto", len(imagenes) == 12, f"-> {len(imagenes)}")
revisar("fotos de Wikimedia", all("wikimedia.org" in u for u in imagenes), f"-> {len(set(imagenes))} unicas")
revisar("fotos distintas", len(set(imagenes)) == 12, f"-> {len(set(imagenes))}")

disparadores = re.findall(r'data-modal-material', html)
revisar("12 botones de detalle", len(disparadores) == 12, f"-> {len(disparadores)}")

atributos = re.findall(r'data-(codigo|nombre|categoria|unidad|precio|precio-merma|merma|descripcion|imagen|licencia|fuente)="', html)
revisar("data attributes completos", len(atributos) == 12 * 11, f"-> {len(atributos)} de {12 * 11}")

for identificador in [
    "modal-material", "modal-material-imagen", "modal-material-codigo", "modal-material-categoria",
    "modal-material-titulo", "modal-material-descripcion", "modal-material-unidad",
    "modal-material-precio", "modal-material-precio-merma", "modal-material-merma", "modal-material-credito",
    "modal-material-cerrar",
]:
    if f'id="{identificador}"' not in html:
        revisar(f"modal #{identificador}", False)
revisar("modal completo", all(f'id="{i}"' in html for i in [
    "modal-material", "modal-material-imagen", "modal-material-codigo", "modal-material-categoria",
    "modal-material-titulo", "modal-material-descripcion", "modal-material-unidad",
    "modal-material-precio", "modal-material-precio-merma", "modal-material-merma", "modal-material-credito",
    "modal-material-cerrar",
]))

revisar("modal con role dialog", 'role="dialog"' in html and 'aria-modal="true"' in html)
revisar("modal oculto al cargar", 'class="modal-material fixed inset-0 z-[60] hidden"' in html)
revisar("codigos M01 a M12", all(f"M{i:02d}" in html for i in range(1, 13)))
revisar("script del modal incluido", "js/modal-material.js" in html)

respuesta = cliente.get("/static/js/modal-material.js")
revisar("modal-material.js servido", respuesta.status_code == 200, f"-> {respuesta.status_code}")

residuos = []
for pagina in ["/", "/materiales", "/calculadora", "/contacto"]:
    cuerpo = cliente.get(pagina).get_data(as_text=True)
    for termino in ["Chile", "+56 9", "@polideportivos.cl", "organizacion.cl", "empresa.cl", "Santiago, Chile"]:
        if termino in cuerpo:
            residuos.append(f"{pagina}:{termino}")
revisar("sin residuos de Chile en el sitio", not residuos, f"-> {residuos}")

contacto = cliente.get("/contacto").get_data(as_text=True)
revisar("telefono +593", "+593 2 000 0000" in contacto)
revisar("correo .ec", "contacto@polideportivos.ec" in contacto)
revisar("direccion Quito", "Quito, Pichincha" in contacto)
revisar("placeholder .ec", "@organizacion.ec" in contacto)
revisar("telefono placeholder ecuadoreno", "+593 9 1234 5678" in contacto)

with app.app_context():
    hormigon = Material.query.filter_by(clave="hormigon_premezclado").one()
    revisar("descripcion con H20", "H20" in hormigon.descripcion)
    portal = Material.query.filter_by(clave="portales_estructura").one()
    revisar("descripcion con NEC-15", "NEC-15" in portal.descripcion)
    led = Material.query.filter_by(clave="luminaria_led").one()
    revisar("descripcion con lux", "lux" in led.descripcion)

portada = cliente.get("/").get_data(as_text=True)
revisar("portada menciona Ecuador", "Ecuador" in portada)
revisar("portada sin color oscuro dominante", 'bg-acero-950 text-white' not in portada)

print()
if fallos:
    print(f"FALLOS ({len(fallos)}): {fallos}")
    sys.exit(1)
print("CATALOGO + MODAL + ECUADOR: TODO VERIFICADO")