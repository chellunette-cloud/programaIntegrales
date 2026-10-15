# -*- coding: utf-8 -*-
"""Resolutor de Integrales Múltiples — Cálculo Integral Multivariable.

Aplicación interactiva (Streamlit) para resolver integrales dobles y triples,
cambios a coordenadas polares/cilíndricas/esféricas y cálculo de áreas y
volúmenes, mostrando el procedimiento completo paso a paso.

Ejecutar con:  streamlit run app.py
"""
from __future__ import annotations

import sympy as sp
import streamlit as st

from motor import ErrorEntrada, parsear_ejercicio, resolver
from motor.coordenadas import convertir_a_polares
from motor.ejemplos import EJEMPLOS, ejemplo_por_titulo, lista_titulos
from motor.graficas import figura_region_2d, figura_solido_3d
from motor.latex_utils import a_unicode, representar_integral
from motor.reportes import generar_pdf, procedimiento_texto
from motor.volumenes import (
    solido_cilindro,
    solido_cono,
    solido_esfera,
    solido_entre_superficies,
    solido_paraboloide,
)

# --------------------------------------------------------------------------
# Configuración de la página
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Resolutor de Integrales Múltiples",
    page_icon="∫",
    layout="wide",
)

st.markdown(
    """
    <style>
    .titulo-app { font-size: 2.0rem; font-weight: 800; color: #1f3b73; }
    .subtitulo-app { color: #555; margin-top: -0.6rem; }
    .resultado-final {
        background: #eef6ee; border-left: 6px solid #2e8b57;
        padding: 0.7rem 1rem; border-radius: 6px;
    }
    .aviso {
        background: #fff6e5; border-left: 6px solid #e6a700;
        padding: 0.6rem 1rem; border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Estado de sesión
# --------------------------------------------------------------------------
def _init_estado():
    if "texto" not in st.session_state:
        st.session_state.texto = EJEMPLOS[1]["texto"]
    if "paquete" not in st.session_state:
        st.session_state.paquete = None
    if "error" not in st.session_state:
        st.session_state.error = None
    if "ocr_resultado" not in st.session_state:
        st.session_state.ocr_resultado = ""


_init_estado()


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def construir_paquete(spec, pasos_extra=None, timeout=30.0):
    """Resuelve la especificación y prepara gráficas, texto y PDF."""
    sol = resolver(spec, timeout=timeout)
    if pasos_extra:
        sol.pasos = list(pasos_extra) + list(sol.pasos)

    fig2d = fig3d = None
    try:
        fig2d = figura_region_2d(spec)
    except Exception:  # noqa: BLE001
        fig2d = None
    try:
        fig3d = figura_solido_3d(spec)
    except Exception:  # noqa: BLE001
        fig3d = None

    figuras = [f for f in (fig2d, fig3d) if f is not None]
    texto = procedimiento_texto(sol)
    try:
        pdf = generar_pdf(sol, figuras)
        error_pdf = None
    except Exception as exc:  # noqa: BLE001
        pdf = None
        error_pdf = str(exc)

    return {
        "sol": sol,
        "fig2d": fig2d,
        "fig3d": fig3d,
        "texto": texto,
        "pdf": pdf,
        "error_pdf": error_pdf,
        "spec": spec,
    }


def ejecutar_texto(texto):
    try:
        spec = parsear_ejercicio(texto)
    except ErrorEntrada as exc:
        st.session_state.error = str(exc)
        st.session_state.paquete = None
        return
    except Exception as exc:  # noqa: BLE001
        st.session_state.error = f"Error inesperado al interpretar el ejercicio: {exc}"
        st.session_state.paquete = None
        return
    try:
        st.session_state.paquete = construir_paquete(spec)
        st.session_state.error = None
    except Exception as exc:  # noqa: BLE001
        st.session_state.error = f"Error al resolver: {exc}"
        st.session_state.paquete = None


# --------------------------------------------------------------------------
# Barra lateral
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    modo = st.radio(
        "Tipo de ejercicio",
        [
            "🤖 Detección automática",
            "🔄 Convertir a coordenadas polares",
            "🧊 Volumen de un sólido",
        ],
        help="El sistema intenta reconocer el tipo automáticamente, pero puedes "
        "elegir un modo específico.",
    )
    detalle = st.toggle("Mostrar procedimiento con mayor detalle", value=True)
    st.divider()
    st.markdown("### 📚 Ejemplos de práctica")
    titulo_ej = st.selectbox("Cargar un ejemplo", ["— elegir —"] + lista_titulos())
    if titulo_ej != "— elegir —":
        if st.button("Cargar ejemplo", use_container_width=True):
            st.session_state.texto = ejemplo_por_titulo(titulo_ej)["texto"]
            st.session_state.paquete = None
            st.session_state.error = None
            st.rerun()

    st.divider()
    with st.expander("📷 Reconocer desde una foto (OCR)"):
        archivo = st.file_uploader(
            "Sube una imagen del ejercicio", type=["png", "jpg", "jpeg", "webp", "bmp"]
        )
        if archivo is not None:
            try:
                import pytesseract
                from PIL import Image

                imagen = Image.open(archivo)
                st.image(imagen, caption="Imagen cargada", use_container_width=True)
                if st.button("Reconocer texto", use_container_width=True):
                    try:
                        txt = pytesseract.image_to_string(imagen)
                        st.session_state.ocr_resultado = txt.strip()
                    except Exception as exc:  # noqa: BLE001
                        st.error(
                            "No se pudo ejecutar el OCR. Comprueba que Tesseract "
                            f"está instalado y en el PATH. Detalle: {exc}"
                        )
                if st.session_state.ocr_resultado:
                    st.text_area(
                        "Texto reconocido (revisa y corrige antes de resolver)",
                        key="ocr_resultado",
                        height=120,
                    )
                    if st.button("Usar este texto", use_container_width=True):
                        st.session_state.texto = st.session_state.ocr_resultado
                        st.session_state.paquete = None
                        st.rerun()
            except ImportError:
                st.warning(
                    "El OCR opcional no está instalado. Para activarlo:\n\n"
                    "1. Instala Tesseract-OCR en el sistema.\n"
                    "2. `pip install pytesseract pillow`\n\n"
                    "Para ecuaciones escritas a mano existen mejores resultados "
                    "con herramientas como **pix2tex (LaTeX-OCR)**; puedes pegar el "
                    "resultado corregido en el campo de texto."
                )
    st.divider()
    st.caption(
        "Motor simbólico: SymPy · Verificación numérica: SciPy · "
        "Gráficas: Matplotlib · Interfaz: Streamlit"
    )


# --------------------------------------------------------------------------
# Encabezado
# --------------------------------------------------------------------------
st.markdown('<div class="titulo-app">∫ Resolutor de Integrales Múltiples</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitulo-app">Integrales dobles y triples · coordenadas polares, '
    'cilíndricas y esféricas · áreas y volúmenes · solución paso a paso</div>',
    unsafe_allow_html=True,
)
st.write("")


# --------------------------------------------------------------------------
# Modo: detección automática / texto libre
# --------------------------------------------------------------------------
if modo == "🤖 Detección automática":
    st.markdown("**Escribe o pega el ejercicio** (acepta notación LaTeX o texto plano).")
    st.text_area(
        "Ejercicio",
        key="texto",
        height=110,
        label_visibility="collapsed",
        placeholder=r"Ej.: \int_0^1\int_0^{\sqrt{1-x^2}}(x^2+y^2)\,dy\,dx",
    )
    c1, c2, _ = st.columns([1, 1, 4])
    resolver_click = c1.button("▶ Resolver", type="primary", use_container_width=True)
    limpiar_click = c2.button("🧹 Limpiar", use_container_width=True)

    if limpiar_click:
        st.session_state.texto = ""
        st.session_state.paquete = None
        st.session_state.error = None
        st.rerun()
    if resolver_click:
        ejecutar_texto(st.session_state.texto)

# --------------------------------------------------------------------------
# Modo: conversión a polares
# --------------------------------------------------------------------------
elif modo == "🔄 Convertir a coordenadas polares":
    st.markdown("**Convierte una integral doble cartesiana a coordenadas polares.**")
    col1, col2 = st.columns([2, 1])
    with col1:
        integrando_txt = st.text_input(
            "Integrando f(x, y)", value="x^2+y^2",
            help="Escribe solo el integrando, por ejemplo x^2+y^2, x*y, e^{-(x^2+y^2)}…",
        )
    with col2:
        region = st.selectbox(
            "Región de integración",
            [
                "disco",
                "semicirculo_superior",
                "semicirculo_inferior",
                "cuarto_circulo",
                "corona",
                "cardioide",
                "rosa_4",
            ],
            format_func=lambda s: {
                "disco": "Disco (círculo completo)",
                "semicirculo_superior": "Semicírculo superior",
                "semicirculo_inferior": "Semicírculo inferior",
                "cuarto_circulo": "Cuarto de círculo (1.er cuadrante)",
                "corona": "Corona circular",
                "cardioide": "Cardioide r = a(1+cos θ)",
                "rosa_4": "Rosa de 4 pétalos r = a·cos 2θ",
            }[s],
        )
    col3, col4 = st.columns(2)
    a = col3.text_input("Parámetro a (radio interior)", value="1")
    b = col4.text_input("Parámetro b (radio exterior, solo corona)", value="2")

    if st.button("▶ Convertir y resolver", type="primary"):
        try:
            from motor.latex_utils import parsear

            f = parsear(integrando_txt, ["x", "y"])
            spec, pasos_conv = convertir_a_polares(f, region, a, b)
            st.session_state.paquete = construir_paquete(spec, pasos_extra=pasos_conv)
            st.session_state.error = None
        except Exception as exc:  # noqa: BLE001
            st.session_state.error = f"No se pudo preparar la conversión: {exc}"
            st.session_state.paquete = None

# --------------------------------------------------------------------------
# Modo: volumen de un sólido
# --------------------------------------------------------------------------
else:
    st.markdown("**Cálculo de volúmenes de sólidos predefinidos.**")
    tipo_solido = st.selectbox(
        "Sólido",
        ["esfera", "cilindro", "cono", "paraboloide", "entre_superficies"],
        format_func=lambda s: {
            "esfera": "Esfera de radio a",
            "cilindro": "Cilindro de radio a y altura h",
            "cono": "Cono de radio a y altura h",
            "paraboloide": "Paraboloide z = x² + y² hasta z = h",
            "entre_superficies": "Volumen entre dos superficies (integral doble)",
        }[s],
    )
    spec = None
    if tipo_solido == "esfera":
        a = st.text_input("Radio a", value="5")
        if st.button("▶ Calcular volumen", type="primary"):
            spec = solido_esfera(a)
    elif tipo_solido == "cilindro":
        c1, c2 = st.columns(2)
        a = c1.text_input("Radio a", value="2")
        h = c2.text_input("Altura h", value="3")
        if st.button("▶ Calcular volumen", type="primary"):
            spec = solido_cilindro(a, h)
    elif tipo_solido == "cono":
        c1, c2 = st.columns(2)
        a = c1.text_input("Radio a", value="2")
        h = c2.text_input("Altura h", value="4")
        if st.button("▶ Calcular volumen", type="primary"):
            spec = solido_cono(a, h)
    elif tipo_solido == "paraboloide":
        h = st.text_input("Altura h (plano z = h)", value="4")
        if st.button("▶ Calcular volumen", type="primary"):
            spec = solido_paraboloide(h)
    else:
        st.caption("Superficie superior z = f(x,y) menos superficie inferior z = g(x,y).")
        c1, c2 = st.columns(2)
        sup = c1.text_input("Superficie superior z =", value="4 - x^2 - y^2")
        inf = c2.text_input("Superficie inferior z =", value="0")
        c3, c4 = st.columns(2)
        xa = c3.text_input("x desde", value="0")
        xb = c4.text_input("x hasta", value="1")
        c5, c6 = st.columns(2)
        ya = c5.text_input("y desde", value="0")
        yb = c6.text_input("y hasta", value="1")
        if st.button("▶ Calcular volumen", type="primary"):
            spec = solido_entre_superficies(sup, inf, xa, xb, ya, yb)

    if spec is not None:
        try:
            st.session_state.paquete = construir_paquete(spec)
            st.session_state.error = None
        except Exception as exc:  # noqa: BLE001
            st.session_state.error = f"Error al resolver el volumen: {exc}"
            st.session_state.paquete = None


# --------------------------------------------------------------------------
# Mensajes de error
# --------------------------------------------------------------------------
if st.session_state.error:
    st.markdown(
        f'<div class="aviso">⚠️ <b>No se pudo resolver:</b><br>{st.session_state.error}</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Resultados
# --------------------------------------------------------------------------
paquete = st.session_state.paquete
if paquete:
    sol = paquete["sol"]
    spec = paquete["spec"]

    st.divider()
    tabs = st.tabs(
        [
            "📝 Procedimiento",
            "🎯 Resultado",
            "📐 Fórmulas",
            "📊 Región (2D)",
            "🧊 Sólido (3D)",
            "✅ Verificación",
            "⬇️ Exportar",
        ]
    )

    # ----- Procedimiento ------------------------------------------------
    with tabs[0]:
        for paso in sol.pasos:
            if not detalle and paso.tipo in ("integral",) and "Antiderivada" in paso.titulo:
                continue
            st.markdown(f"#### {paso.titulo}")
            if paso.explicacion:
                st.markdown(paso.explicacion)
            for latex, _texto in paso.formulas:
                if latex:
                    try:
                        st.latex(latex)
                    except Exception:  # noqa: BLE001
                        st.code(_texto or latex)
                elif _texto:
                    st.code(_texto)
            st.write("")
        if sol.advertencias:
            for adv in sol.advertencias:
                st.warning(adv)

    # ----- Resultado ----------------------------------------------------
    with tabs[1]:
        st.markdown("### Resultado final")
        if sol.resultado is not None:
            try:
                st.latex(sp.latex(sol.resultado))
            except Exception:  # noqa: BLE001
                st.code(a_unicode(sol.resultado))
        if sol.resultado_decimal is not None:
            etiqueta = "Valor numérico" if sol.exacto else "Valor aproximado (numérico)"
            st.markdown(
                f'<div class="resultado-final"><b>{etiqueta}:</b> '
                f'{sol.resultado_decimal:.10g}</div>',
                unsafe_allow_html=True,
            )
        st.write("")
        st.info("**Método:** " + sol.metodo)
        if not sol.exacto:
            st.error(
                "El resultado presentado es una aproximación numérica; no debe "
                "considerarse un valor exacto."
            )
        if sol.usa_funciones_especiales:
            st.warning(
                "El resultado involucra una función especial (no elemental). Es un "
                "valor exacto en términos de dicha función, no una aproximación."
            )

    # ----- Fórmulas -----------------------------------------------------
    with tabs[2]:
        st.markdown("### Fórmulas y elementos diferenciales utilizados")
        for f in sol.formulas_empleadas:
            st.markdown(f"**{f['titulo']}**")
            try:
                st.latex(f["latex"])
            except Exception:  # noqa: BLE001
                st.code(f["texto"])
        if sol.especificacion.sistema == "polar":
            st.markdown("---")
            st.markdown("**Recordatorio (jacobiano):** al pasar a polares, "
                        "`dA = r dr dθ`; el factor `r` proviene del determinante "
                        "jacobiano de la transformación.")

    # ----- Región 2D ----------------------------------------------------
    with tabs[3]:
        if paquete["fig2d"] is not None:
            st.pyplot(paquete["fig2d"])
            st.caption("Región de integración aproximada.")
        else:
            st.info(
                "No hay una región bidimensional que graficar para este ejercicio "
                "(por ejemplo, una integral triple o una región no determinable)."
            )

    # ----- Sólido 3D ----------------------------------------------------
    with tabs[4]:
        if paquete["fig3d"] is not None:
            st.pyplot(paquete["fig3d"])
            st.caption("Representación aproximada del sólido.")
        else:
            st.info(
                "No se generó una representación tridimensional para este ejercicio. "
                "Usa el modo «Volumen de un sólido» para ver el dibujo del sólido."
            )

    # ----- Verificación -------------------------------------------------
    with tabs[5]:
        st.markdown("### Verificación independiente")
        v = sol.verificacion
        col1, col2 = st.columns(2)
        if sol.resultado_decimal is not None:
            col1.metric("Resultado simbólico / mostrado", f"{sol.resultado_decimal:.10g}")
        if v.get("numerico") is not None:
            col2.metric("Integración numérica (SciPy)", f"{v['numerico']:.10g}")
        if v.get("diferencia") is not None:
            st.write(f"Diferencia absoluta: **{v['diferencia']:.3e}**")
        if v.get("coincide") is True:
            st.success("✔ " + (v.get("mensaje") or "Los valores coinciden."))
        elif v.get("coincide") is False:
            st.warning("⚠ " + (v.get("mensaje") or "Los valores no coinciden plenamente."))
        else:
            st.info(v.get("mensaje") or "No fue posible verificar numéricamente.")

    # ----- Exportar -----------------------------------------------------
    with tabs[6]:
        st.markdown("### Copiar y descargar")
        st.markdown("**Procedimiento completo (texto):**")
        st.code(paquete["texto"], language="text")
        st.markdown("**Expandir con notación matemática:**")
        with st.expander("Ver el LaTeX del resultado"):
            if sol.resultado is not None:
                st.code(sp.latex(sol.resultado), language="latex")

        d1, d2 = st.columns(2)
        if paquete["pdf"] is not None:
            d1.download_button(
                "📄 Descargar solución en PDF",
                data=paquete["pdf"],
                file_name="solucion_paso_a_paso.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            d1.warning("No se pudo generar el PDF: " + str(paquete.get("error_pdf")))
        d2.download_button(
            "📝 Descargar procedimiento (TXT)",
            data=paquete["texto"].encode("utf-8"),
            file_name="procedimiento.txt",
            mime="text/plain",
            use_container_width=True,
        )

else:
    st.info(
        "Escribe un ejercicio y pulsa **Resolver**, o carga un ejemplo desde la "
        "barra lateral para comenzar."
    )
