@echo off
REM Ejecuta la aplicacion del Resolutor de Integrales Multiples.
cd /d "%~dp0"
python -m streamlit run app.py
pause
