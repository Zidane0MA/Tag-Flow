# Iniciar backend Flask en un nuevo proceso
$backendPath = $PSScriptRoot
Start-Process -FilePath "python" -ArgumentList "app.py" -WorkingDirectory $backendPath -WindowStyle Normal

# Esperar 5 segundos para que el backend arranque
Start-Sleep -Seconds 5

# Cambiar al directorio del frontend
Set-Location -Path (Join-Path $PSScriptRoot "tag-flow-modern-ui-final")

# Abrir el navegador
Start-Process "http://localhost:5173"

# Iniciar el servidor de desarrollo
npm run dev

# Mantener la ventana abierta
Read-Host -Prompt "Presiona Enter para salir"