# -*- coding: utf-8 -*-
"""Pruebas automáticas del motor matemático.

Se pueden ejecutar de dos formas:

    python tests/test_motor.py        # ejecución directa
    pytest tests/test_motor.py        # con pytest (si está instalado)

Comparan los resultados con valores conocidos y con integración numérica
independiente (SciPy). Algunas pruebas tardan unos segundos.
"""
from __future__ import annotations

import io
import os
import sys

# Permite ejecutar el archivo directamente desde la carpeta tests/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sympy as sp

from motor import ErrorEntrada, parsear_ejercicio, resolver
from motor.graficas import figura_region_2d, figura_solido_3d
from motor.reportes import generar_pdf, procedimiento_texto
from motor.volumenes import (
    solido_cilindro,
    solido_cono,
    solido_entre_superficies,
    solido_esfera,
    solido_paraboloide,
)

TOL = 1e-6


def _resolver(texto):
    return resolver(parsear_ejercicio(texto), timeout=40.0)


# --------------------------------------------------------------------------
# 1. Integral doble sobre región rectangular
# --------------------------------------------------------------------------
def test_doble_rectangular():
    sol = _resolver(r"\int_0^2\int_0^1 (x+y)\,dy\,dx")
    assert sol.exacto
    assert abs(float(sol.resultado) - 3.0) < TOL, sol.resultado


# --------------------------------------------------------------------------
# 2. Integral doble sobre un semicírculo / cuarto de disco
# --------------------------------------------------------------------------
def test_doble_semicirculo():
    sol = _resolver(r"\int_0^1\int_0^{\sqrt{1-x^2}}(x^2+y^2)\,dy\,dx")
    assert abs(float(sol.resultado) - sp.pi / 8) < TOL, sol.resultado
    assert sol.verificacion.get("coincide") is True


# --------------------------------------------------------------------------
# 3. Transformada a coordenadas polares
# --------------------------------------------------------------------------
def test_polares():
    sol = _resolver(r"\int_0^{2\pi}\int_0^1 e^{r^2} r\,dr\,d\theta")
    esperado = sp.pi * (sp.E - 1)
    assert abs(float(sol.resultado) - float(esperado)) < TOL, sol.resultado
    assert sol.especificacion.sistema == "polar"


# --------------------------------------------------------------------------
# 4. Integral con función exponencial
# --------------------------------------------------------------------------
def test_exponencial():
    sol = _resolver(r"\int_0^1\int_0^1 e^{x+y}\,dy\,dx")
    esperado = (sp.E - 1) ** 2
    assert abs(float(sol.resultado) - float(esperado)) < 1e-6, sol.resultado


# --------------------------------------------------------------------------
# 5. Integral triple sobre una región sencilla (cubo unitario)
# --------------------------------------------------------------------------
def test_triple_cubo():
    sol = _resolver(r"\int_0^1\int_0^1\int_0^1 xyz\,dz\,dy\,dx")
    assert abs(float(sol.resultado) - 1 / 8) < TOL, sol.resultado


# --------------------------------------------------------------------------
# 6. Volumen de una esfera
# --------------------------------------------------------------------------
def test_volumen_esfera():
    sol = _resolver(
        r"\int_0^{5}\int_0^{2\pi}\int_0^{\pi}\rho^2\sin\phi\,d\phi\,d\theta\,d\rho"
    )
    assert abs(float(sol.resultado) - 500 * sp.pi / 3) < 1e-6, sol.resultado


def test_volumen_solidos_predefinidos():
    esfera = resolver(solido_esfera(3))
    assert abs(esfera.resultado_decimal - 4 / 3 * sp.pi * 27) < 1e-6
    cil = resolver(solido_cilindro(2, 3))
    assert abs(cil.resultado_decimal - sp.pi * 4 * 3) < 1e-6
    cono = resolver(solido_cono(2, 4))
    assert abs(cono.resultado_decimal - sp.pi * 4 * 4 / 3) < 1e-6
    par = resolver(solido_paraboloide(4))
    assert abs(par.resultado_decimal - sp.pi * 16 / 2) < 1e-6


def test_volumen_entre_superficies():
    # Volumen bajo z = 4 − x² − y² sobre [0,1]²: ∫₀¹∫₀¹ (4 − x² − y²) dy dx = 10/3.
    spec = solido_entre_superficies("4 - x^2 - y^2", "0", "0", "1", "0", "1")
    sol = resolver(spec)
    assert sol.exacto
    assert abs(float(sol.resultado) - sp.Rational(10, 3)) < TOL, sol.resultado
    assert sol.verificacion.get("coincide") is True
    # El sólido debe poder dibujarse en 3D (antes fallaba por desajuste de símbolos).
    assert figura_solido_3d(spec) is not None


# --------------------------------------------------------------------------
# 7. Integral sin antiderivada elemental (función especial)
# --------------------------------------------------------------------------
def test_funcion_especial():
    sol = _resolver(r"\int_0^1 e^{x^2}\,dx")
    assert sol.exacto, "Debe resolverse simbólicamente con erfi"
    assert sol.usa_funciones_especiales
    assert abs(sol.resultado_decimal - 1.4626517459) < 1e-6
    # Debe advertirse que no es elemental.
    assert any("especial" in a.lower() for a in sol.advertencias)


# --------------------------------------------------------------------------
# 8. Errores y limites inválidos o ambiguos
# --------------------------------------------------------------------------
def test_entrada_incompleta():
    for malo in [
        r"\int_0^1 \int_0^1 (x+y)",
        r"\int_0^1 (x+y)",
        "",
        r"\int_0^{1}\int_0^{x}(x+y)\,dx\,dy",  # orden incoherente
    ]:
        try:
            parsear_ejercicio(malo)
            raise AssertionError(f"Debió fallar: {malo!r}")
        except ErrorEntrada:
            pass


# --------------------------------------------------------------------------
# 9. Área mediante integral doble
# --------------------------------------------------------------------------
def test_area():
    sol = _resolver(r"\int_0^{1}\int_{0}^{1-x} dy\,dx")
    assert abs(float(sol.resultado) - 0.5) < TOL, sol.resultado


# --------------------------------------------------------------------------
# 10. Verificación numérica coincide con el valor simbólico
# --------------------------------------------------------------------------
def test_verificacion_numerica():
    sol = _resolver(r"\int_0^{\pi/2}\int_0^1 r^2\,dr\,d\theta")
    assert sol.verificacion.get("coincide") is True
    assert sol.verificacion.get("diferencia") is not None
    assert sol.verificacion["diferencia"] < 1e-6


# --------------------------------------------------------------------------
# 11. Gráficas y PDF
# --------------------------------------------------------------------------
def test_graficas_y_pdf():
    sol = _resolver(r"\int_0^1\int_0^{\sqrt{1-x^2}}(x^2+y^2)\,dy\,dx")
    fig2d = figura_region_2d(sol.especificacion)
    assert fig2d is not None

    sol_esf = resolver(solido_esfera(2))
    fig3d = figura_solido_3d(sol_esf.especificacion)
    assert fig3d is not None

    texto = procedimiento_texto(sol)
    assert "RESULTADO EXACTO" in texto

    pdf = generar_pdf(sol, [fig2d])
    assert pdf[:4] == b"%PDF", "El PDF debe comenzar con %PDF"


# --------------------------------------------------------------------------
# 12. Radicales y funciones trigonométricas
# --------------------------------------------------------------------------
def test_radicales_trigonometricas():
    sol = _resolver(r"\int_0^{\pi/2}\int_0^1 \sqrt{1-r^2}\,r\,dr\,d\theta")
    # ∫0^1 sqrt(1-r^2) r dr = 1/3 ; por θ => π/6
    assert abs(float(sol.resultado) - sp.pi / 6) < 1e-6, sol.resultado


# --------------------------------------------------------------------------
# Ejecución directa
# --------------------------------------------------------------------------
def _main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    pruebas = [
        (n, f) for n, f in sorted(globals().items())
        if n.startswith("test_") and callable(f)
    ]
    fallos = 0
    for nombre, fn in pruebas:
        try:
            fn()
            print(f"[OK]   {nombre}")
        except Exception as exc:  # noqa: BLE001
            fallos += 1
            print(f"[FALLA] {nombre}: {exc}")
    print("-" * 50)
    print(f"{len(pruebas) - fallos}/{len(pruebas)} pruebas correctas")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(_main())
