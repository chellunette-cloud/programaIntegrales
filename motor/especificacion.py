# -*- coding: utf-8 -*-
"""Estructuras de datos del motor matemático.

Estas clases describen, de forma independiente de la interfaz, un ejercicio de
integración múltiple y su solución paso a paso.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import sympy as sp


@dataclass
class Capa:
    """Una integral simple dentro de la integral múltiple.

    Parameters
    ----------
    variable : sp.Symbol
        Variable de integración de esta capa.
    inferior, superior : sp.Expr
        Límites de integración (pueden depender de variables más externas).
    """

    variable: sp.Symbol
    inferior: sp.Expr
    superior: sp.Expr

    def __post_init__(self):
        if not isinstance(self.variable, sp.Symbol):
            self.variable = sp.Symbol(str(self.variable), real=True)
        self.inferior = sp.sympify(self.inferior)
        self.superior = sp.sympify(self.superior)

    @property
    def es_constante(self) -> bool:
        return not (self.inferior.free_symbols or self.superior.free_symbols)


@dataclass
class Paso:
    """Un paso del procedimiento mostrado al estudiante."""

    titulo: str
    explicacion: str = ""
    # Cada fórmula se guarda como (latex, texto_unicode).
    formulas: list = field(default_factory=list)
    tipo: str = "info"  # info | integral | resultado | advertencia | verificacion


@dataclass
class Especificacion:
    """Descripción completa del ejercicio a resolver.

    `capas[0]` es la integral más externa y `capas[-1]` la más interna,
    de modo que la escritura natural ``\\int_a^b \\int_c^d f dy dx`` produce
    capas = [x: a..b, y: c..d].
    """

    capas: list
    integrando: sp.Expr
    sistema: str = "cartesiano"  # cartesiano | polar | cilindrico | esferico | general
    tipo_calculo: str = "integral"  # integral | area | volumen
    descripcion: str = ""
    texto_original: str = ""
    advertencias: list = field(default_factory=list)
    # Información extra para sólidos (superficie superior/inferior, etc.)
    info_volumen: dict = field(default_factory=dict)

    def __post_init__(self):
        # Normaliza los símbolos: si el integrando o los límites contienen un
        # símbolo con el mismo nombre que una variable de integración pero con
        # supuestos distintos (p. ej. creado por ``sympify`` a partir de texto),
        # se sustituye por el símbolo real de la capa. Sin esto, ``integrate``
        # trataría ese símbolo como una constante ajena a la variable.
        self.integrando = sp.sympify(self.integrando)
        canonicos = {c.variable.name: c.variable for c in self.capas}
        if not canonicos:
            return

        def _normalizar(expr):
            mapa = {
                s: canonicos[s.name]
                for s in expr.free_symbols
                if s.name in canonicos and s != canonicos[s.name]
            }
            return expr.subs(mapa) if mapa else expr

        self.integrando = _normalizar(self.integrando)
        for capa in self.capas:
            capa.inferior = _normalizar(capa.inferior)
            capa.superior = _normalizar(capa.superior)

    @property
    def dimension(self) -> int:
        return len(self.capas)

    @property
    def variables(self) -> list:
        return [c.variable for c in self.capas]


@dataclass
class Solucion:
    """Resultado completo de resolver una especificación."""

    especificacion: Especificacion
    pasos: list
    resultado: Optional[sp.Expr]
    resultado_decimal: Optional[float]
    exacto: bool
    metodo: str  # "simbolico" | "simbolico (funcion especial)" | "numerico"
    verificacion: dict = field(default_factory=dict)
    advertencias: list = field(default_factory=list)
    formulas_empleadas: list = field(default_factory=list)
    usa_funciones_especiales: bool = False
