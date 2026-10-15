# -*- coding: utf-8 -*-
"""Generación del procedimiento en texto y exportación a PDF."""
from __future__ import annotations

import io
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import mathtext  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from .latex_utils import a_unicode, latex_limpio, representar_integral  # noqa: E402


# --------------------------------------------------------------------------
# Texto plano (para copiar y pegar / transcribir)
# --------------------------------------------------------------------------
def procedimiento_texto(sol) -> str:
    lineas = []
    lineas.append("=" * 68)
    lineas.append("SOLUCIÓN PASO A PASO"
                  )
    lineas.append("=" * 68)
    lineas.append("")
    for paso in sol.pasos:
        lineas.append(paso.titulo)
        lineas.append("-" * len(paso.titulo))
        if paso.explicacion:
            for l in paso.explicacion.split("\n"):
                lineas.extend(textwrap.wrap(l, 88) or [""])
        for _, texto in paso.formulas:
            if texto:
                lineas.append("    " + texto)
        lineas.append("")

    lineas.append("=" * 68)
    if sol.resultado is not None:
        lineas.append("RESULTADO EXACTO:  " + a_unicode(sol.resultado))
    if sol.resultado_decimal is not None:
        lineas.append("APROXIMACIÓN:      ≈ " + f"{sol.resultado_decimal:.10g}")
    lineas.append("MÉTODO:            " + sol.metodo)
    if sol.advertencias:
        lineas.append("")
        lineas.append("Advertencias:")
        for a in sol.advertencias:
            lineas.extend(textwrap.wrap("  • " + a, 88))
    lineas.append("=" * 68)
    return "\n".join(lineas)


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
def _latex_valido(tex: str) -> bool:
    try:
        mathtext.MathTextParser("agg").parse("$" + latex_limpio(tex) + "$")
        return True
    except Exception:  # noqa: BLE001
        return False


def _bloques(sol):
    """Convierte la solución en una lista de bloques de contenido."""
    bloques = []
    bloques.append(("titulo", "Solución paso a paso"))
    lat, _ = representar_integral(sol.especificacion.capas, sol.especificacion.integrando)
    bloques.append(("formula", (lat, None)))
    bloques.append(("texto", sol.especificacion.texto_original))
    bloques.append(("sep", None))
    for paso in sol.pasos:
        bloques.append(("subtitulo", paso.titulo))
        if paso.explicacion:
            bloques.append(("texto", paso.explicacion))
        for latex, texto in paso.formulas:
            if latex:
                bloques.append(("formula", (latex, texto)))
            elif texto:
                bloques.append(("texto", "    " + texto))
        bloques.append(("espacio", None))
    bloques.append(("sep", None))
    if sol.resultado is not None:
        bloques.append(("subtitulo", "Resultado final exacto"))
        bloques.append(("formula", (None, a_unicode(sol.resultado))))
    if sol.resultado_decimal is not None:
        bloques.append(("texto", f"Aproximación numérica: ≈ {sol.resultado_decimal:.10g}"))
    bloques.append(("texto", "Método: " + sol.metodo))
    return bloques


def generar_pdf(sol, figuras=None) -> bytes:
    """Genera un PDF con el procedimiento, la verificación y las gráficas."""
    figuras = figuras or []
    buffer = io.BytesIO()
    ancho, alto = 8.27, 11.69  # A4 en pulgadas
    margen = 0.85

    def nueva_pagina():
        fig = plt.figure(figsize=(ancho, alto), dpi=120)
        return fig, [alto - margen]  # y actual

    def guardar(pagina):
        if pagina is not None:
            pdf.savefig(pagina)
            plt.close(pagina)

    with PdfPages(buffer) as pdf:
        pagina, y = nueva_pagina()

        def salto(altura):
            nonlocal pagina, y
            if y[0] - altura < margen:
                guardar(pagina)
                pagina, y = nueva_pagina()
            y[0] -= altura
            return y[0]

        def escribe(txt, tam=10, negrita=False, cursiva=False, salto_linea=True):
            nonlocal pagina
            lineas = []
            ancho_car = max(40, int((ancho - 2 * margen) / (tam * 0.0092)))
            for parrafo in str(txt).split("\n"):
                lineas.extend(textwrap.wrap(parrafo, ancho_car) or [""])
            for lin in lineas:
                yy = salto(0.19 * tam / 10 + 0.02)
                pagina.text(
                    margen,
                    yy,
                    lin,
                    fontsize=tam,
                    fontweight="bold" if negrita else "normal",
                    fontstyle="italic" if cursiva else "normal",
                    va="top",
                )

        for tipo, contenido in _bloques(sol):
            if tipo == "titulo":
                salto(0.15)
                escribe(contenido, tam=18, negrita=True)
                salto(0.1)
            elif tipo == "subtitulo":
                salto(0.12)
                escribe(contenido, tam=12.5, negrita=True)
            elif tipo == "texto":
                escribe(contenido, tam=10)
            elif tipo == "sep":
                yy = salto(0.12)
                linea = Line2D(
                    [margen / ancho, 1 - margen / ancho],
                    [yy / alto, yy / alto],
                    transform=pagina.transFigure,
                    color="#999",
                    lw=0.8,
                )
                pagina.add_artist(linea)
            elif tipo == "espacio":
                salto(0.08)
            elif tipo == "formula":
                latex, texto = contenido
                altura = 0.62
                yy = salto(altura)
                texto_mostrar = latex_limpio(latex) if latex else None
                if texto_mostrar and _latex_valido(texto_mostrar):
                    pagina.text(
                        0.5,
                        yy + 0.06,
                        "$" + texto_mostrar + "$",
                        fontsize=14,
                        ha="center",
                        va="center",
                    )
                else:
                    pagina.text(
                        0.5,
                        yy + 0.06,
                        texto or (a_unicode(latex) if latex else ""),
                        fontsize=11,
                        ha="center",
                        va="center",
                    )
        guardar(pagina)

        for fig in figuras:
            try:
                pdf.savefig(fig)
            except Exception:  # noqa: BLE001
                pass
        d = pdf.infodict()
        d["Title"] = "Solución paso a paso — Cálculo Integral Multivariable"
        d["Author"] = "Resolutor de Integrales Múltiples"

    return buffer.getvalue()
