# -*- coding: utf-8 -*-
"""Utilidades de notación matemática.

Convierte notación LaTeX / texto plano a expresiones de SymPy, y presenta
expresiones de SymPy como LaTeX (para la interfaz) y como texto Unicode
(para copiar/pegar y transcribir a mano).
"""
from __future__ import annotations

import re
from typing import Iterable

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


# --------------------------------------------------------------------------
# Lectura de argumentos LaTeX
# --------------------------------------------------------------------------
def leer_grupo(s: str, i: int):
    """Lee un grupo balanceado ``{...}`` que comienza en ``s[i] == '{'``."""
    if i >= len(s) or s[i] != "{":
        raise ValueError("Se esperaba '{'")
    prof = 0
    j = i
    while j < len(s):
        if s[j] == "{":
            prof += 1
        elif s[j] == "}":
            prof -= 1
            if prof == 0:
                return s[i + 1 : j], j + 1
        j += 1
    raise ValueError("Llaves desbalanceadas en la expresión")


def _leer_argumento(s: str, i: int):
    """Lee el siguiente argumento: un grupo ``{}``, un comando con sus
    argumentos, o un token simple (número/letra/símbolo)."""
    while i < len(s) and s[i].isspace():
        i += 1
    if i >= len(s):
        raise ValueError("Expresión incompleta")
    if s[i] == "{":
        return leer_grupo(s, i)
    if s[i] == "(":
        prof = 0
        j = i
        while j < len(s):
            if s[j] == "(":
                prof += 1
            elif s[j] == ")":
                prof -= 1
                if prof == 0:
                    return s[i + 1 : j], j + 1
            j += 1
        raise ValueError("Paréntesis desbalanceados en la expresión")
    if s[i] == "\\":
        m = re.match(r"\\[a-zA-Z]+", s[i:])
        if not m:
            return s[i], i + 1
        nombre = m.group(0)
        j = i + len(nombre)
        if nombre in (r"\frac", r"\dfrac", r"\tfrac"):
            a, j = _leer_argumento(s, j)
            b, j = _leer_argumento(s, j)
            return nombre + "{" + a + "}{" + b + "}", j
        if nombre == r"\sqrt":
            k = j
            while k < len(s) and s[k].isspace():
                k += 1
            if k < len(s) and s[k] == "[":
                fin = s.find("]", k)
                if fin == -1:
                    raise ValueError("Corchete '[' sin cerrar en \\sqrt")
                idx = s[k + 1 : fin]
                arg, j = _leer_argumento(s, fin + 1)
                return nombre + "[" + idx + "]{" + arg + "}", j
            arg, j = _leer_argumento(s, j)
            return nombre + "{" + arg + "}", j
        return nombre, j
    m = re.match(r"[0-9]+(?:\.[0-9]+)?|[A-Za-z]", s[i:])
    if m:
        return m.group(0), i + m.end()
    return s[i], i + 1


def _expandir_frac(s: str) -> str:
    while True:
        m = re.search(r"\\(?:d|t)?frac", s)
        if not m:
            return s
        i = m.end()
        a, i = _leer_argumento(s, i)
        b, i = _leer_argumento(s, i)
        s = s[: m.start()] + "((" + a + ")/(" + b + "))" + s[i:]


_FUNCIONES_LATEX = [
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "coth",
    "sech",
    "csch",
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "ln",
    "log",
    "exp",
]


def _expandir_funciones(s: str) -> str:
    """Convierte funciones escritas sin paréntesis a forma explícita.

    ``\\sin x`` → ``sin(x)``, ``\\cos^2 y`` → ``(cos(y))^(2)``,
    ``x\\sin y`` → ``x*sin(y)``. Si la función ya va seguida de ``{`` o ``(``
    también se normaliza, y se inserta ``*`` cuando hace falta para no
    confundir el nombre de la función con una variable.
    """
    for nombre in _FUNCIONES_LATEX:
        patron = re.compile(r"\\" + nombre + r"(?![a-zA-Z])")
        pos = 0
        while True:
            m = patron.search(s, pos)
            if not m:
                break
            j = m.end()
            # ¿Potencia inmediata?  \cos^2 ...
            k = j
            while k < len(s) and s[k].isspace():
                k += 1
            potencia = None
            if k < len(s) and s[k] == "^":
                try:
                    exponente, j = _leer_argumento(s, k + 1)
                    potencia = exponente
                except ValueError:
                    pos = m.end()
                    continue
            try:
                arg, fin = _leer_argumento(s, j)
            except ValueError:
                pos = m.end()
                continue
            reemplazo = nombre + "(" + arg + ")"
            if potencia is not None:
                reemplazo = "(" + reemplazo + ")^(" + potencia + ")"
            inicio = m.start()
            pre = ""
            if inicio > 0 and (s[inicio - 1].isalnum() or s[inicio - 1] in ")}"):
                pre = "*"
            s = s[:inicio] + pre + reemplazo + s[fin:]
            pos = inicio + len(pre) + len(reemplazo)
    return s


def _expandir_sqrt(s: str) -> str:
    while True:
        m = re.search(r"\\sqrt", s)
        if not m:
            return s
        i = m.end()
        k = i
        while k < len(s) and s[k].isspace():
            k += 1
        if k < len(s) and s[k] == "[":
            fin = s.find("]", k)
            if fin == -1:
                raise ValueError("Corchete '[' sin cerrar en \\sqrt")
            n = s[k + 1 : fin]
            a, j = _leer_argumento(s, fin + 1)
            rep = "((" + a + ")**(1/(" + n + ")))"
        else:
            a, j = _leer_argumento(s, i)
            rep = "sqrt(" + a + ")"
        s = s[: m.start()] + rep + s[j:]


# --------------------------------------------------------------------------
# Normalización LaTeX -> expresión tipo Python
# --------------------------------------------------------------------------
_COMANDOS = [
    ("varepsilon", "epsilon"),
    ("vartheta", "theta"),
    ("varphi", "phi"),
    ("arcsin", "asin"),
    ("arccos", "acos"),
    ("arctan", "atan"),
    ("sinh", "sinh"),
    ("cosh", "cosh"),
    ("tanh", "tanh"),
    ("coth", "coth"),
    ("sech", "sech"),
    ("csch", "csch"),
    ("cdot", "*"),
    ("times", "*"),
    ("ast", "*"),
    ("div", "/"),
    ("infty", "oo"),
    ("theta", "theta"),
    ("lambda", "lambda"),
    ("alpha", "alpha"),
    ("beta", "beta"),
    ("gamma", "gamma"),
    ("delta", "delta"),
    ("epsilon", "epsilon"),
    ("omega", "omega"),
    ("Omega", "Omega"),
    ("Delta", "Delta"),
    ("Gamma", "Gamma"),
    ("sigma", "sigma"),
    ("tau", "tau"),
    ("eta", "eta"),
    ("zeta", "zeta"),
    ("kappa", "kappa"),
    ("chi", "chi"),
    ("psi", "psi"),
    ("phi", "phi"),
    ("rho", "rho"),
    ("mu", "mu"),
    ("nu", "nu"),
    ("varpi", "pi"),
    ("pi", "pi"),
    ("ln", "log"),
    ("log", "log"),
    ("exp", "exp"),
    ("min", "Min"),
    ("max", "Max"),
    ("sin", "sin"),
    ("cos", "cos"),
    ("tan", "tan"),
    ("cot", "cot"),
    ("sec", "sec"),
    ("csc", "csc"),
]

_FUNCIONES = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot,
    "sec": sp.sec,
    "csc": sp.csc,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "coth": sp.coth,
    "sech": sp.sech,
    "csch": sp.csch,
    "log": sp.log,
    "exp": sp.exp,
    "sqrt": sp.sqrt,
    "Abs": sp.Abs,
    "Min": sp.Min,
    "Max": sp.Max,
    "pi": sp.pi,
    "oo": sp.oo,
    "e": sp.E,
    "E": sp.E,
}


def normalizar(texto: str) -> str:
    """Convierte una cadena en notación LaTeX a una expresión tipo Python."""
    s = texto.strip()
    s = re.sub(r"\\displaystyle|\\limits|\\nolimits", "", s)
    s = re.sub(r"\\left|\\right", "", s)
    s = re.sub(r"\\[!,;: ]", " ", s)
    s = _expandir_funciones(s)
    s = _expandir_frac(s)
    s = _expandir_sqrt(s)
    for cmd, rep in _COMANDOS:
        s = re.sub(r"\\" + cmd + r"(?![a-zA-Z])", rep, s)
    # Restos de comandos desconocidos: se elimina la barra invertida.
    s = re.sub(r"\\([a-zA-Z]+)", r"\1", s)
    s = s.replace("{", "(").replace("}", ")")
    s = s.replace("^", "**")
    return s


def parsear(texto: str, variables: Iterable[str] = ()) -> sp.Expr:
    """Parsea ``texto`` (LaTeX o texto plano) a una expresión de SymPy.

    Las variables indicadas se crean como símbolos reales para que coincidan
    exactamente con los de la integración.
    """
    s = normalizar(texto)
    locales = dict(_FUNCIONES)
    for v in variables:
        locales[str(v)] = sp.Symbol(str(v), real=True)
    transformaciones = standard_transformations + (
        convert_xor,
        implicit_multiplication_application,
    )
    return parse_expr(
        s, local_dict=locales, transformations=transformaciones, evaluate=True
    )


# --------------------------------------------------------------------------
# Presentación
# --------------------------------------------------------------------------
_MAPA_GRIEGO = {
    "theta": "θ",
    "phi": "φ",
    "varphi": "φ",
    "rho": "ρ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "varepsilon": "ε",
    "omega": "ω",
    "Omega": "Ω",
    "sigma": "σ",
    "tau": "τ",
    "eta": "η",
    "zeta": "ζ",
    "kappa": "κ",
    "chi": "χ",
    "psi": "ψ",
    "Delta": "Δ",
    "Gamma": "Γ",
    "Lambda": "Λ",
}


def a_latex(expr) -> str:
    """LaTeX de una expresión (apto para KaTeX/MathJax)."""
    if expr is None:
        return ""
    return sp.latex(sp.sympify(expr))


def latex_limpio(tex: str) -> str:
    """Limpia LaTeX para el subconjunto que entiende ``matplotlib.mathtext``."""
    if not tex:
        return ""
    tex = tex.replace(r"\left", "").replace(r"\right", "")
    tex = re.sub(r"\\displaystyle|\\limits|\\nolimits|\\,|\\!|\\;|\\:", " ", tex)
    tex = tex.replace(r"\Bigg|", "|").replace(r"\Big|", "|").replace(r"\big|", "|")
    return tex


def _unir_factores(textos: list) -> str:
    if not textos:
        return ""
    out = textos[0]
    for p in textos[1:]:
        if p.startswith("1/(") and p.endswith(")"):
            out = out + "/" + p[3:-1]
        elif out and (out[-1].isdigit() or out[-1] in ")√") and (p[0].isalpha() or p[0] == "("):
            out = out + p
        elif out and out[-1].isalnum() and p[0] == "(":
            out = out + p
        else:
            out = out + "*" + p
    return out


def a_unicode(expr) -> str:
    """Representación lineal legible en Unicode de una expresión."""
    try:
        e = sp.sympify(expr)
    except Exception:
        return str(expr)
    return _u(e)


def _u(e) -> str:  # noqa: C901 (función de presentación, muchas ramas)
    if e is None:
        return ""
    if e is sp.oo:
        return "∞"
    if e is -sp.oo:
        return "-∞"
    if e is sp.pi:
        return "π"
    if e is sp.E:
        return "e"
    if e is sp.I:
        return "i"
    if isinstance(e, sp.Integer):
        return str(e)
    if isinstance(e, sp.Rational):
        return f"{e.p}/{e.q}"
    if isinstance(e, sp.Float):
        return str(e)
    if isinstance(e, sp.Symbol):
        return _MAPA_GRIEGO.get(e.name, e.name)
    if isinstance(e, sp.Pow):
        base, ex = e.args
        if ex == sp.Rational(1, 2):
            return "√(" + _u(base) + ")"
        if isinstance(ex, sp.Rational) and ex.q != 1:
            if ex.p == 1:
                return "(" + _u(base) + ")^(1/" + str(ex.q) + ")"
            return "(" + _u(base) + ")^(" + f"{ex.p}/{ex.q}" + ")"
        if isinstance(ex, sp.Integer) and ex < 0:
            k = -ex
            if k == 1:
                return "1/(" + _u(base) + ")"
            return "1/(" + _u(base) + "^" + str(k) + ")"
        if ex.is_number and ex.is_negative:
            return "1/(" + _u(base) + "^(" + _u(-ex) + "))"
        return _u(base) + "^(" + _u(ex) + ")"
    if isinstance(e, sp.Mul):
        coeff, resto = e.as_coeff_Mul()
        factores = list(resto.args) if resto.is_Mul else [resto]
        textos = []
        for f in factores:
            t = _u(f)
            if f.is_Add:
                t = "(" + t + ")"
            textos.append(t)
        cuerpo = _unir_factores(textos)
        if coeff == 1:
            return cuerpo
        if coeff == -1:
            return "-" + cuerpo
        if isinstance(coeff, sp.Rational) and coeff.q != 1:
            if coeff.p == 1:
                return cuerpo + "/" + str(coeff.q)
            if coeff.p == -1:
                return "-" + cuerpo + "/" + str(coeff.q)
            return f"{coeff.p}*{cuerpo}/{coeff.q}"
        ctxt = _u(coeff)
        if cuerpo and (cuerpo[0].isalpha() or cuerpo[0] in "√("):
            return ctxt + cuerpo
        return ctxt + "*" + cuerpo
    if isinstance(e, sp.Add):
        partes = []
        for i, t in enumerate(e.args):
            coeff = t.as_coeff_Mul()[0]
            if coeff.is_negative:
                frag = _u(-t)
                partes.append(("-" if i == 0 else " - ") + frag)
            else:
                frag = _u(t)
                partes.append(("" if i == 0 else " + ") + frag)
        return "".join(partes)
    if isinstance(e, sp.Integral):
        lims = ""
        ds = ""
        for v, a, b in e.limits:
            lims += f"∫[{_u(a)}..{_u(b)}] "
            ds += " d" + _u(v)
        return lims + _u(e.function) + ds
    if isinstance(e, sp.Function):
        nom = type(e).__name__
        if nom == "exp":
            return "e^(" + _u(e.args[0]) + ")"
        if nom == "log":
            return "ln(" + _u(e.args[0]) + ")"
        if nom == "Abs":
            return "|" + _u(e.args[0]) + "|"
        mapa = {
            "sin": "sin",
            "cos": "cos",
            "tan": "tan",
            "cot": "cot",
            "sec": "sec",
            "csc": "csc",
            "asin": "arcsin",
            "acos": "arccos",
            "atan": "arctan",
            "sinh": "sinh",
            "cosh": "cosh",
            "tanh": "tanh",
        }
        base = mapa.get(nom, nom)
        return base + "(" + ", ".join(_u(a) for a in e.args) + ")"
    return str(e)


def representar_integral(capas, integrando):
    """Devuelve (latex, texto) de una integral múltiple descrita por capas."""
    body_latex = sp.latex(sp.sympify(integrando))
    body_texto = a_unicode(integrando)
    for capa in reversed(capas):
        body_latex = (
            r"\int_{%s}^{%s} %s\, d%s"
            % (sp.latex(capa.inferior), sp.latex(capa.superior), body_latex, sp.latex(capa.variable))
        )
        body_texto = (
            f"∫[{a_unicode(capa.inferior)}..{a_unicode(capa.superior)}] "
            f"{body_texto} d{a_unicode(capa.variable)}"
        )
    return body_latex, body_texto
