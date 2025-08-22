@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ==========================================
:: Script de Remuxing MP4 a MKV usando MKVToolNix
:: Para videos de X (Twitter) con problemas de codificacion
:: ==========================================

:: Configuracion
set "SOURCE_DIR=D:\4K All\X\&bookmarks"
set "MKVMERGE_PATH=C:\Program Files\MKVToolNix\mkvmerge.exe"
set "LOG_FILE=%~dp0remux_log_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt"

:: Limpiar caracteres especiales del nombre del log
set "LOG_FILE=%LOG_FILE: =0%"

echo ==========================================
echo    REMUXING MP4 a MKV - Tag-Flow X Videos
echo ==========================================
echo.
echo Directorio fuente: D:\4K All\X\^&bookmarks
echo MKVMerge: %MKVMERGE_PATH%
echo Log: %LOG_FILE%
echo.

:: Verificar que MKVMerge existe
if not exist "%MKVMERGE_PATH%" (
    echo ERROR: No se encuentra MKVMerge en: %MKVMERGE_PATH%
    echo Por favor verifica la instalacion de MKVToolNix
    pause
    exit /b 1
)

:: Verificar que el directorio fuente existe
if not exist "%SOURCE_DIR%" (
    echo ERROR: No se encuentra el directorio fuente: %SOURCE_DIR%
    pause
    exit /b 1
)

:: Inicializar log
echo Inicio del proceso de remuxing: %date% %time% > "%LOG_FILE%"
echo Directorio fuente: D:\4K All\X\^&bookmarks >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

:: Contadores
set /a TOTAL_FILES=0
set /a PROCESSED_FILES=0
set /a SUCCESSFUL_FILES=0
set /a ERROR_FILES=0

:: Contar archivos MP4 primero
echo Contando archivos MP4...
for /r "%SOURCE_DIR%" %%f in (*.mp4) do (
    set /a TOTAL_FILES+=1
)

echo Encontrados %TOTAL_FILES% archivos MP4 para procesar
echo.

if %TOTAL_FILES%==0 (
    echo No se encontraron archivos MP4 en el directorio especificado.
    pause
    exit /b 0
)

:: Confirmar antes de proceder
echo ADVERTENCIA: Este script convertira %TOTAL_FILES% archivos MP4 a MKV
echo y eliminara los archivos MP4 originales.
echo.
set /p CONFIRM="Desea continuar? (S/N): "
if /i not "%CONFIRM%"=="S" (
    echo Operacion cancelada por el usuario.
    pause
    exit /b 0
)

echo.
echo Iniciando procesamiento...
echo ==========================================

:: Procesar cada archivo MP4
for /r "%SOURCE_DIR%" %%f in (*.mp4) do (
    set /a PROCESSED_FILES+=1
    set "MP4_FILE=%%f"
    set "MKV_FILE=%%~dpnf.mkv"
    
    :: Mostrar progreso
    echo.
    echo [!PROCESSED_FILES!/!TOTAL_FILES!] Procesando: %%~nxf
    echo Carpeta: %%~dpf
    
    :: Log del archivo actual
    echo [!PROCESSED_FILES!/!TOTAL_FILES!] Procesando: !MP4_FILE! >> "%LOG_FILE%"
    
    :: Verificar que el archivo MP4 existe y no esta en uso
    if exist "!MP4_FILE!" (
        :: Verificar que el MKV de destino no existe
        if exist "!MKV_FILE!" (
            echo   ADVERTENCIA: El archivo MKV ya existe, saltando...
            echo   SALTADO: !MKV_FILE! ya existe >> "%LOG_FILE%"
        ) else (
            :: Ejecutar mkvmerge
            echo   Ejecutando remuxing...
            "%MKVMERGE_PATH%" -o "!MKV_FILE!" "!MP4_FILE!" 2>nul
            
            :: Verificar si el proceso fue exitoso
            if !ERRORLEVEL! EQU 0 (
                :: Verificar que el archivo MKV se creo y tiene tamano > 0
                if exist "!MKV_FILE!" (
                    for %%s in ("!MKV_FILE!") do set "MKV_SIZE=%%~zs"
                    if !MKV_SIZE! GTR 0 (
                        echo   Remuxing exitoso
                        echo   Eliminando MP4 original...
                        del "!MP4_FILE!" 2>nul
                        if !ERRORLEVEL! EQU 0 (
                            echo   MP4 original eliminado
                            set /a SUCCESSFUL_FILES+=1
                            echo   EXITOSO: !MP4_FILE! -> !MKV_FILE! >> "%LOG_FILE%"
                        ) else (
                            echo   Error al eliminar MP4 original
                            echo   ERROR: No se pudo eliminar !MP4_FILE! >> "%LOG_FILE%"
                            set /a ERROR_FILES+=1
                        )
                    ) else (
                        echo   Error: MKV creado pero con tamano 0
                        del "!MKV_FILE!" 2>nul
                        echo   ERROR: MKV con tamano 0 - !MKV_FILE! >> "%LOG_FILE%"
                        set /a ERROR_FILES+=1
                    )
                ) else (
                    echo   Error: No se pudo crear el archivo MKV
                    echo   ERROR: No se creo !MKV_FILE! >> "%LOG_FILE%"
                    set /a ERROR_FILES+=1
                )
            ) else (
                echo   Error en mkvmerge (codigo: !ERRORLEVEL!)
                echo   ERROR: mkvmerge fallo para !MP4_FILE! (codigo: !ERRORLEVEL!) >> "%LOG_FILE%"
                set /a ERROR_FILES+=1
            )
        )
    ) else (
        echo   Error: Archivo MP4 no encontrado o inaccesible
        echo   ERROR: MP4 no encontrado - !MP4_FILE! >> "%LOG_FILE%"
        set /a ERROR_FILES+=1
    )
)

:: Resumen final
echo.
echo ==========================================
echo           RESUMEN DEL PROCESAMIENTO
echo ==========================================
echo Total de archivos encontrados: %TOTAL_FILES%
echo Archivos procesados exitosamente: %SUCCESSFUL_FILES%
echo Archivos con errores: %ERROR_FILES%
echo.

:: Log del resumen
echo. >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"
echo RESUMEN FINAL - %date% %time% >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"
echo Total de archivos encontrados: %TOTAL_FILES% >> "%LOG_FILE%"
echo Archivos procesados exitosamente: %SUCCESSFUL_FILES% >> "%LOG_FILE%"
echo Archivos con errores: %ERROR_FILES% >> "%LOG_FILE%"

if %ERROR_FILES% GTR 0 (
    echo ATENCION: %ERROR_FILES% archivos tuvieron errores
    echo Revisa el log para mas detalles: %LOG_FILE%
    echo ERROR: %ERROR_FILES% archivos fallaron >> "%LOG_FILE%"
) else (
    echo Todos los archivos se procesaron exitosamente
    echo EXITO: Todos los archivos procesados correctamente >> "%LOG_FILE%"
)

echo.
echo Log completo guardado en: %LOG_FILE%
echo.
pause