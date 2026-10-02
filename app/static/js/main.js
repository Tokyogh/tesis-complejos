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
})();