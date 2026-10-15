# -*- coding: utf-8 -*-
"""Interpretación de ejercicios escritos en notación matemática.

Admite, entre otras, expresiones como::

    \\int_0^1 \\int_0^{\\sqrt{1-x^2}} (x^2+y^2) \\, dy \\, dx
    \\int_0^{2\\pi} \\int_0^1 e^{r^2} r \\, dr \\, d\\theta
    \\int_0^1 x^2 dx          (texto plano también funciona)

y las convierte en una :class:`~motor.especificacion.Especificacion`.
"""
from __future__ import annotations

import re

import sympy as sp

from .especificacion import Capa, Especificacion
from .latex_utils import a_unicode, normalizar, parsear, _leer_argumento

_MARCA = "\x00INT\x00"


class ErrorEntrada(Exception):
    """Error de interpretación que debe comunicarse al usuario."""


# --------------------------------------------------------------------------
# Preparación del texto
# --------------------------------------------------------------------------
def _preparar(texto: str) -> str:
    s = texto
    s = re.sub(r"\\displaystyle|\\limits|\\nolimits", "", s)
    s = re.sub(r"\\left|\\right", "", s)
    s = re.sub(r"\\[!,;: ]", " ", s)
    # Contar integrales: \iiint cuenta como 3, \iint como 2.
    s = re.sub(r"\\iiint", _MARCA * 3, s)
    s = re.sub(r"\\iint", _MARCA * 2, s)
    s = re.sub(r"\\int", _MARCA, s)
    s = s.replace("∭", _MARCA * 3).replace("∬", _MARCA * 2).replace("∫", _MARCA)
    s = re.sub(r"(?<![A-Za-z_])int(?![A-Za-z_])", _MARCA, s)
    return s


def _extraer_integrales(s: str):
    """Extrae la lista de (límite infer, límite super) y el cuerpo restante."""
    integrales = []
    restante = []
    i = 0
    while i < len(s):
        if s.startswith(_MARCA, i):
            i += len(_MARCA)
            lo = hi = None
            while True:
                j = i
                while j < len(s) and s[j].isspace():
                    j += 1
                if j < len(s) and s[j] in "_^":
                    tipo = s[j]
                    try:
                        atomo, k = _leer_argumento(s, j + 1)
                    except ValueError as exc:
                        raise ErrorEntrada(
                            f"No se pudieron leer los límites de integración: {exc}"
                        ) from exc
                    if tipo == "_":
                        lo = atomo
                    else:
                        hi = atomo
                    i = k
                else:
                    break
            integrales.append((lo, hi))
            while i < len(s) and s[i].isspace():
                i += 1
        else:
            restante.append(s[i])
            i += 1
    return integrales, "".join(restante)


_RE_DIF = re.compile(
    r"(?<![A-Za-z])[dD]\s*(\\theta|\\varphi|\\phi|\\rho|\\lambda|[A-Za-z])"
)


def _extraer_diferenciales(cuerpo: str):
    """Separa el integrando de los diferenciales (que van al final)."""
    coincidencias = list(_RE_DIF.finditer(cuerpo))
    if not coincidencias:
        return [], cuerpo
    corrida = [coincidencias[-1]]
    for m in reversed(coincidencias[:-1]):
        entre = cuerpo[m.end() : corrida[0].start()]
        if entre.strip(" ,\t\r\n") == "":
            corrida.insert(0, m)
        else:
            break
    integrando = cuerpo[: corrida[0].start()]
    difs = [normalizar(m.group(1)) for m in corrida]
    return difs, integrando


# --------------------------------------------------------------------------
# Detección del sistema de coordenadas
# --------------------------------------------------------------------------
def _detectar_sistema(nombres) -> str:
    conj = {str(n) for n in nombres}
    if conj == {"r", "theta"}:
        return "polar"
    if conj == {"r", "theta", "z"}:
        return "cilindrico"
    if "rho" in conj:
        return "esferico"
    if conj <= {"x", "y"}:
        return "cartesiano"
    if conj <= {"x", "y", "z"}:
        return "cartesiano"
    return "general"


# --------------------------------------------------------------------------
# Función principal
# --------------------------------------------------------------------------
def parsear_ejercicio(texto: str) -> Especificacion:
    """Interpreta ``texto`` y devuelve una :class:`Especificacion`.

    Lanza :class:`ErrorEntrada` con un mensaje claro si el ejercicio está
    incompleto o es ambiguo (en lugar de inventar datos).
    """
    if not texto or not texto.strip():
        raise ErrorEntrada("El campo está vacío. Escribe un ejercicio para resolverlo.")

    preparado = _preparar(texto)
    integrales, cuerpo = _extraer_integrales(preparado)
    n = len(integrales)
    if n == 0:
        raise ErrorEntrada(
            "No se detectó ninguna integral. Escribe el ejercicio con \\int "
            "(por ejemplo: \\int_0^1 \\int_0^1 (x+y) dy dx)."
        )

    difs, integrando_txt = _extraer_diferenciales(cuerpo)

    # Notación compacta dV -> dx dy dz
    if len(difs) == 1 and difs[0].lower() in ("v", "vol"):
        difs = ["x", "y", "z"][:n]

    if len(difs) != n:
        raise ErrorEntrada(
            f"Se encontraron {n} integral(es) pero {len(difs)} diferencial(es). "
            "Asegúrate de que cada \\int tenga su diferencial al final "
            "(dx, dy, dz, dr, dθ, dφ, dρ...). Puedes escribir, por ejemplo, "
            "\\int_0^1\\int_0^1 f(x,y)\\,dy\\,dx."
        )

    variables = list(difs)
    integrando_txt = integrando_txt.strip().strip(",").strip()
    if integrando_txt == "":
        integrando = sp.Integer(1)
    else:
        try:
            integrando = parsear(integrando_txt, variables)
        except Exception as exc:  # noqa: BLE001
            raise ErrorEntrada(
                f"No se pudo interpretar el integrando «{integrando_txt.strip()}». "
                f"Detalle: {exc}"
            ) from exc

    capas = []
    for k in range(n):
        lo_t, hi_t = integrales[k]
        if lo_t is None or hi_t is None:
            faltante = "inferior" if lo_t is None else "superior"
            raise ErrorEntrada(
                f"La integral número {k + 1} no tiene límite {faltante}. "
                "Cada integral necesita ambos límites (por ejemplo, \\int_0^1)."
            )
        nombre_var = difs[n - 1 - k]
        var = sp.Symbol(nombre_var, real=True)
        try:
            lo = parsear(lo_t, variables)
            hi = parsear(hi_t, variables)
        except Exception as exc:  # noqa: BLE001
            raise ErrorEntrada(
                f"No se pudieron interpretar los límites de la integral número "
                f"{k + 1} ({a_unicode(lo_t)} a {a_unicode(hi_t)}). Detalle: {exc}"
            ) from exc
        capas.append(Capa(var, lo, hi))

    # Validación: los límites de una capa solo pueden depender de variables
    # más externas (ya integradas antes).
    for k, capa in enumerate(capas):
        prohibidas = {c.variable for c in capas[k:]}
        deps = (capa.inferior.free_symbols | capa.superior.free_symbols) & prohibidas
        if deps:
            nombres = ", ".join(a_unicode(d) for d in sorted(deps, key=str))
            raise ErrorEntrada(
                "Los límites de integración no son coherentes: una integral "
                f"interna depende de {nombres}, que todavía no se ha integrado. "
                "Revisa el orden de los límites y de los diferenciales "
                "(el diferencial más a la derecha corresponde a la integral "
                "más externa)."
            )

    advertencias = []
    for capa in capas:
        if capa.es_constante:
            try:
                if float(capa.inferior) >= float(capa.superior):
                    advertencias.append(
                        "Se detectó un límite inferior mayor o igual que el "
                        f"superior en la variable {a_unicode(capa.variable)}."
                    )
            except (TypeError, ValueError):
                pass

    sistema = _detectar_sistema(difs)
    if integrando == 1:
        tipo_calculo = "volumen" if n == 3 else ("area" if n == 2 else "integral")
    else:
        tipo_calculo = "integral"

    return Especificacion(
        capas=capas,
        integrando=integrando,
        sistema=sistema,
        tipo_calculo=tipo_calculo,
        texto_original=texto.strip(),
        descripcion="",
        advertencias=advertencias,
    )
