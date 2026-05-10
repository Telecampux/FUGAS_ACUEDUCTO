@echo off
title Ejecutor IANC H2O
setlocal

:: Cambiamos a la ruta correcta en el disco D
set "APP_PATH=D:\IANC_H2O\IANC_H2O"
set "APP_FILE=app.py"

:: El comando /d es vital para saltar de C: a D:
cd /d "%APP_PATH%"

:: Verificamos que el archivo exista
if not exist "%APP_FILE%" (
    echo [ERROR] No se encontro %APP_FILE% en %APP_PATH%
    pause
    exit /b
)

echo Iniciando aplicacion con Streamlit...
:: Usamos 'streamlit run' porque tu codigo usa 'st.markdown'
streamlit run "%APP_FILE%"

pause
endlocal