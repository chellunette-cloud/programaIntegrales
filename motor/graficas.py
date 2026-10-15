# -*- coding: utf-8 -*-
"""Representación gráfica de regiones de integración (2D) y de sólidos (3D)."""
from __future__ import annotations

import numpy as np
import sympy as sp

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401,E402


def _eval_sobre(expr, nombre_var, arr):
    """Evalúa ``expr`` (función de ``nombre_var``) sobre el arreglo ``arr``."""
    free = set(expr.free_symbols)
    if not free:
        return np.full(arr.shape, float(expr), dtype=float)
    if len(free) != 1 or list(free)[0].name != nombre_var:
        raise ValueError("La expresión no es graficable con esta variable.")
    sym = list(free)[0]
    f = sp.lambdify([sym], expr, modules="numpy")
    return np.broadcast_to(np.asarray(f(arr), dtype=float), arr.shape)


def _limites_numericos(capa):
    return not (capa.inferior.free_symbols or capa.superior.free_symbols)


def _evaluar_xy(expr, X, Y):
    """Evalúa ``expr`` (función de x e y) sobre las mallas ``X``, ``Y``.

    Usa los símbolos reales propios de la expresión en lugar de crear símbolos
    nuevos, para evitar desajustes de supuestos que harían fallar ``lambdify``.
    """
    valores = {"x": X, "y": Y}
    libres = sorted(expr.free_symbols, key=lambda s: s.name)
    if not libres:
        return np.full(X.shape, float(expr), dtype=float)
    f = sp.lambdify(libres, expr, modules="numpy")
    args = [valores[s.name] for s in libres]
    return np.broadcast_to(np.asarray(f(*args), dtype=float), X.shape)


# --------------------------------------------------------------------------
# Región 2D
# --------------------------------------------------------------------------
def figura_region_2d(spec):
    """Devuelve una figura Matplotlib de la región de la integral doble."""
    if spec.dimension != 2:
        return None
    nombres = {c.variable.name for c in spec.capas}
    try:
        if nombres == {"r", "theta"}:
            return _region_polar(spec)
        if nombres <= {"x", "y"}:
            return _region_cartesiana(spec)
    except Exception:  # noqa: BLE001
        return None
    return None


def _region_cartesiana(spec):
    externa, interna = spec.capas[0], spec.capas[1]
    if not _limites_numericos(externa):
        return None
    lo0 = float(externa.inferior)
    hi0 = float(externa.superior)
    t = np.linspace(lo0, hi0, 500)
    lo = _eval_sobre(interna.inferior, externa.variable.name, t)
    hi = _eval_sobre(interna.superior, externa.variable.name, t)

    fig, ax = plt.subplots(figsize=(5.2, 4.4), dpi=110)
    if externa.variable.name == "x":
        ax.fill_between(t, lo, hi, color="#4c78a8", alpha=0.35, label="región R")
        ax.plot(t, lo, color="#1f4e79", lw=1.4)
        ax.plot(t, hi, color="#1f4e79", lw=1.4)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
    else:
        ax.fill_betweenx(t, lo, hi, color="#4c78a8", alpha=0.35, label="región R")
        ax.plot(lo, t, color="#1f4e79", lw=1.4)
        ax.plot(hi, t, color="#1f4e79", lw=1.4)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
    _estilo(ax)
    fig.tight_layout()
    return fig


def _region_polar(spec):
    externa, interna = spec.capas[0], spec.capas[1]  # theta, r
    if not _limites_numericos(externa):
        return None
    t0 = float(externa.inferior)
    t1 = float(externa.superior)
    th = np.linspace(t0, t1, 600)
    try:
        r_lo = _eval_sobre(interna.inferior, "theta", th)
        r_hi = _eval_sobre(interna.superior, "theta", th)
    except ValueError:
        return None
    r_lo = np.maximum(r_lo, 0.0)
    r_hi = np.maximum(r_hi, 0.0)
    x_lo, y_lo = r_lo * np.cos(th), r_lo * np.sin(th)
    x_hi, y_hi = r_hi * np.cos(th), r_hi * np.sin(th)
    px = np.concatenate([x_hi, x_lo[::-1]])
    py = np.concatenate([y_hi, y_lo[::-1]])

    fig, ax = plt.subplots(figsize=(5.2, 4.4), dpi=110)
    ax.fill(px, py, color="#4c78a8", alpha=0.35, label="región R")
    ax.plot(x_hi, y_hi, color="#1f4e79", lw=1.5)
    ax.plot(x_lo, y_lo, color="#1f4e79", lw=1.5)
    ax.axhline(0, color="#bbb", lw=0.8)
    ax.axvline(0, color="#bbb", lw=0.8)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.axis("equal")
    _estilo(ax)
    fig.tight_layout()
    return fig


def _estilo(ax):
    ax.grid(True, ls=":", alpha=0.5)
    ax.legend(loc="best", fontsize=8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


# --------------------------------------------------------------------------
# Sólido 3D
# --------------------------------------------------------------------------
def figura_solido_3d(spec):
    info = (spec.info_volumen or {}).get("grafico")
    if not info:
        return None
    tipo = info.get("tipo")
    try:
        if tipo == "esfera":
            return _dibujo_esfera(float(info["a"]))
        if tipo == "cilindro":
            return _dibujo_cilindro(float(info["a"]), float(info["h"]))
        if tipo == "cono":
            return _dibujo_cono(float(info["a"]), float(info["h"]))
        if tipo == "paraboloide":
            return _dibujo_paraboloide(float(info["h"]))
        if tipo == "superficies":
            return _dibujo_superficies(info)
    except Exception:  # noqa: BLE001
        return None
    return None


def _nuevo_3d(figsize=(5.4, 4.6)):
    fig = plt.figure(figsize=figsize, dpi=110)
    ax = fig.add_subplot(111, projection="3d")
    return fig, ax


def _dibujo_esfera(a):
    fig, ax = _nuevo_3d()
    u = np.linspace(0, 2 * np.pi, 80)
    v = np.linspace(0, np.pi, 50)
    U, V = np.meshgrid(u, v)
    X = a * np.sin(V) * np.cos(U)
    Y = a * np.sin(V) * np.sin(U)
    Z = a * np.cos(V)
    ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.75, linewidth=0, antialiased=True)
    ax.set_title(f"Esfera de radio {a:g}")
    _etiquetas3d(ax)
    return fig


def _dibujo_cilindro(a, h):
    fig, ax = _nuevo_3d()
    u = np.linspace(0, 2 * np.pi, 60)
    zz = np.linspace(0, h, 30)
    U, Z = np.meshgrid(u, zz)
    X = a * np.cos(U)
    Y = a * np.sin(U)
    ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8, linewidth=0)
    rr = np.linspace(0, a, 25)
    R, TH = np.meshgrid(rr, u)
    ax.plot_surface(R * np.cos(TH), R * np.sin(TH), np.full_like(R, h), alpha=0.35, color="#f58518")
    ax.set_title(f"Cilindro r = {a:g}, 0 ≤ z ≤ {h:g}")
    _etiquetas3d(ax)
    return fig


def _dibujo_cono(a, h):
    fig, ax = _nuevo_3d()
    u = np.linspace(0, 2 * np.pi, 60)
    rr = np.linspace(0, a, 30)
    U, R = np.meshgrid(u, rr)
    Z = h * (1 - R / a)
    ax.plot_surface(R * np.cos(U), R * np.sin(U), Z, cmap="plasma", alpha=0.8, linewidth=0)
    ax.set_title(f"Cono r ≤ {a:g}(1 − z/{h:g})")
    _etiquetas3d(ax)
    return fig


def _dibujo_paraboloide(h):
    fig, ax = _nuevo_3d()
    u = np.linspace(0, 2 * np.pi, 60)
    rr = np.linspace(0, np.sqrt(h), 30)
    U, R = np.meshgrid(u, rr)
    X, Y, Z = R * np.cos(U), R * np.sin(U), R**2
    ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8, linewidth=0)
    ax.plot_surface(X, Y, np.full_like(Z, h), alpha=0.3, color="#f58518")
    ax.set_title(f"Paraboloide z = x² + y²,  z ≤ {h:g}")
    _etiquetas3d(ax)
    return fig


def _dibujo_superficies(info):
    capas = info["region"]
    externa, interna = capas[0], capas[1]
    if not _limites_numericos(externa):
        return None
    lo0, hi0 = float(externa.inferior), float(externa.superior)
    t = np.linspace(lo0, hi0, 50)
    lo = _eval_sobre(interna.inferior, externa.variable.name, t)
    hi = _eval_sobre(interna.superior, externa.variable.name, t)
    s = np.linspace(0, 1, 40)
    T = np.tile(t, (s.size, 1))
    inner = (lo[None, :] + s[:, None] * (hi - lo)[None, :])
    if externa.variable.name == "x":
        X, Y = T, inner
    else:
        X, Y = inner, T
    sup = info["superior"]
    inf_ = info["inferior"]
    Zs = _evaluar_xy(sup, X, Y)
    Zi = _evaluar_xy(inf_, X, Y)
    fig, ax = _nuevo_3d()
    ax.plot_surface(X, Y, Zs, cmap="viridis", alpha=0.8, linewidth=0)
    ax.plot_surface(X, Y, Zi, cmap="magma", alpha=0.55, linewidth=0)
    ax.set_title("Superficie superior e inferior")
    _etiquetas3d(ax)
    return fig


def _etiquetas3d(ax):
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
