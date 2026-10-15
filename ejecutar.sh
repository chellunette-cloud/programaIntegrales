#!/usr/bin/env bash
# Ejecuta la aplicación del Resolutor de Integrales Múltiples.
cd "$(dirname "$0")" || exit 1
python -m streamlit run app.py
