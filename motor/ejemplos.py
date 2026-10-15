# -*- coding: utf-8 -*-
"""Ejemplos de práctica incluidos en la aplicación."""
from __future__ import annotations

EJEMPLOS = [
    {
        "titulo": "Doble sobre rectángulo",
        "texto": r"\int_0^2\int_0^1 (x+y)\,dy\,dx",
    },
    {
        "titulo": "Doble sobre semicírculo (cuarto de disco)",
        "texto": r"\int_0^1\int_0^{\sqrt{1-x^2}}(x^2+y^2)\,dy\,dx",
    },
    {
        "titulo": "Doble con límites variables",
        "texto": r"\int_0^1\int_0^{x}(x+y)\,dy\,dx",
    },
    {
        "titulo": "Cambio a coordenadas polares",
        "texto": r"\int_0^{2\pi}\int_0^1 e^{r^2}\,r\,dr\,d\theta",
    },
    {
        "titulo": "Integral con exponencial",
        "texto": r"\int_0^1\int_0^1 e^{x+y}\,dy\,dx",
    },
    {
        "titulo": "Triple sobre cubo",
        "texto": r"\int_0^1\int_0^1\int_0^1 xyz\,dz\,dy\,dx",
    },
    {
        "titulo": "Volumen de una esfera (coordenadas esféricas)",
        "texto": r"\int_0^{5}\int_0^{2\pi}\int_0^{\pi}\rho^2\sin\phi\,d\phi\,d\theta\,d\rho",
    },
    {
        "titulo": "Área de una región",
        "texto": r"\int_0^{1}\int_{0}^{1-x} dy\,dx",
    },
    {
        "titulo": "Sin antiderivada elemental (función especial)",
        "texto": r"\int_0^1 e^{x^2}\,dx",
    },
    {
        "titulo": "Ejemplo con límites ambiguos (para probar el control de errores)",
        "texto": r"\int_0^1 \int_0^1 (x+y)",
    },
]


def lista_titulos():
    return [e["titulo"] for e in EJEMPLOS]


def ejemplo_por_titulo(titulo):
    for e in EJEMPLOS:
        if e["titulo"] == titulo:
            return e
    return EJEMPLOS[0]
