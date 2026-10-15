# -*- coding: utf-8 -*-
"""Cambio de coordenadas: polares, cilíndricas y esféricas.

Incluye la conversión de una integral doble cartesiana a coordenadas polares
para regiones típicas (círculos, semicírculos, sectores, coronas).
"""
from __future__ import annotations

import sympy as sp

from .especificacion import Capa, Especificacion, Paso
from .latex_utils import a_unicode, representar_integral

x, y, z = sp.symbols("x y z", real=True)
r, theta = sp.symbols("r theta", real=True)
rho, phi = sp.symbols("rho phi", real=True)

# Información de jacobianos para la sección de fórmulas.
JACOBIANOS = {
    "polar": {
        "transformacion": r"x=r\cos\theta,\qquad y=r\sin\theta",
        "jacobiano": r"J=\frac{\partial(x,y)}{\partial(r,\theta)}=r",
        "diferencial": r"dA=r\,dr\,d\theta",
    },
    "cilindrico": {
        "transformacion": r"x=r\cos\theta,\qquad y=r\sin\theta,\qquad z=z",
        "jacobiano": r"J=r",
        "diferencial": r"dV=r\,dr\,d\theta\,dz",
    },
    "esferico": {
        "transformacion": r"x=\rho\sin\phi\cos\theta,\quad y=\rho\sin\phi\sin\theta,\quad z=\rho\cos\phi",
        "jacobiano": r"J=\rho^{2}\sin\phi",
        "diferencial": r"dV=\rho^{2}\sin\phi\,d\rho\,d\phi\,d\theta",
    },
}


# Regiones típicas para el cambio a polares.
# Cada entrada: (nombre, descripción, θ_inf, θ_sup, r_inf, r_sup)
def _presets(a_expr, b_expr):
    p = sp.pi
    return {
        "disco": (
            "Disco de radio a centrado en el origen  (x² + y² ≤ a²)",
            0,
            2 * p,
            0,
            a_expr,
        ),
        "semicirculo_superior": (
            "Semicírculo superior de radio a  (y ≥ 0, x² + y² ≤ a²)",
            0,
            p,
            0,
            a_expr,
        ),
        "semicirculo_inferior": (
            "Semicírculo inferior de radio a  (y ≤ 0, x² + y² ≤ a²)",
            p,
            2 * p,
            0,
            a_expr,
        ),
        "cuarto_circulo": (
            "Cuarto de círculo en el primer cuadrante  (x ≥ 0, y ≥ 0, x² + y² ≤ a²)",
            0,
            p / 2,
            0,
            a_expr,
        ),
        "corona": (
            "Corona circular  (a² ≤ x² + y² ≤ b²)",
            0,
            2 * p,
            a_expr,
            b_expr,
        ),
        "cardioide": (
            "Interior del cardioide  r = a(1 + cos θ)",
            0,
            2 * p,
            0,
            a_expr * (1 + sp.cos(theta)),
        ),
        "rosa_4": (
            "Rosa de 4 pétalos  r = a·cos(2θ)",
            0,
            2 * p,
            0,
            a_expr * sp.cos(2 * theta),
        ),
    }


def convertir_a_polares(integrando_xy: sp.Expr, tipo: str, a=1, b=2):
    """Convierte ``∫∫ f(x,y) dA`` a polares para una región típica.

    Devuelve ``(especificacion, pasos)`` donde los pasos documentan la
    sustitución y el jacobiano.
    """
    a_expr = sp.sympify(a)
    b_expr = sp.sympify(b)
    presets = _presets(a_expr, b_expr)
    if tipo not in presets:
        raise ValueError(f"Región desconocida: {tipo}")

    nombre, _, th_inf, th_sup, r_inf, r_sup = presets[tipo]

    # Se parsea con los símbolos reales del módulo para que coincidan con los
    # usados en la sustitución a polares (evita símbolos sin supuestos).
    f_xy = sp.sympify(integrando_xy, locals={"x": x, "y": y})
    f_polar = sp.simplify(f_xy.subs({x: r * sp.cos(theta), y: r * sp.sin(theta)}))
    integrando = sp.simplify(f_polar * r)  # jacobiano r

    capas = [Capa(theta, th_inf, th_sup), Capa(r, r_inf, r_sup)]
    spec = Especificacion(
        capas=capas,
        integrando=integrando,
        sistema="polar",
        tipo_calculo="integral",
        descripcion=nombre,
        texto_original=f"Conversión a polares de ∫∫ ({a_unicode(f_xy)}) dA sobre {nombre}",
    )

    pasos = []
    pasos.append(
        Paso(
            "Cambio a coordenadas polares",
            "Se usa la transformación x = r·cos θ, y = r·sin θ, con elemento de "
            "área dA = r·dr·dθ (el factor r es el jacobiano de la transformación).",
            [
                (r"x=r\cos\theta,\qquad y=r\sin\theta", "x = r·cos θ,  y = r·sin θ"),
                (r"dA = r\,dr\,d\theta", "dA = r·dr·dθ"),
            ],
            "info",
        )
    )
    pasos.append(
        Paso(
            "Sustitución del integrando",
            "Se reemplazan x e y por sus expresiones en r y θ y se multiplica por el jacobiano r.",
            [
                (
                    r"f(x,y)\,dA \;\longrightarrow\; f\big(r\cos\theta,\,r\sin\theta\big)\, r\,dr\,d\theta",
                    f"{a_unicode(f_xy)}·dA  ⟶  ({a_unicode(f_polar)})·r·dr·dθ",
                )
            ],
            "info",
        )
    )
    pasos.append(
        Paso(
            "Nuevos límites",
            f"Región: {nombre}. Límites en θ y r según la región.",
            [
                (r"\theta \in [%s,\,%s]" % (sp.latex(th_inf), sp.latex(th_sup)),
                 f"θ ∈ [{a_unicode(th_inf)}, {a_unicode(th_sup)}]"),
                (r"r \in [%s,\,%s]" % (sp.latex(r_inf), sp.latex(r_sup)),
                 f"r ∈ [{a_unicode(r_inf)}, {a_unicode(r_sup)}]"),
            ],
            "info",
        )
    )
    return spec, pasos


def formulas_cambio(sistema: str):
    info = JACOBIANOS.get(sistema)
    if not info:
        return []
    return [
        {"titulo": "Transformación", "latex": info["transformacion"], "texto": info["transformacion"]},
        {"titulo": "Jacobiano", "latex": info["jacobiano"], "texto": info["jacobiano"]},
        {"titulo": "Elemento diferencial", "latex": info["diferencial"], "texto": info["diferencial"]},
    ]
