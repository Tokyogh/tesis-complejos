(function () {
    const formulario = document.getElementById("form-calculadora");
    if (!formulario) {
        return;
    }

    const campos = ["largo", "ancho", "altura", "espesor_losa", "num_canchas", "indirectos"].map(function (id) {
        return document.getElementById(id);
    }).filter(Boolean);

    const checks = Array.prototype.slice.call(document.querySelectorAll(".componente-check"));
    const area = document.getElementById("res-area");
    const perimetro = document.getElementById("res-perimetro");
    const volumen = document.getElementById("res-volumen");
    const botonTodos = document.getElementById("seleccionar-todos");
    const botonNinguno = document.getElementById("limpiar-todos");
    const botonDescargar = document.getElementById("descargar-detalle");

    const totalGeneral = document.getElementById("res-total");
    const totalDetalle = document.getElementById("res-total-detalle");
    const costoDirectoCelda = document.getElementById("res-costo-directo");
    const montoIndirectosCelda = document.getElementById("res-monto-indirectos");
    const costoM2Celda = document.getElementById("res-costo-m2");
    const avisoPersonalizado = document.getElementById("aviso-personalizado");
    const botonRestablecer = document.getElementById("restablecer-precios");
    const inputsPrecio = Array.prototype.slice.call(document.querySelectorAll(".precio-personal"));
    const filasResultado = Array.prototype.slice.call(document.querySelectorAll("#panel-resultado tbody tr[data-componente]"));

    const preciosEditados = {};
    const CLAVE_ALMACEN = "polideportivopro.precios";

    function cargarPreciosGuardados() {
        try {
            const guardado = window.localStorage.getItem(CLAVE_ALMACEN);
            if (!guardado) {
                return;
            }
            const datos = JSON.parse(guardado);
            if (datos && typeof datos === "object") {
                Object.keys(datos).forEach(function (clave) {
                    const numero = parseFloat(datos[clave]);
                    if (!isNaN(numero) && numero >= 0) {
                        preciosEditados[clave] = numero;
                    }
                });
            }
        } catch (error) {
            /* el navegador puede bloquear el almacenamiento local */
        }
    }

    function persistirPrecios() {
        try {
            if (Object.keys(preciosEditados).length) {
                window.localStorage.setItem(CLAVE_ALMACEN, JSON.stringify(preciosEditados));
            } else {
                window.localStorage.removeItem(CLAVE_ALMACEN);
            }
        } catch (error) {
            /* el navegador puede bloquear el almacenamiento local */
        }
    }

    function valor(id) {
        const campo = document.getElementById(id);
        const numero = parseFloat(campo ? campo.value : "0");
        return isNaN(numero) ? 0 : numero;
    }

    function formato(numero, decimales) {
        return numero.toLocaleString("en-US", {
            minimumFractionDigits: decimales,
            maximumFractionDigits: decimales,
        });
    }

    function dinero(numero) {
        return "$" + formato(numero, 2);
    }

    function superficieCancha() {
        const largo = valor("largo");
        const ancho = valor("ancho");
        const canchas = Math.max(valor("num_canchas"), 1);
        return largo * ancho * canchas;
    }

    function marcarEstadoPersonalizado() {
        const hay = Object.keys(preciosEditados).length > 0;
        if (avisoPersonalizado) {
            avisoPersonalizado.style.display = hay ? "inline-block" : "none";
        }
        if (botonRestablecer) {
            botonRestablecer.style.display = hay ? "inline-block" : "none";
        }
    }

    function recalcularPrecios() {
        if (!filasResultado.length) {
            return;
        }

        const subtotales = [];
        let costoDirecto = 0;

        filasResultado.forEach(function (fila) {
            const clave = fila.dataset.clave;
            const entrada = fila.querySelector(".precio-personal");
            const cantidad = parseFloat(fila.dataset.cantidad) || 0;
            const unitario = entrada ? (parseFloat(entrada.value) || 0) : (parseFloat(fila.dataset.unitario) || 0);
            const subtotal = Math.round(cantidad * unitario);

            fila.dataset.unitario = unitario;
            fila.dataset.subtotal = subtotal;
            subtotales.push(subtotal);
            costoDirecto += subtotal;

            const celda = fila.querySelector(".celda-subtotal");
            if (celda) {
                celda.textContent = dinero(subtotal);
            }
        });

        costoDirecto = Math.round(costoDirecto);
        const indirectos = valor("indirectos");
        const montoIndirectos = Math.round((costoDirecto * indirectos) / 100);
        const costoTotal = Math.round(costoDirecto + montoIndirectos);
        const superficie = superficieCancha();
        const costoM2 = superficie > 0 ? Math.round(costoTotal / superficie) : 0;

        const mayor = Math.max.apply(null, subtotales.concat([1]));

        filasResultado.forEach(function (fila, indice) {
            const barra = fila.querySelector(".barra-partida");
            if (barra) {
                barra.style.width = ((subtotales[indice] / mayor) * 100).toFixed(1) + "%";
            }
        });

        if (costoDirectoCelda) {
            costoDirectoCelda.textContent = dinero(costoDirecto);
        }
        if (montoIndirectosCelda) {
            montoIndirectosCelda.textContent = dinero(montoIndirectos);
        }
        if (totalDetalle) {
            totalDetalle.textContent = dinero(costoTotal);
        }
        if (totalGeneral) {
            totalGeneral.textContent = dinero(costoTotal);
        }
        if (costoM2Celda) {
            costoM2Celda.textContent = dinero(costoM2);
        }
    }

    function aplicarPreciosGuardados() {
        inputsPrecio.forEach(function (entrada) {
            const clave = entrada.dataset.clave;
            const catalogo = entrada.dataset.catalogo;
            if (Object.prototype.hasOwnProperty.call(preciosEditados, clave)) {
                entrada.value = preciosEditados[clave];
            } else {
                entrada.value = catalogo;
            }
            entrada.classList.toggle("precio-modificado", Object.prototype.hasOwnProperty.call(preciosEditados, clave));
        });
        marcarEstadoPersonalizado();
        persistirPrecios();
        recalcularPrecios();
    }

    inputsPrecio.forEach(function (entrada) {
        entrada.addEventListener("input", function () {
            const clave = entrada.dataset.clave;
            const catalogo = parseFloat(entrada.dataset.catalogo);
            const escrito = parseFloat(entrada.value);
            const valorFinal = isNaN(escrito) ? 0 : escrito;

            if (!isNaN(catalogo) && Math.abs(valorFinal - catalogo) < 0.0001) {
                delete preciosEditados[clave];
                entrada.classList.remove("precio-modificado");
            } else {
                preciosEditados[clave] = valorFinal;
                entrada.classList.add("precio-modificado");
            }

            marcarEstadoPersonalizado();
            persistirPrecios();
            recalcularPrecios();
        });
    });

    if (botonRestablecer) {
        botonRestablecer.addEventListener("click", function () {
            Object.keys(preciosEditados).forEach(function (clave) {
                delete preciosEditados[clave];
            });
            aplicarPreciosGuardados();
        });
    }

    function actualizarMetricas() {
        const largo = valor("largo");
        const ancho = valor("ancho");
        const canchas = Math.max(valor("num_canchas"), 1);
        const espesor = valor("espesor_losa");

        const superficie = largo * ancho * canchas;
        const perim = 2 * (largo + ancho) * canchas;

        if (area) {
            area.textContent = formato(superficie, 0);
        }
        if (perimetro) {
            perimetro.textContent = formato(perim, 0);
        }
        if (volumen) {
            volumen.textContent = formato(superficie * espesor, 1);
        }

        recalcularPrecios();
    }

    if (botonTodos) {
        botonTodos.addEventListener("click", function () {
            checks.forEach(function (check) {
                check.checked = true;
            });
        });
    }

    if (botonNinguno) {
        botonNinguno.addEventListener("click", function () {
            checks.forEach(function (check) {
                check.checked = false;
            });
        });
    }

    if (botonDescargar) {
        botonDescargar.addEventListener("click", function () {
            const personalizado = Object.keys(preciosEditados).length > 0;
            const filas = [["Componente", "Material", "Cantidad", "Unidad", "Precio unitario", "Subtotal"]];

            document.querySelectorAll("#panel-resultado tbody tr[data-componente]").forEach(function (fila) {
                filas.push([
                    fila.dataset.componente,
                    fila.dataset.material,
                    fila.dataset.cantidad,
                    fila.dataset.unidad,
                    fila.dataset.unitario,
                    fila.dataset.subtotal,
                ]);
            });

            const total = document.getElementById("res-total");
            filas.push([]);
            filas.push(["Total estimado", total ? total.textContent.trim() : "Presupuesto preliminar"]);

            if (personalizado) {
                filas.push(["Origen de los precios", "Personalizado (editado en esta pantalla)"]);
            }

            if (costoDirectoCelda && montoIndirectosCelda) {
                filas.push(["Costo directo", costoDirectoCelda.textContent.trim()]);
                filas.push(["Gastos indirectos", montoIndirectosCelda.textContent.trim()]);
            }

            const csv = filas
                .map(function (fila) {
                    return fila
                        .map(function (celda) {
                            return '"' + String(celda).replace(/"/g, '""') + '"';
                        })
                        .join(";");
                })
                .join("\n");

            const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
            const url = URL.createObjectURL(blob);
            const enlace = document.createElement("a");
            enlace.href = url;
            enlace.download = "presupuesto-polideportivo.csv";
            document.body.appendChild(enlace);
            enlace.click();
            document.body.removeChild(enlace);
            URL.revokeObjectURL(url);
        });
    }

    formulario.addEventListener("submit", function (evento) {
        const seleccion = checks.filter(function (check) {
            return check.checked;
        });
        if (seleccion.length === 0) {
            evento.preventDefault();
            window.alert("Selecciona al menos un componente para realizar la estimación.");
        }
    });

    campos.forEach(function (campo) {
        campo.addEventListener("input", actualizarMetricas);
    });
    checks.forEach(function (check) {
        check.addEventListener("change", actualizarMetricas);
    });

    cargarPreciosGuardados();
    actualizarMetricas();
    aplicarPreciosGuardados();
})();