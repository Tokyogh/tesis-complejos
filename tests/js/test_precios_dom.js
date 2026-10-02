const fs = require("fs");
const { JSDOM } = require("jsdom");

const BASE = "http://127.0.0.1:5000";
const JS = require("path").join(__dirname, "..", "..", "app", "static", "js") + require("path").sep;

const fallos = [];
function revisar(nombre, condicion, detalle = "") {
    console.log(`[${condicion ? "OK " : "FAIL"}] ${nombre} ${detalle}`);
    if (!condicion) fallos.push(nombre);
}

const datos = new URLSearchParams();
datos.set("proyecto", "Polideportivo Comunal Norte");
datos.set("solicitante", "Ana Pérez");
datos.set("correo", "ana@ejemplo.ec");
datos.set("largo", "28");
datos.set("ancho", "15");
datos.set("altura", "8");
datos.set("espesor_losa", "0.15");
datos.set("num_canchas", "2");
datos.set("indirectos", "18");
[
    "terreno_compactacion", "hormigon_premezclado", "malla_losa", "piso_deportivo",
    "cesped_sintetico", "estructura_cubierta", "portales_estructura", "malla_cerramiento",
    "postes_cercamiento", "luminaria_led", "demarcacion", "tablero_basquetbol",
].forEach((c) => datos.append("componentes", c));

(async function () {
    const html = await (await fetch(BASE + "/calculadora", { method: "POST", body: datos })).text();
    console.log(`HTML con resultados: ${html.length} bytes\n`);

    const dom = new JSDOM(html, {
        runScripts: "dangerously",
        pretendToBeVisual: true,
        url: BASE + "/calculadora",
    });
    const { window } = dom;
    const errores = [];
    window.addEventListener("error", (e) => errores.push(e.message));

    for (const archivo of ["main.js", "calculator.js"]) {
        try {
            window.eval(fs.readFileSync(JS + archivo, "utf8"));
        } catch (error) {
            revisar(`carga de ${archivo}`, false, error.message);
        }
    }

    const doc = window.document;
    const inputs = [...doc.querySelectorAll(".precio-personal")];
    const filas = [...doc.querySelectorAll("#panel-resultado tbody tr[data-componente]")];
    const total = doc.getElementById("res-total");
    const directo = doc.getElementById("res-costo-directo");
    const indirectosCelda = doc.getElementById("res-monto-indirectos");
    const totalDetalle = doc.getElementById("res-total-detalle");
    const m2 = doc.getElementById("res-costo-m2");
    const aviso = doc.getElementById("aviso-personalizado");
    const restablecer = doc.getElementById("restablecer-precios");

    revisar("12 precios editables", inputs.length === 12, `-> ${inputs.length}`);
    revisar("12 filas con data-clave", filas.every((f) => f.dataset.clave), `-> ${filas.length}`);
    revisar("aviso oculto al inicio", aviso.style.display === "none");
    revisar("botÃ³n restablecer oculto", restablecer.style.display === "none");

    function num(texto) {
        return parseFloat(String(texto).replace(/[^0-9.]/g, ""));
    }

    const totalInicial = total.textContent.trim();
    const directoInicial = num(directo.textContent);
    const sumaFilas = filas.reduce((acc, f) => acc + parseFloat(f.dataset.subtotal), 0);
    revisar("total inicial del servidor", totalInicial === "$215,866.00", `-> ${totalInicial}`);
    revisar("directo inicial = suma de filas", Math.abs(directoInicial - sumaFilas) <= 1, `-> ${directo.textContent} vs ${sumaFilas}`);

    // --- duplicar el precio del hormigÃ³n (10.5 -> 150) ---
    const hormigon = inputs.find((i) => i.dataset.clave === "hormigon_premezclado");
    const cantidadHormigon = parseFloat(hormigon.closest("tr").dataset.cantidad);
    hormigon.value = "300";
    hormigon.dispatchEvent(new window.Event("input", { bubbles: true }));

    const directoNuevo = num(directo.textContent);
    const esperadoDirecto = Math.round(directoInicial - 150 * cantidadHormigon + 300 * cantidadHormigon);
    revisar("costo directo recalculado", Math.abs(directoNuevo - esperadoDirecto) <= 1, `-> ${directo.textContent} (esperado ${esperadoDirecto})`);

    const esperadoIndirectos = Math.round((esperadoDirecto * 18) / 100);
    const indirectoNuevo = num(indirectosCelda.textContent);
    revisar("indirectos recalculados (18%)", Math.abs(indirectoNuevo - esperadoIndirectos) <= 1, `-> ${indirectosCelda.textContent}`);

    const esperadoTotal = Math.round(esperadoDirecto + esperadoIndirectos);
    revisar("total general actualizado", Math.abs(num(total.textContent) - esperadoTotal) <= 1, `-> ${total.textContent}`);
    revisar("total del detalle actualizado", Math.abs(num(totalDetalle.textContent) - esperadoTotal) <= 1, `-> ${totalDetalle.textContent}`);

    const esperadoM2 = Math.round(esperadoTotal / 840);
    revisar("costo por m2 actualizado", Math.abs(num(m2.textContent) - esperadoM2) <= 1, `-> ${m2.textContent}`);

    const filaHormigon = hormigon.closest("tr");
    revisar("subtotal de la fila actualizado", Math.abs(parseFloat(filaHormigon.dataset.subtotal) - Math.round(300 * cantidadHormigon)) <= 1, `-> ${filaHormigon.dataset.subtotal}`);
    revisar("celda de subtotal actualizada", Math.abs(num(filaHormigon.querySelector(".celda-subtotal").textContent) - Math.round(300 * cantidadHormigon)) <= 1, `-> ${filaHormigon.querySelector(".celda-subtotal").textContent}`);
    revisar("data-unitario actualizado", parseFloat(filaHormigon.dataset.unitario) === 300, `-> ${filaHormigon.dataset.unitario}`);

    revisar("aviso de cÃ¡lculo personalizado", aviso.style.display === "inline-block");
    revisar("botÃ³n restablecer visible", restablecer.style.display === "inline-block");
    revisar("input marcado como modificado", hormigon.classList.contains("precio-modificado"));

    const guardado = window.localStorage.getItem("polideportivopro.precios");
    revisar("precio persistido", guardado && guardado.includes("hormigon_premezclado"), `-> ${guardado}`);

    const barra = filaHormigon.querySelector(".barra-partida");
    revisar("barra de partida con ancho", barra.style.width && barra.style.width.endsWith("%"), `-> ${barra.style.width}`);

    // --- restablecer ---
    restablecer.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    revisar("precio vuelve al catÃ¡logo", parseFloat(hormigon.value) === 150, `-> ${hormigon.value}`);
    revisar("total vuelve al original", total.textContent.trim() === totalInicial, `-> ${total.textContent}`);
    revisar("aviso oculto tras restablecer", aviso.style.display === "none");
    revisar("almacenamiento limpio", !window.localStorage.getItem("polideportivopro.precios"));

    // --- editar a un valor invÃ¡lido (vacÃ­o) ---
    const terreno = inputs.find((i) => i.dataset.clave === "terreno_compactacion");
    terreno.value = "";
    terreno.dispatchEvent(new window.Event("input", { bubbles: true }));
    revisar("precio vacÃ­o no rompe el cÃ¡lculo", directo.textContent.startsWith("$"), `-> ${directo.textContent}`);
    revisar("subtotal en cero", parseFloat(terreno.closest("tr").dataset.subtotal) === 0);

    revisar("sin errores de runtime", errores.length === 0, errores.join(" | "));

    console.log("");
    if (fallos.length) {
        console.log(`FALLOS (${fallos.length}): ${fallos.join(", ")}`);
        process.exit(1);
    }
    console.log("PRECIOS EDITABLES: COMPORTAMIENTO CORRECTO");
})().catch((e) => {
    console.log("ERROR: " + e.message);
    process.exit(1);
});