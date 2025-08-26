@echo off
REM Iniciar backend Flask en una nueva ventana
start "Backend" cmd /k "cd /d %~dp0 && python app.py"
REM Esperar 5 segundos para que el backend arranque
timeout /t 5 /nobreak > nul
cd /d %~dp0\tag-flow-modern-ui-final
start http://localhost:5173
npm run dev
pause
