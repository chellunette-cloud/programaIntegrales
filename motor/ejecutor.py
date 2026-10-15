# -*- coding: utf-8 -*-
"""Ejecución con límite de tiempo.

Algunas integrales simbólicas pueden tardar mucho o colgarse. Para que la
aplicación nunca se quede bloqueada, las operaciones simbólicas se ejecutan en
un hilo demonio con un tiempo máximo. Si se agota, se avisa y se recurre al
método numérico.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Tuple

# Estado: "ok" | "timeout" | "error"
Resultado = Tuple[str, Any]


def ejecutar_con_timeout(
    func: Callable, args: tuple = (), kwargs: dict | None = None, timeout: float = 30.0
) -> Resultado:
    """Ejecuta ``func(*args, **kwargs)`` con un tiempo máximo.

    Devuelve una tupla ``(estado, valor)`` donde ``estado`` es:
      * ``"ok"`` con el valor devuelto,
      * ``"timeout"`` si se superó ``timeout`` segundos,
      * ``"error"`` con la excepción producida.
    """
    caja: dict = {}

    def objetivo():
        try:
            caja["valor"] = func(*args, **(kwargs or {}))
        except Exception as exc:  # noqa: BLE001 - se reporta al llamador
            caja["error"] = exc

    hilo = threading.Thread(target=objetivo, daemon=True)
    hilo.start()
    hilo.join(timeout)
    if hilo.is_alive():
        return ("timeout", None)
    if "error" in caja:
        return ("error", caja["error"])
    return ("ok", caja.get("valor"))
