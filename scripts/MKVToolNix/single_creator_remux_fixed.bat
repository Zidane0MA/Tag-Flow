@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ==========================================
:: Script para procesar UN SOLO CREADOR
:: ==========================================

set "BASE_DIR=D:\4K All\X\&bookmarks"
set "MKVMERGE_PATH=C:\Program Files\MKVToolNix\mkvmerge.exe"

:: Solicitar nombre del creador
echo Directorio base: %BASE_DIR%
echo.
echo Creadores disponibles:
for /d %%d in ("%BASE_DIR%\*") do echo   - %%~nxd
echo.
set /p CREATOR_NAME="Introduce el nombre del creador: "

if "%CREATOR_NAME%"=="" (
    echo Error: Debes especificar un creador
    pause
    exit /b 1
)

set "CREATOR_DIR=%BASE_DIR%\%CREATOR_NAME%"

if not exist "%CREATOR_DIR%" (
    echo Error: No se encuentra el directorio del creador: %CREATOR_DIR%
    pause
    exit /b 1
)

echo.
echo Procesando creador: %CREATOR_NAME%
echo Directorio: %CREATOR_DIR%
echo.

:: Contar archivos
set /a TOTAL=0
for /r "%CREATOR_DIR%" %%f in (*.mp4) do set /a TOTAL+=1

if %TOTAL%==0 (
    echo No se encontraron archivos MP4 en este directorio
    pause
    exit /b 0
)

echo Encontrados %TOTAL% archivos MP4
set /p CONFIRM="Procesar estos archivos? (S/N): "
if /i not "%CONFIRM%"=="S" exit /b 0

echo.
echo Procesando...

set /a COUNT=0
for /r "%CREATOR_DIR%" %%f in (*.mp4) do (
    set /a COUNT+=1
    set "MP4_FILE=%%f"
    set "MKV_FILE=%%~dpnf.mkv"
    
    echo [!COUNT!/!TOTAL!] %%~nxf
    
    if not exist "!MKV_FILE!" (
        "%MKVMERGE_PATH%" -o "!MKV_FILE!" "!MP4_FILE!" >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            if exist "!MKV_FILE!" (
                del "!MP4_FILE!"
                echo   Completado
            ) else (
                echo   Error: MKV no creado
            )
        ) else (
            echo   Error en mkvmerge
        )
    ) else (
        echo   Ya existe, saltando
    )
)

echo.
echo Creador "%CREATOR_NAME%" procesado completamente
pause