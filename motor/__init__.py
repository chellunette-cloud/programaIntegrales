# -*- coding: utf-8 -*-
"""Motor matemático para integrales múltiples (doble/triple), coordenadas
polares/cilíndricas/esféricas y cálculo de áreas y volúmenes."""

from .especificacion import Capa, Especificacion, Paso, Solucion  # noqa: F401
from .parser import ErrorEntrada, parsear_ejercicio  # noqa: F401
from .motor_integracion import resolver  # noqa: F401

__all__ = [
    "Capa",
    "Especificacion",
    "Paso",
    "Solucion",
    "ErrorEntrada",
    "parsear_ejercicio",
    "resolver",
]
