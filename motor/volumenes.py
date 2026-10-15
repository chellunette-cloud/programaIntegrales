# -*- coding: utf-8 -*-
"""Sólidos predefinidos para el cálculo de volúmenes.

Cada función devuelve una :class:`~motor.especificacion.Especificacion` lista
para resolver, junto con información para su representación en 3D.
"""
from __future__ import annotations

import sympy as sp

from .especificacion import Capa, Especificacion

x, y, z = sp.symbols("x y z", real=True)
r, theta = sp.symbols("r theta", real=True)
rho, phi = sp.symbols("rho phi", real=True)
pi = sp.pi


def solido_esfera(a=5):
    a = sp.sympify(a)
    spec = Especificacion(
        capas=[Capa(rho, 0, a), Capa(phi, 0, pi), Capa(theta, 0, 2 * pi)],
        integrando=rho**2 * sp.sin(phi),
        sistema="esferico",
        tipo_calculo="volumen",
        descripcion=f"Volumen de la esfera de radio {a} (x² + y² + z² = {a}²).",
        info_volumen={"grafico": {"tipo": "esfera", "a": a}, "nombre": "Esfera"},
    )
    return spec


def solido_cilindro(a=2, h=3):
    a, h = sp.sympify(a), sp.sympify(h)
    spec = Especificacion(
        capas=[Capa(theta, 0, 2 * pi), Capa(r, 0, a), Capa(z, 0, h)],
        integrando=r,
        sistema="cilindrico",
        tipo_calculo="volumen",
        descripcion=f"Volumen del cilindro de radio {a} y altura {h}.",
        info_volumen={"grafico": {"tipo": "cilindro", "a": a, "h": h}, "nombre": "Cilindro"},
    )
    return spec


def solido_cono(a=2, h=4):
    a, h = sp.sympify(a), sp.sympify(h)
    spec = Especificacion(
        capas=[Capa(theta, 0, 2 * pi), Capa(r, 0, a), Capa(z, 0, h * (1 - r / a))],
        integrando=r,
        sistema="cilindrico",
        tipo_calculo="volumen",
        descripcion=f"Volumen del cono de radio {a} y altura {h} (vértice en z = {h}).",
        info_volumen={"grafico": {"tipo": "cono", "a": a, "h": h}, "nombre": "Cono"},
    )
    return spec


def solido_paraboloide(h=4):
    h = sp.sympify(h)
    spec = Especificacion(
        capas=[Capa(theta, 0, 2 * pi), Capa(r, 0, sp.sqrt(h)), Capa(z, r**2, h)],
        integrando=r,
        sistema="cilindrico",
        tipo_calculo="volumen",
        descripcion=f"Volumen bajo el paraboloide z = x² + y² y por debajo del plano z = {h}.",
        info_volumen={"grafico": {"tipo": "paraboloide", "h": h}, "nombre": "Paraboloide"},
    )
    return spec


def solido_entre_superficies(sup, inf, xa, xb, y_inf, y_sup):
    """Volumen entre la superficie ``sup`` (arriba) y ``inf`` (abajo) sobre una
    región plana dada por x ∈ [xa, xb], y ∈ [y_inf, y_sup]."""
    # Se parsea con los símbolos reales del módulo para que coincidan con los
    # que usa ``Capa`` (que fuerza ``real=True``). De lo contrario ``sympify``
    # crearía símbolos sin supuestos y la integración los trataría como
    # constantes distintas de la variable de integración.
    loc = {"x": x, "y": y, "z": z}
    sup_e = sp.sympify(sup, locals=loc)
    inf_e = sp.sympify(inf, locals=loc)
    xa, xb = sp.sympify(xa, locals=loc), sp.sympify(xb, locals=loc)
    y_inf_e, y_sup_e = sp.sympify(y_inf, locals=loc), sp.sympify(y_sup, locals=loc)
    integrando = sp.simplify(sup_e - inf_e)
    spec = Especificacion(
        capas=[Capa(x, xa, xb), Capa(y, y_inf_e, y_sup_e)],
        integrando=integrando,
        sistema="cartesiano",
        tipo_calculo="volumen",
        descripcion="Volumen entre dos superficies sobre la región plana indicada.",
        info_volumen={
            "grafico": {
                "tipo": "superficies",
                "superior": sup_e,
                "inferior": inf_e,
                "region": [Capa(x, xa, xb), Capa(y, y_inf_e, y_sup_e)],
            },
            "nombre": "Sólido entre superficies",
        },
    )
    return spec


CASOS_DISPONIBLES = {
    "esfera": "Esfera de radio a",
    "cilindro": "Cilindro de radio a y altura h",
    "cono": "Cono de radio a y altura h",
    "paraboloide": "Paraboloide z = x² + y² hasta z = h",
    "entre_superficies": "Volumen entre dos superficies (integral doble)",
}
