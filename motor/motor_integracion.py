# -*- coding: utf-8 -*-
"""Motor de integración simbólica paso a paso.

Resuelve una :class:`~motor.especificacion.Especificacion` produciendo una
lista de pasos con explicación y fórmulas, verifica el resultado con
integración numérica independiente (SciPy) y detecta cuándo aparece una
función especial o cuándo no existe antiderivada elemental.
"""
from __future__ import annotations

import sympy as sp

from .ejecutor import ejecutar_con_timeout
from .especificacion import Capa, Especificacion, Paso, Solucion
from .latex_utils import a_unicode, representar_integral

# Funciones que SymPy puede devolver y que NO son elementales.
_NOMBRES_ESPECIALES = {
    "erf",
    "erfi",
    "erfc",
    "erfinv",
    "Ei",
    "li",
    "Li",
    "Si",
    "Ci",
    "Shi",
    "Chi",
    "fresnelc",
    "fresnels",
    "expint",
    "gamma",
    "loggamma",
    "lowergamma",
    "uppergamma",
    "polygamma",
    "besselj",
    "bessely",
    "besseli",
    "besselk",
    "hankel1",
    "hankel2",
    "lambertw",
    "polylog",
    "zeta",
    "lerchphi",
    "hyper",
    "meijerg",
    "elliptic_f",
    "elliptic_e",
    "elliptic_k",
    "dawson",
}


# --------------------------------------------------------------------------
# Utilidades internas
# --------------------------------------------------------------------------
def usa_funciones_especiales(expr) -> bool:
    if expr is None:
        return False
    for f in sp.sympify(expr).atoms(sp.Function):
        if type(f).__name__ in _NOMBRES_ESPECIALES:
            return True
    return False


def _es_problematico(r) -> bool:
    if r is None:
        return True
    try:
        if r.has(sp.nan) or r.has(sp.zoo) or r.has(sp.oo) or r.has(-sp.oo):
            return True
        if r.is_finite is False:
            return True
    except Exception:  # noqa: BLE001
        return False
    return False


def sustituir_limite(F, var, val, direccion: str = "-"):
    """Evalúa F en ``var = val``; si es singular usa el límite lateral."""
    try:
        r = F.subs(var, val)
    except Exception:  # noqa: BLE001
        r = sp.nan
    if _es_problematico(r):
        for d in (direccion, "+", "-"):
            try:
                r2 = sp.limit(F, var, val, dir=d)
            except Exception:  # noqa: BLE001
                continue
            if not _es_problematico(r2):
                return r2
    return r

def _es_finito_num(x):
    try:
        return x is not None and x == x and abs(x) != float("inf")
    except Exception:  # noqa: BLE001
        return False

def a_decimal(expr):
    """Convierte una expresión exacta a un ``float`` (parte real)."""
    try:
        v = complex(sp.N(expr, 20))
    except Exception:  # noqa: BLE001
        return None
    if abs(v.imag) < 1e-9:
        return float(v.real)
    return None


def latex_seguro(expr):
    """Devuelve (latex, apto) donde ``apto`` indica si puede renderizarse."""
    if expr is None:
        return "", False
    try:
        if sp.sympify(expr).has(sp.Piecewise):
            return "", False
        tex = sp.latex(sp.sympify(expr))
        if "cases" in tex or "Piecewise" in tex:
            return "", False
        return tex, True
    except Exception:  # noqa: BLE001
        return "", False


def _resolver_capa(actual, var, lo, hi):
    """Calcula una integral simple (antiderivada y evaluación de límites)."""
    F = sp.integrate(actual, var)
    if F is None or sp.sympify(F).has(sp.Integral):
        return {"ok": False}
    F = sp.simplify(F)
    F_sup = sustituir_limite(F, var, hi, "-")
    F_inf = sustituir_limite(F, var, lo, "+")
    res = sp.simplify(F_sup - F_inf)
    return {
        "ok": True,
        "antiderivada": F,
        "F_sup": F_sup,
        "F_inf": F_inf,
        "resultado": res,
    }


# --------------------------------------------------------------------------
# Integración numérica (verificación y respaldo)
# --------------------------------------------------------------------------
def calcular_numerico(spec: Especificacion):
    """Integra numéricamente con SciPy mediante ``quad`` anidado.

    Se usa integración anidada (en lugar de ``nquad``) porque es más robusta
    frente a límites con derivada singular, como ``sqrt(1-x^2)``.
    """
    try:
        import numpy as np
        from scipy.integrate import quad
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"SciPy/NumPy no disponible: {exc}"}

    varorden = spec.variables
    n = len(varorden)
    if n == 0:
        return {"ok": False, "error": "No hay variables de integración."}

    try:
        func = sp.lambdify(varorden, spec.integrando, modules=["numpy", "scipy"])
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"No se pudo preparar la función: {exc}"}

    # Precompilar los límites (funciones de las variables externas).
    limites = []
    for i, capa in enumerate(spec.capas):
        deps = varorden[:i]
        try:
            if deps:
                lo_f = sp.lambdify(deps, capa.inferior, modules="numpy")
                hi_f = sp.lambdify(deps, capa.superior, modules="numpy")
            else:
                lo_f = float(capa.inferior)
                hi_f = float(capa.superior)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"Límite no evaluable: {exc}"}
        limites.append((lo_f, hi_f))

    def evaluar(i, valores):
        if i == n:
            try:
                r = float(func(*valores))
            except Exception:  # noqa: BLE001
                return 0.0
            return r if np.isfinite(r) else 0.0
        lo_f, hi_f = limites[i]
        try:
            a = float(lo_f) if isinstance(lo_f, float) else float(lo_f(*valores))
            b = float(hi_f) if isinstance(hi_f, float) else float(hi_f(*valores))
        except Exception:  # noqa: BLE001
            return 0.0
        if np.isnan(a) or np.isnan(b) or b <= a:
            return 0.0
        v, _ = quad(
            lambda t: evaluar(i + 1, valores + [t]),
            a,
            b,
            limit=100,
            epsabs=1e-9,
            epsrel=1e-9,
        )
        return v

    try:
        valor = evaluar(0, [])
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"La integración numérica falló: {exc}"}

    if not _es_finito_num(valor):
        return {"ok": False, "error": "La integral numérica no convergió a un valor finito."}
    return {"ok": True, "valor": float(valor), "error": None}


# --------------------------------------------------------------------------
# Fórmulas empleadas
# --------------------------------------------------------------------------
def _formulas_empleadas(spec: Especificacion):
    f = []
    sis = spec.sistema
    if sis == "polar":
        f.append(("Cambio a coordenadas polares", r"x=r\cos\theta,\quad y=r\sin\theta"))
        f.append(("Jacobiano (elemento de área)", r"dA = r\,dr\,d\theta"))
    elif sis == "cilindrico":
        f.append(("Coordenadas cilíndricas", r"x=r\cos\theta,\quad y=r\sin\theta,\quad z=z"))
        f.append(("Jacobiano (elemento de volumen)", r"dV = r\,dr\,d\theta\,dz"))
    elif sis == "esferico":
        f.append(
            (
                "Coordenadas esféricas",
                r"x=\rho\sin\phi\cos\theta,\quad y=\rho\sin\phi\sin\theta,\quad z=\rho\cos\phi",
            )
        )
        f.append(("Jacobiano (elemento de volumen)", r"dV = \rho^{2}\sin\phi\,d\rho\,d\phi\,d\theta"))
    else:
        f.append(("Elemento de área (cartesiano)", r"dA = dy\,dx"))
        f.append(("Elemento de volumen (cartesiano)", r"dV = dz\,dy\,dx"))

    if spec.tipo_calculo == "area":
        f.append(("Área de una región plana", r"A = \iint_{R} dA"))
    if spec.tipo_calculo == "volumen":
        f.append(("Volumen entre dos superficies", r"V = \iint_{R}\big(z_{sup}-z_{inf}\big)\,dA"))
        f.append(("Volumen con integral triple", r"V = \iiint_{S} dV"))
    return [{"titulo": t, "latex": l, "texto": l} for t, l in f]


# --------------------------------------------------------------------------
# Resolución completa
# --------------------------------------------------------------------------
def resolver(spec: Especificacion, timeout: float = 30.0, detalle: bool = True) -> Solucion:
    pasos: list = []
    advertencias = list(spec.advertencias)

    # ---- Paso 1: identificación ----------------------------------------
    tipo_txt = {
        "integral": "integral múltiple",
        "area": "cálculo de un área",
        "volumen": "cálculo de un volumen",
    }.get(spec.tipo_calculo, "integral múltiple")
    sistema_txt = {
        "cartesiano": "coordenadas cartesianas",
        "polar": "coordenadas polares",
        "cilindrico": "coordenadas cilíndricas",
        "esferico": "coordenadas esféricas",
        "general": "coordenadas generales",
    }.get(spec.sistema, spec.sistema)
    var_txt = ", ".join(a_unicode(v) for v in spec.variables)
    explicacion1 = (
        f"Se trata de una {tipo_txt} de orden {spec.dimension}, planteada en "
        f"{sistema_txt}. Variables de integración (de la más externa a la más "
        f"interna): {var_txt}."
    )
    if spec.tipo_calculo == "volumen" and spec.info_volumen:
        explicacion1 += " El integrando es la diferencia entre la superficie superior y la inferior."
    lat0, txt0 = representar_integral(spec.capas, spec.integrando)
    pasos.append(Paso("1. Planteamiento del ejercicio", explicacion1, [(lat0, txt0)], "integral"))

    # ---- Paso 2: límites -----------------------------------------------
    lineas = ["Límites de integración, de la capa más interna a la más externa:"]
    form2 = []
    for capa in reversed(spec.capas):
        lit = (
            f"  • {a_unicode(capa.variable)}: desde {a_unicode(capa.inferior)} "
            f"hasta {a_unicode(capa.superior)}"
        )
        lineas.append(lit)
        deps = capa.inferior.free_symbols | capa.superior.free_symbols
        if deps:
            deps_txt = ", ".join(a_unicode(d) for d in sorted(deps, key=str))
            lineas.append(f"      (depende de {deps_txt})")
        form2.append(
            (
                r"%s \in [%s,\; %s]"
                % (sp.latex(capa.variable), sp.latex(capa.inferior), sp.latex(capa.superior)),
                f"{a_unicode(capa.variable)} ∈ [{a_unicode(capa.inferior)}, {a_unicode(capa.superior)}]",
            )
        )
    pasos.append(Paso("2. Región y límites de integración", "\n".join(lineas), form2, "info"))

    # ---- Pasos 3..: integración capa por capa --------------------------
    actual = spec.integrando
    exito = True
    hubo_timeout = False
    numero = 3
    for indice in range(spec.dimension):
        capa = spec.capas[spec.dimension - 1 - indice]
        var = capa.variable
        lo, hi = capa.inferior, capa.superior

        lat_int, txt_int = representar_integral([capa], actual)
        pasos.append(
            Paso(
                f"{numero}. Integración respecto a {a_unicode(var)} (capa {'interna' if indice == 0 else 'externa' if indice == spec.dimension - 1 else 'intermedia'})",
                f"Se integra respecto a {a_unicode(var)}, tratando las demás variables "
                f"como constantes, desde {a_unicode(lo)} hasta {a_unicode(hi)}.",
                [(lat_int, txt_int)],
                "integral",
            )
        )
        numero += 1

        estado, info = ejecutar_con_timeout(
            _resolver_capa, (actual, var, lo, hi), timeout=timeout
        )
        if estado == "timeout":
            hubo_timeout = True
            advertencias.append(
                f"La integración respecto a {a_unicode(var)} excedió el tiempo "
                "máximo; se muestra el resultado por vía numérica."
            )
            exito = False
            break
        if estado == "error" or not info or not info.get("ok"):
            advertencias.append(
                f"No se encontró una antiderivada elemental respecto a "
                f"{a_unicode(var)}; se recurre a un método numérico."
            )
            exito = False
            break

        F = info["antiderivada"]
        F_sup = info["F_sup"]
        F_inf = info["F_inf"]
        res = info["resultado"]

        latF, okF = latex_seguro(F)
        form_anti = []
        if okF:
            form_anti.append(
                (r"\int %s\, d%s = %s" % (sp.latex(actual), sp.latex(var), latF),
                 f"∫ {a_unicode(actual)} d{a_unicode(var)} = {a_unicode(F)}")
            )
        else:
            form_anti.append(
                (r"\int %s\, d%s" % (sp.latex(actual), sp.latex(var)),
                 f"∫ {a_unicode(actual)} d{a_unicode(var)}  (antiderivada en forma cerrada compleja)")
            )
        pasos.append(
            Paso(
                f"{numero}. Antiderivada respecto a {a_unicode(var)}",
                "Se obtiene una antiderivada de la expresión respecto a la variable indicada.",
                form_anti,
                "integral",
            )
        )
        numero += 1

        lat_sup, _ = latex_seguro(F_sup)
        lat_inf, _ = latex_seguro(F_inf)
        lat_res, ok_res = latex_seguro(res)
        form_eval = []
        if lat_sup and lat_inf:
            form_eval.append((r"F(%s) = %s" % (sp.latex(hi), lat_sup),
                              f"F({a_unicode(hi)}) = {a_unicode(F_sup)}"))
            form_eval.append((r"F(%s) = %s" % (sp.latex(lo), lat_inf),
                              f"F({a_unicode(lo)}) = {a_unicode(F_inf)}"))
        if ok_res:
            form_eval.append(
                (r"\int_{%s}^{%s} %s\, d%s = %s" % (sp.latex(lo), sp.latex(hi), sp.latex(actual), sp.latex(var), lat_res),
                 f"∫[{a_unicode(lo)}..{a_unicode(hi)}] {a_unicode(actual)} d{a_unicode(var)} = {a_unicode(res)}")
            )
        else:
            form_eval.append(("", f"Resultado de esta capa: {a_unicode(res)}"))
        pasos.append(
            Paso(
                f"{numero}. Evaluación en los límites ({a_unicode(var)})",
                f"Se evalúa la antiderivada: F({a_unicode(hi)}) − F({a_unicode(lo)}).",
                form_eval,
                "integral",
            )
        )
        numero += 1
        actual = res

    # ---- Resultado final ----------------------------------------------
    resultado_exacto = None
    resultado_decimal = None
    metodo = "simbolico"
    especiales = False

    if exito:
        resultado_exacto = sp.simplify(actual)
        especiales = usa_funciones_especiales(resultado_exacto)
        resultado_decimal = a_decimal(resultado_exacto)
        metodo = "simbolico_funcion_especial" if especiales else "simbolico"
        latR, okR = latex_seguro(resultado_exacto)
        formR = []
        if okR:
            formR.append((latR, a_unicode(resultado_exacto)))
        pasos.append(
            Paso(
                "Resultado exacto",
                "Se simplifica la expresión obtenida.",
                formR,
                "resultado",
            )
        )
    else:
        metodo = "numerico"
        pasos.append(
            Paso(
                "Resultado",
                "La integral no pudo resolverse de forma simbólica; se presenta el "
                "valor obtenido por integración numérica (aproximado).",
                [],
                "advertencia",
            )
        )

    # ---- Verificación numérica ----------------------------------------
    num = calcular_numerico(spec)
    verificacion = {"numerico": None, "error_numerico": None, "coincide": None, "diferencia": None, "mensaje": ""}
    if num.get("ok"):
        verificacion["numerico"] = num["valor"]
        verificacion["error_numerico"] = num["error"]
        if not exito:
            resultado_decimal = num["valor"]
        if resultado_decimal is not None:
            dif = abs(float(resultado_decimal) - num["valor"])
            referencia = max(1.0, abs(num["valor"]))
            verificacion["diferencia"] = dif
            verificacion["coincide"] = dif <= 1e-4 * referencia
            if verificacion["coincide"]:
                verificacion["mensaje"] = (
                    "El valor simbólico y la integración numérica independiente coinciden."
                )
            else:
                verificacion["mensaje"] = (
                    "Advertencia: el valor simbólico y el numérico no coinciden "
                    "plenamente; revisa los límites o la región."
                )
    else:
        verificacion["mensaje"] = num.get("error", "No fue posible verificar numéricamente.")

    if verificacion["numerico"] is not None:
        formV = [
            (
                r"\approx %s" % f"{verificacion['numerico']:.10g}",
                f"valor numérico ≈ {verificacion['numerico']:.10g}",
            )
        ]
        pasos.append(
            Paso(
                "Verificación numérica (SciPy)",
                verificacion["mensaje"]
                + (
                    f" Error estimado: {verificacion['error_numerico']:.2e}."
                    if verificacion["error_numerico"] is not None
                    else ""
                ),
                formV,
                "verificacion",
            )
        )

    # ---- Método / notas -------------------------------------------------
    if metodo == "simbolico":
        metodo_txt = "Cálculo simbólico exacto (SymPy) verificado numéricamente (SciPy)."
    elif metodo == "simbolico_funcion_especial":
        metodo_txt = (
            "Cálculo simbólico exacto usando una función especial (no elemental), "
            "verificado numéricamente (SciPy)."
        )
        advertencias.append(
            "El resultado contiene una función especial (por ejemplo erf, erfi, Ei, Si…), "
            "por lo que la antiderivada NO es elemental."
        )
    else:
        metodo_txt = "Cálculo numérico aproximado (SciPy). No es un resultado exacto."

    return Solucion(
        especificacion=spec,
        pasos=pasos,
        resultado=resultado_exacto,
        resultado_decimal=resultado_decimal,
        exacto=(metodo != "numerico"),
        metodo=metodo_txt,
        verificacion=verificacion,
        advertencias=advertencias,
        formulas_empleadas=_formulas_empleadas(spec),
        usa_funciones_especiales=especiales,
    )
