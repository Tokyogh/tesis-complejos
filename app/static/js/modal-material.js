(function () {
    "use strict";

    const modal = document.getElementById("modal-material");
    if (!modal) {
        return;
    }

    const fondo = modal.querySelector(".modal-material-fondo");
    const caja = modal.querySelector(".modal-material-caja");
    const botonCerrar = document.getElementById("modal-material-cerrar");
    const disparadores = document.querySelectorAll("[data-modal-material]");

    const campos = {
        imagen: document.getElementById("modal-material-imagen"),
        codigo: document.getElementById("modal-material-codigo"),
        categoria: document.getElementById("modal-material-categoria"),
        titulo: document.getElementById("modal-material-titulo"),
        descripcion: document.getElementById("modal-material-descripcion"),
        unidad: document.getElementById("modal-material-unidad"),
        precio: document.getElementById("modal-material-precio"),
        precioMerma: document.getElementById("modal-material-precio-merma"),
        merma: document.getElementById("modal-material-merma"),
        credito: document.getElementById("modal-material-credito")
    };

    let ultimoDisparador = null;
    let estaAbierto = false;

    const FOCABLES = 'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])';

    function dato(datos, clave) {
        const valor = datos[clave];
        return valor === undefined || valor === null ? "" : valor;
    }

    function llenar(datos) {
        const imagen = dato(datos, "imagen");

        if (imagen) {
            campos.imagen.src = imagen;
            campos.imagen.alt = dato(datos, "nombre") || "Material del catálogo";
            campos.imagen.classList.remove("hidden");
        } else {
            campos.imagen.classList.add("hidden");
        }

        campos.codigo.textContent = dato(datos, "codigo");
        campos.categoria.textContent = dato(datos, "categoria");
        campos.titulo.textContent = dato(datos, "nombre");
        campos.descripcion.textContent = dato(datos, "descripcion");
        campos.unidad.textContent = dato(datos, "unidad");
        campos.precio.textContent = dato(datos, "precio");
        campos.precioMerma.textContent = dato(datos, "precioMerma");
        campos.merma.textContent = "merma " + (dato(datos, "merma") || "0") + "%";

        const licencia = dato(datos, "licencia");
        const fuente = dato(datos, "fuente");
        campos.credito.textContent = licencia
            ? "Fotografía: " + fuente + " · Licencia " + licencia
            : "Fotografía: " + (fuente || "Wikimedia Commons");
    }

    function abrir(datos, disparador) {
        llenar(datos);
        ultimoDisparador = disparador || null;
        estaAbierto = true;

        modal.classList.remove("hidden");
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("overflow-hidden");

        window.requestAnimationFrame(function () {
            fondo.classList.replace("opacity-0", "opacity-100");
            caja.classList.remove("opacity-0", "translate-y-6", "scale-95");
        });

        if (botonCerrar) {
            botonCerrar.focus();
        }
    }

    function cerrar() {
        if (!estaAbierto) {
            return;
        }
        estaAbierto = false;

        fondo.classList.replace("opacity-100", "opacity-0");
        caja.classList.add("opacity-0", "translate-y-6", "scale-95");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("overflow-hidden");

        window.setTimeout(function () {
            if (!estaAbierto) {
                modal.classList.add("hidden");
            }
        }, 300);

        if (ultimoDisparador) {
            ultimoDisparador.focus();
        }
    }

    disparadores.forEach(function (disparador) {
        disparador.addEventListener("click", function () {
            abrir(disparador.dataset, disparador);
        });
    });

    if (botonCerrar) {
        botonCerrar.addEventListener("click", cerrar);
    }

    if (fondo) {
        fondo.addEventListener("click", cerrar);
    }

    document.addEventListener("keydown", function (evento) {
        if (!estaAbierto) {
            return;
        }

        if (evento.key === "Escape") {
            evento.preventDefault();
            cerrar();
            return;
        }

        if (evento.key !== "Tab") {
            return;
        }

        const focables = Array.prototype.filter.call(
            caja.querySelectorAll(FOCABLES),
            function (elemento) {
                return elemento.offsetParent !== null;
            }
        );

        if (!focables.length) {
            return;
        }

        const primero = focables[0];
        const ultimo = focables[focables.length - 1];

        if (evento.shiftKey && document.activeElement === primero) {
            evento.preventDefault();
            ultimo.focus();
        } else if (!evento.shiftKey && document.activeElement === ultimo) {
            evento.preventDefault();
            primero.focus();
        }
    });
})();