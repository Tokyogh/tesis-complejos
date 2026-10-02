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
datos.set("solicitante", "Ana Perez");
datos.set("correo", "ana@ejemplo.ec");
datos.set("largo", "28");
datos.set("ancho", "15");
datos.set("altura", "8");
datos.set("espesor_losa", "0.15");
datos.set("num_canchas", "2");
datos.set("indirectos", "18");
["terreno_compactacion", "hormigon_premezclado", "piso_deportivo", "luminaria_led"].forEach((c) =>
    datos.append("componentes", c)
);

(async function () {
    const html = await (await fetch(BASE + "/calculadora", { method: "POST", body: datos })).text();
    const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: BASE + "/calculadora" });
    const { window } = dom;

    let capturado = null;
    let nombreDescarga = null;
    window.URL.createObjectURL = (blob) => {
        capturado = blob;
        return "blob:mock";
    };
    window.URL.revokeObjectURL = () => {};

    window.eval(fs.readFileSync(JS + "main.js", "utf8"));
    window.eval(fs.readFileSync(JS + "calculator.js", "utf8"));
    const doc = window.document;

    const boton = doc.getElementById("descargar-detalle");
    revisar("botÃ³n de detalle existe", !!boton);

    // intercepta el click del enlace temporal para leer el nombre
    const crearOriginal = doc.createElement.bind(doc);
    doc.createElement = function (etiqueta) {
        const elemento = crearOriginal(etiqueta);
        if (etiqueta === "a") {
            const clickOriginal = elemento.click.bind(elemento);
            elemento.click = function () {
                nombreDescarga = elemento.download;
            };
            void clickOriginal;
        }
        return elemento;
    };

    // 1) CSV con precios de catÃ¡logo
    boton.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    let texto = await capturado.text();
    console.log("\n--- CSV CON PRECIOS DE CATALOGO ---");
    console.log(texto);
    revisar("nombre del archivo", nombreDescarga === "presupuesto-polideportivo.csv", `-> ${nombreDescarga}`);
    revisar("encabezado correcto", texto.includes('"Componente";"Material";"Cantidad";"Unidad";"Precio unitario";"Subtotal"'));
    revisar("sin marca de personalizaciÃ³n", !texto.includes("Personalizado"));
    revisar("total del catÃ¡logo", /"Total estimado";"\$[\d,]+\.\d{2}"/.test(texto), `-> ${(texto.match(/"Total estimado";"([^"]+)"/) || [])[1]}`);
    revisar("subtotal = cantidad x precio", texto.includes('"19845"') && texto.includes('"132.3"') && texto.includes('"150"'));

    // 2) editar un precio y volver a exportar
    const precio = doc.querySelector('.precio-personal[data-clave="hormigon_premezclado"]');
    precio.value = "200";
    precio.dispatchEvent(new window.Event("input", { bubbles: true }));
    boton.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    texto = await capturado.text();
    console.log("\n--- CSV CON PRECIO EDITADO ---");
    console.log(texto);
    revisar("marca de origen personalizada", texto.includes("Personalizado (editado en esta pantalla)"));
    revisar("precio editado en el CSV", /Terreno y fundaciones/.test(texto) && texto.includes("200"));
    revisar("aparece costo directo", /Costo direct o/.test(texto.replace(/,/g, "")) || texto.includes("Costo directo"));
    revisar("aparece gastos indirectos", texto.includes("Gastos indirectos"));

    console.log("");
    if (fallos.length) {
        console.log(`FALLOS (${fallos.length}): ${fallos.join(", ")}`);
        process.exit(1);
    }
    console.log("CSV: COMPORTAMIENTO CORRECTO");
})().catch((e) => {
    console.log("ERROR: " + e.message);
    process.exit(1);
});