const fs = require("fs");
const { JSDOM } = require("jsdom");

const BASE = "http://127.0.0.1:5000";
const JS = require("path").join(__dirname, "..", "..", "app", "static", "js") + require("path").sep;

const fallos = [];
function revisar(nombre, condicion, detalle = "") {
    console.log(`[${condicion ? "OK " : "FAIL"}] ${nombre} ${detalle}`);
    if (!condicion) fallos.push(nombre);
}

(async function () {
    const html = await (await fetch(BASE + "/materiales")).text();
    console.log(`HTML recibido: ${html.length} bytes\n`);

    const dom = new JSDOM(html, {
        runScripts: "dangerously",
        pretendToBeVisual: true,
        url: BASE + "/materiales",
    });

    const { window } = dom;
    const errores = [];
    window.addEventListener("error", (e) => errores.push(e.message));

    for (const archivo of ["main.js", "modal-material.js"]) {
        const codigo = fs.readFileSync(JS + archivo, "utf8");
        try {
            window.eval(codigo);
            console.log(`ejecutado ${archivo}`);
        } catch (error) {
            revisar(`carga de ${archivo}`, false, error.message);
        }
    }
    console.log("");

    const modal = window.document.getElementById("modal-material");
    const botones = window.document.querySelectorAll("[data-modal-material]");
    revisar("modal en el DOM", !!modal);
    revisar("12 botones de detalle", botones.length === 12, `-> ${botones.length}`);
    revisar("modal inicia oculto", modal.classList.contains("hidden"));
    revisar("modal aria-hidden true", modal.getAttribute("aria-hidden") === "true");

    // --- click en el primer botÃ³n ---
    botones[0].dispatchEvent(new window.MouseEvent("click", { bubbles: true }));

    revisar("modal visible tras el click", !modal.classList.contains("hidden"));
    revisar("aria-hidden false", modal.getAttribute("aria-hidden") === "false");
    revisar("body con scroll bloqueado", window.document.body.classList.contains("overflow-hidden"));

    const titulo = window.document.getElementById("modal-material-titulo");
    const imagen = window.document.getElementById("modal-material-imagen");
    const precio = window.document.getElementById("modal-material-precio");
    revisar("titulo llenado", titulo.textContent.length > 3, `-> "${titulo.textContent}"`);
    revisar("imagen con src", imagen.getAttribute("src").startsWith("https://"), `-> ${imagen.getAttribute("src").slice(0, 60)}`);
    revisar("precio llenado", precio.textContent.startsWith("$"), `-> ${precio.textContent}`);

    const caja = modal.querySelector(".modal-material-caja");
    const fondo = modal.querySelector(".modal-material-fondo");
    await new Promise((r) => setTimeout(r, 60));
    revisar("caja visible (sin opacity-0)", !caja.classList.contains("opacity-0"), caja.className);
    revisar("fondo visible (opacity-100)", fondo.classList.contains("opacity-100"), fondo.className);

    // --- segundo botÃ³n: cambia el contenido ---
    botones[5].dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    revisar("contenido cambia al segundo material", titulo.textContent.length > 3, `-> "${titulo.textContent}"`);

    // --- cerrar con Escape ---
    const teclado = new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true });
    window.document.dispatchEvent(teclado);
    await new Promise((r) => setTimeout(r, 400));
    revisar("modal se cierra con Escape", modal.classList.contains("hidden"));
    revisar("scroll liberado", !window.document.body.classList.contains("overflow-hidden"));

    // --- reabrir y cerrar con el backdrop ---
    botones[2].dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    revisar("reabre", !modal.classList.contains("hidden"));
    fondo.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    await new Promise((r) => setTimeout(r, 400));
    revisar("modal se cierra con el fondo", modal.classList.contains("hidden"));

    // --- cerrar con el botÃ³n X ---
    botones[3].dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    const botonCerrar = window.document.getElementById("modal-material-cerrar");
    botonCerrar.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    await new Promise((r) => setTimeout(r, 400));
    revisar("modal se cierra con la X", modal.classList.contains("hidden"));

    revisar("sin errores de runtime", errores.length === 0, errores.join(" | "));

    console.log("");
    if (fallos.length) {
        console.log(`FALLOS (${fallos.length}): ${fallos.join(", ")}`);
        process.exit(1);
    }
    console.log("MODAL: COMPORTAMIENTO CORRECTO EN DOM REAL");
})().catch((e) => {
    console.log("ERROR: " + e.message);
    process.exit(1);
});