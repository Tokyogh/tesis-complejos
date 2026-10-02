import re

from util import crear_app_de_pruebas

app = crear_app_de_pruebas("portada")
cliente = app.test_client()

fallos = []


def revisar(nombre, condicion, detalle=""):
    print(f"[{'OK ' if condicion else 'FAIL'}] {nombre} {detalle}")
    if not condicion:
        fallos.append(nombre)


html = cliente.get("/").get_data(as_text=True)
revisar("GET / responde 200", cliente.get("/").status_code == 200)
revisar("sin errores de Jinja", "Traceback" not in html and "UndefinedError" not in html)

imagenes = re.findall(r'<img[^>]+src="([^"]+)"', html)
revisar("portada tiene 3+ imagenes", len(imagenes) >= 3, f"-> {len(imagenes)}")

proyectos = re.findall(r'<article[^>]*>.*?</article>', html, re.S)
revisar("6 tarjetas de proyecto", len(proyectos) == 6, f"-> {len(proyectos)}")

for proyecto in proyectos:
    if "<img" not in proyecto:
        fallos.append("proyecto sin imagen")
revisar("cada proyecto con foto", all("<img" in p for p in proyectos))

ciudades = ["Guayaquil", "Quito", "Cuenca", "Manta", "Portoviejo"]
presentes = [c for c in ciudades if c in html]
revisar("ciudades ecuatorianas en portafolio", len(presentes) == 5, f"-> {presentes}")

residuos = [t for t in ["Chile", "+56", "@polideportivos.cl", "Santiago", "Rancagua"] if t in html]
revisar("sin residuos de Chile", not residuos, f"-> {residuos}")

revisar("marcadores de diseño", all(m in html for m in ["patron-plano", "bg-acero-700", "bg-arcilla-500", "cifra", "nav-enlace"]))
revisar("loading lazy en portafolio", html.count('loading="lazy"') >= 6, f"-> {html.count('loading=\"lazy\"')}")
revisar("referrerpolicy en imagenes", html.count('referrerpolicy="no-referrer"') >= 8)

print()
if fallos:
    print(f"FALLOS ({len(fallos)}): {fallos}")
    sys.exit(1)
print("PORTADA OK")