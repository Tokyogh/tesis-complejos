(function () {
    const boton = document.getElementById("menu-movil");
    const panel = document.getElementById("menu-panel");

    if (boton && panel) {
        boton.addEventListener("click", function () {
            const oculto = panel.classList.toggle("hidden");
            boton.setAttribute("aria-expanded", String(!oculto));
        });

        panel.querySelectorAll("a").forEach(function (enlace) {
            enlace.addEventListener("click", function () {
                panel.classList.add("hidden");
                boton.setAttribute("aria-expanded", "false");
            });
        });
    }

    const hoy = new Date().toISOString().slice(0, 10);
    document.querySelectorAll('input[type="date"]').forEach(function (campo) {
        if (!campo.min) {
            campo.min = hoy;
        }
    });

    const perfilMenu = document.getElementById("perfil-menu");
    const perfilBoton = document.getElementById("perfil-boton");
    const perfilPanel = document.getElementById("perfil-panel");

    function cerrarPerfil() {
        if (!perfilPanel || !perfilBoton) {
            return;
        }
        perfilPanel.classList.add("hidden");
        perfilBoton.setAttribute("aria-expanded", "false");
    }

    if (perfilMenu && perfilBoton && perfilPanel) {
        perfilBoton.addEventListener("click", function (evento) {
            evento.stopPropagation();
            const abierto = perfilPanel.classList.toggle("hidden");
            perfilBoton.setAttribute("aria-expanded", String(!abierto));
        });

        perfilPanel.querySelectorAll("a").forEach(function (enlace) {
            enlace.addEventListener("click", cerrarPerfil);
        });

        document.addEventListener("click", function (evento) {
            if (!perfilMenu.contains(evento.target)) {
                cerrarPerfil();
            }
        });

        document.addEventListener("keydown", function (evento) {
            if (evento.key === "Escape") {
                cerrarPerfil();
            }
        });
    }
})();
