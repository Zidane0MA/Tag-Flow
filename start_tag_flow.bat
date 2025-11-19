@echo off
echo Iniciando Tag-Flow Backend y Frontend...

rem --- Backend Setup and Start ---
echo.
echo ===============================
echo Iniciando Backend...
echo ===============================

rem Check if virtual environment exists
if not exist "tag-flow-env" (
    echo Entorno virtual no encontrado. Creando uno nuevo...
    python -m venv tag-flow-env
    pause
)

rem Install Python dependencies
if not exist "tag-flow-env\.dependencies_installed" (
    echo Instalando dependencias de Python...
    call tag-flow-env\Scripts\activate.bat
    pip install -r requirements.txt
    type nul > tag-flow-env\.dependencies_installed
    pause
) else (
    echo Dependencias de Python ya instaladas.
    echo [Elimina tag-flow-env\.dependencies_installed para forzar reinstalacion]
    pause
)

echo Iniciando servidor Flask (Backend) en segundo plano...
call tag-flow-env\Scripts\activate.bat
start "Tag-Flow Backend" cmd /c "python app.py"
timeout /t 3 /nobreak > nul
echo Backend iniciado en segundo plano.
pause

rem --- Frontend Setup and Start ---
echo.
echo ===============================
echo Iniciando Frontend...
echo ===============================

rem Navigate to frontend directory
cd tag-flow-modern-ui-final
if errorlevel 1 (
    echo Error: No se pudo navegar al directorio del frontend.
    echo Asegurate que 'tag-flow-modern-ui-final' existe.
    pause
    exit /b 1
)

rem Install Node.js dependencies
if not exist "node_modules" (
    echo Instalando dependencias de Node.js...
    npm install
    pause
) else (
    echo Dependencias de Node.js ya instaladas.
    echo [Ejecuta npm install manualmente para actualizar]
    pause
)

echo Iniciando servidor de desarrollo de Vite (Frontend)...
npm run dev
pause

echo.
echo =========================================================================
echo Tag-Flow esta intentando iniciar. Revisa el output en esta ventana.
echo El backend deberia estar en http://127.0.0.1:5000
echo El frontend deberia estar en http://localhost:5173
echo =========================================================================
echo.
pause