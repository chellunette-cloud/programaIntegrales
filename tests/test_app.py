# -*- coding: utf-8 -*-
"""Prueba de la interfaz Streamlit con AppTest (runtime simulado)."""
from __future__ import annotations

import os
import sys
from streamlit.testing.v1 import AppTest

_RUTA_APP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    pass


def _sin_excepcion(at, etiqueta):
    if at.exception:
        for e in at.exception:
            print("EXCEPCION en", etiqueta, ":", e.value)
        raise SystemExit(1)
    print("[OK] sin excepciones:", etiqueta)


def main():
    at = AppTest.from_file(_RUTA_APP, default_timeout=90)
    at.run()
    _sin_excepcion(at, "carga inicial")
    print("   botones:", [b.label for b in at.button])

    # Escribir un ejercicio y resolver.
    at.text_area[0].set_value(r"\int_0^1\int_0^{\sqrt{1-x^2}}(x^2+y^2)\,dy\,dx")
    # Pulsar "Resolver".
    for b in at.button:
        if "Resolver" in b.label:
            b.click()
            break
    at.run()
    _sin_excepcion(at, "resolver integral doble")
    print("   nº de tabs:", len(at.tabs))

    # Verificar que aparece el resultado (π/8 ≈ 0.3927) en algún metric/markdown.
    textos = " ".join(m.value for m in at.markdown)
    assert "0.3927" in textos or "0.392699" in textos, "No se encontró el resultado esperado"
    print("[OK] resultado mostrado en la interfaz")

    # Cargar un ejemplo de error (límites ambiguos).
    at.text_area[0].set_value(r"\int_0^1 (x+y)")
    for b in at.button:
        if "Resolver" in b.label:
            b.click()
            break
    at.run()
    _sin_excepcion(at, "entrada ambigua (debe avisar, no romper)")
    cuerpo = " ".join(m.value for m in at.markdown)
    assert "No se pudo resolver" in cuerpo or "diferencial" in cuerpo
    print("[OK] control de errores en la interfaz")

    # --- Modo: conversión a polares -------------------------------------
    at.sidebar.radio[0].set_value("🔄 Convertir a coordenadas polares")
    at.run()
    for b in at.button:
        if "Convertir y resolver" in b.label:
            b.click()
            break
    at.run()
    _sin_excepcion(at, "modo conversión a polares")
    cuerpo = " ".join(m.value for m in at.markdown)
    assert "polares" in cuerpo.lower() or "θ" in cuerpo
    print("[OK] modo conversión a polares")

    # --- Modo: volumen de un sólido -------------------------------------
    at.sidebar.radio[0].set_value("🧊 Volumen de un sólido")
    at.run()
    for b in at.button:
        if "Calcular volumen" in b.label:
            b.click()
            break
    at.run()
    _sin_excepcion(at, "modo volumen de esfera")
    textos = " ".join(m.value for m in at.markdown) + " ".join(
        m.value for m in at.metric if m.value
    )
    print("[OK] modo volumen de un sólido")

    # --- Modo: volumen entre dos superficies ----------------------------
    at.selectbox[0].set_value("entre_superficies")
    at.run()
    for b in at.button:
        if "Calcular volumen" in b.label:
            b.click()
            break
    at.run()
    _sin_excepcion(at, "modo volumen entre superficies")
    textos = " ".join(m.value for m in at.markdown) + " ".join(
        m.value for m in at.metric if m.value
    )
    assert "3.3333" in textos or "10/3" in textos, "No apareció el volumen 10/3"
    print("[OK] modo volumen entre superficies (10/3)")

    print("\nTodas las comprobaciones de interfaz correctas.")


if __name__ == "__main__":
    main()
