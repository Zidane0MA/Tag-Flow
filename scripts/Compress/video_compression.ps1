# Video Compression Script - PowerShell
# Comprime masivamente videos MP4 usando FFmpeg con configuración optimizada
# Autor: Tag-Flow System
# Fecha: $(Get-Date -Format "yyyy-MM-dd")

param(
    [Parameter(Mandatory=$false)]
    [string]$InputPath,
    
    [Parameter(Mandatory=$false)]
    [string]$FFmpegPath,
    
    [Parameter(Mandatory=$false)]
    [switch]$UseGPU,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("auto", "nvenc", "qsv", "amf", "cpu")]
    [string]$Encoder = "auto",
    
    [Parameter(Mandatory=$false)]
    [switch]$ReplaceOriginal
)

# Configurar codificación UTF-8 para manejar caracteres chinos
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

# Variable global para rastrear procesos FFmpeg activos
$Global:ActiveFFmpegProcesses = @()

# Función para manejar interrupciones (Ctrl+C)
function Stop-AllFFmpegProcesses {
    if ($Global:ActiveFFmpegProcesses.Count -gt 0) {
        Write-ColorOutput "🛑 Deteniendo procesos FFmpeg activos..." "Yellow"
        foreach ($process in $Global:ActiveFFmpegProcesses) {
            try {
                if (-not $process.HasExited) {
                    $process.Kill()
                    Write-ColorOutput "   ✅ Proceso FFmpeg $($process.Id) terminado" "Green"
                }
            }
            catch {
                Write-ColorOutput "   ⚠️  No se pudo terminar el proceso $($process.Id): $($_.Exception.Message)" "Yellow"
            }
        }
        $Global:ActiveFFmpegProcesses.Clear()
    }
}

# Registrar manejador de eventos para Ctrl+C
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-AllFFmpegProcesses
} | Out-Null

# También capturar Ctrl+C durante la ejecución  
$null = Register-ObjectEvent -InputObject ([System.Console]) -EventName "CancelKeyPress" -Action {
    Write-Host "`n🛑 Interrupción detectada. Limpiando procesos..." -ForegroundColor Yellow
    Stop-AllFFmpegProcesses
    [System.Environment]::Exit(1)
}

# Asignar valores por defecto
if ([string]::IsNullOrEmpty($InputPath)) {
    $InputPath = 'D:\4K All\Patreon\许流年 - @u93938365\'
}

if ([string]::IsNullOrEmpty($FFmpegPath)) {
    $FFmpegPath = 'C:\ffmpeg\ffmpeg.exe'
}

# Configuración de colores para la consola
$Host.UI.RawUI.WindowTitle = "Video Compression Tool - Tag-Flow"

function Write-ColorOutput {
    param([string]$Text, [string]$ForegroundColor = "White")
    Write-Host $Text -ForegroundColor $ForegroundColor
}

function Write-Header {
    Clear-Host
    Write-ColorOutput "╔══════════════════════════════════════════════════════════════════════════════╗" "Cyan"
    Write-ColorOutput "║                          VIDEO COMPRESSION TOOL                              ║" "Cyan"
    Write-ColorOutput "║                              Tag-Flow System                                 ║" "Cyan"
    Write-ColorOutput "╚══════════════════════════════════════════════════════════════════════════════╝" "Cyan"
    Write-Host ""
}

function Test-GPUEncoders {
    Write-ColorOutput "🔍 Detectando encoders GPU disponibles..." "Yellow"
    
    $availableEncoders = @()
    
    try {
        # Obtener lista de encoders disponibles
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = $FFmpegPath
        $processInfo.Arguments = "-encoders"
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processInfo
        $process.Start() | Out-Null
        $output = $process.StandardOutput.ReadToEnd()
        $process.WaitForExit()
        
        # Verificar encoders GPU específicos
        $nvencDetected = @()
        if ($output -match "h264_nvenc.*NVIDIA") {
            $nvencDetected += "h264"
            Write-ColorOutput "   ✅ NVIDIA NVENC H.264 detectado" "Green"
        }
        if ($output -match "hevc_nvenc.*NVIDIA") {
            $nvencDetected += "hevc"
            Write-ColorOutput "   ✅ NVIDIA NVENC HEVC detectado" "Green"
        }
        if ($nvencDetected.Count -gt 0) {
            $availableEncoders += "nvenc"
        }
        
        if ($output -match "h264_qsv.*Intel") {
            $availableEncoders += "qsv"
            Write-ColorOutput "   ✅ Intel Quick Sync detectado" "Green"
        }
        
        if ($output -match "h264_amf.*AMD") {
            $availableEncoders += "amf"
            Write-ColorOutput "   ✅ AMD AMF detectado" "Green"
        }
        
        if ($availableEncoders.Count -eq 0) {
            Write-ColorOutput "   ⚠️  No se detectaron encoders GPU, usando CPU" "Yellow"
            $availableEncoders += "cpu"
        }
        
    }
    catch {
        Write-ColorOutput "   ❌ Error detectando encoders GPU: $($_.Exception.Message)" "Red"
        Write-ColorOutput "   ⚠️  Usando encoder CPU por defecto" "Yellow"
        $availableEncoders += "cpu"
    }
    
    # Almacenar información de soporte HEVC para NVENC
    if ($nvencDetected -contains "hevc") {
        $Global:NVENCSupportsHEVC = $true
    } else {
        $Global:NVENCSupportsHEVC = $false
    }
    
    return $availableEncoders
}

function Get-OptimalEncoder {
    param([string[]]$AvailableEncoders)
    
    if ($Encoder -and $Encoder -ne "auto") {
        if ($Encoder -eq "cpu") {
            return @{ Name = "cpu"; VideoCodec = "libx264"; AudioCodec = "aac" }
        }
        elseif ($AvailableEncoders -contains $Encoder) {
            switch ($Encoder) {
                "nvenc" { return @{ Name = "nvenc"; VideoCodec = "h264_nvenc"; AudioCodec = "aac" } }
                "qsv"   { return @{ Name = "qsv"; VideoCodec = "h264_qsv"; AudioCodec = "aac" } }
                "amf"   { return @{ Name = "amf"; VideoCodec = "h264_amf"; AudioCodec = "aac" } }
            }
        }
        else {
            Write-ColorOutput "⚠️  Encoder '$Encoder' no disponible, usando auto-detección" "Yellow"
        }
    }
    
    # Auto-selección (prioridad: NVENC > QSV > AMF > CPU)
    if ($AvailableEncoders -contains "nvenc") {
        return @{ Name = "nvenc"; VideoCodec = "h264_nvenc"; AudioCodec = "aac" }
    }
    elseif ($AvailableEncoders -contains "qsv") {
        return @{ Name = "qsv"; VideoCodec = "h264_qsv"; AudioCodec = "aac" }
    }
    elseif ($AvailableEncoders -contains "amf") {
        return @{ Name = "amf"; VideoCodec = "h264_amf"; AudioCodec = "aac" }
    }
    else {
        return @{ Name = "cpu"; VideoCodec = "libx264"; AudioCodec = "aac" }
    }
}

function Get-SmartEncoder {
    param(
        [hashtable]$VideoAnalysis,
        [string[]]$AvailableEncoders
    )
    
    # Si el usuario forzó un encoder específico, respetarlo
    if ($Encoder -and $Encoder -ne "auto") {
        return Get-OptimalEncoder $AvailableEncoders
    }
    
    # Lógica inteligente basada en el análisis del video
    Write-ColorOutput "🧠 Selección inteligente de encoder:" "Cyan"
    Write-ColorOutput "   Codec original: $($VideoAnalysis.Codec)" "Gray"
    Write-ColorOutput "   Profundidad: $($VideoAnalysis.BitDepth)-bit" "Gray"
    Write-ColorOutput "   Resolución: $($VideoAnalysis.Width)x$($VideoAnalysis.Height)" "Gray"
    
    # Para videos 10-bit
    if ($VideoAnalysis.BitDepth -eq 10) {
        # Prioridad: NVENC HEVC > libx265 (CPU) > NVENC H.264 8-bit
        if ($AvailableEncoders -contains "nvenc" -and $Global:NVENCSupportsHEVC) {
            Write-ColorOutput "   🎯 10-bit detectado → NVENC HEVC" "Green"
            return @{ Name = "nvenc-hevc"; VideoCodec = "hevc_nvenc"; AudioCodec = "aac"; BitDepth = 10 }
        }
        else {
            Write-ColorOutput "   🎯 10-bit detectado → CPU libx265 (NVENC no soporta 10-bit H.264)" "Yellow"
            return @{ Name = "cpu-hevc"; VideoCodec = "libx265"; AudioCodec = "aac"; BitDepth = 10 }
        }
    }
    
    # Para videos 8-bit estándar
    if ($AvailableEncoders -contains "nvenc") {
        Write-ColorOutput "   🎯 8-bit detectado → NVENC H.264" "Green"
        return @{ Name = "nvenc"; VideoCodec = "h264_nvenc"; AudioCodec = "aac"; BitDepth = 8 }
    }
    elseif ($AvailableEncoders -contains "qsv") {
        Write-ColorOutput "   🎯 Fallback → Intel QSV" "Green"
        return @{ Name = "qsv"; VideoCodec = "h264_qsv"; AudioCodec = "aac"; BitDepth = 8 }
    }
    elseif ($AvailableEncoders -contains "amf") {
        Write-ColorOutput "   🎯 Fallback → AMD AMF" "Green"
        return @{ Name = "amf"; VideoCodec = "h264_amf"; AudioCodec = "aac"; BitDepth = 8 }
    }
    else {
        Write-ColorOutput "   🎯 Fallback → CPU libx264" "Yellow"
        return @{ Name = "cpu"; VideoCodec = "libx264"; AudioCodec = "aac"; BitDepth = 8 }
    }
}

function Test-FFmpegInstalled {
    Write-ColorOutput "🔍 Verificando FFmpeg en: $FFmpegPath" "Yellow"
    
    try {
        # Verificar si el archivo existe
        if (-not (Test-Path $FFmpegPath)) {
            Write-ColorOutput "❌ ERROR: No se encontró FFmpeg en la ruta especificada: $FFmpegPath" "Red"
            Write-ColorOutput "   Verifica que la ruta sea correcta" "Yellow"
            return $false
        }
        
        # Intentar ejecutar FFmpeg
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = $FFmpegPath
        $processInfo.Arguments = "-version"
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processInfo
        $process.Start() | Out-Null
        $process.WaitForExit(5000)  # Esperar máximo 5 segundos
        
        if ($process.ExitCode -eq 0) {
            Write-ColorOutput "✅ FFmpeg encontrado y funcionando correctamente" "Green"
            return $true
        } else {
            Write-ColorOutput "❌ ERROR: FFmpeg no responde correctamente (Exit code: $($process.ExitCode))" "Red"
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ ERROR: No se puede ejecutar FFmpeg: $($_.Exception.Message)" "Red"
        Write-ColorOutput "   Descarga FFmpeg desde: https://ffmpeg.org/download.html" "Yellow"
        Write-ColorOutput "   O especifica la ruta completa con -FFmpegPath" "Yellow"
        return $false
    }
}

function Get-FileSizeFormatted {
    param([long]$SizeInBytes)
    
    if ($SizeInBytes -ge 1GB) {
        return "{0:N2} GB" -f ($SizeInBytes / 1GB)
    } elseif ($SizeInBytes -ge 1MB) {
        return "{0:N2} MB" -f ($SizeInBytes / 1MB)
    } elseif ($SizeInBytes -ge 1KB) {
        return "{0:N2} KB" -f ($SizeInBytes / 1KB)
    } else {
        return "{0} bytes" -f $SizeInBytes
    }
}

function Get-CompressionRatio {
    param([long]$OriginalSize, [long]$CompressedSize)
    
    if ($OriginalSize -eq 0) { return "0%" }
    
    $reduction = (($OriginalSize - $CompressedSize) / $OriginalSize) * 100
    return "{0:N1}%" -f $reduction
}

function Analyze-VideoWithFFprobe {
    param([string]$VideoPath)
    
    try {
        # Obtener ffprobe path (mismo directorio que ffmpeg)
        $ffprobePath = $FFmpegPath -replace "ffmpeg\.exe$", "ffprobe.exe"
        
        if (-not (Test-Path $ffprobePath)) {
            Write-ColorOutput "⚠️  ffprobe no encontrado, usando valores por defecto" "Yellow"
            return @{
                Success = $false
                Bitrate = 5000
                Codec = "h264"
                BitDepth = 8
                Width = 1920
                Height = 1080
                FrameRate = 30
                Duration = 180
            }
        }
        
        # Ejecutar ffprobe para obtener metadata JSON
        $ffprobeArgs = @(
            "-v", "quiet"
            "-print_format", "json"
            "-show_format"
            "-show_streams"
            "`"$VideoPath`""
        )
        
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = $ffprobePath
        $processInfo.Arguments = [string]::Join(" ", $ffprobeArgs)
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processInfo
        $process.Start() | Out-Null
        $output = $process.StandardOutput.ReadToEnd()
        $process.WaitForExit()
        
        if ($process.ExitCode -ne 0) {
            Write-ColorOutput "❌ Error ejecutando ffprobe" "Red"
            return @{ Success = $false }
        }
        
        # Parsear JSON
        $metadata = $output | ConvertFrom-Json
        
        # Extraer stream de video (primer stream de video encontrado)
        $videoStream = $metadata.streams | Where-Object { $_.codec_type -eq "video" } | Select-Object -First 1
        
        if (-not $videoStream) {
            Write-ColorOutput "❌ No se encontró stream de video" "Red"
            return @{ Success = $false }
        }
        
        # Extraer datos
        $bitrate = [int]($metadata.format.bit_rate -as [int]) / 1000  # Convertir a kbps
        $codec = $videoStream.codec_name
        $pixFormat = $videoStream.pix_fmt
        $width = [int]$videoStream.width
        $height = [int]$videoStream.height
        $frameRate = if ($videoStream.r_frame_rate) { 
            $parts = $videoStream.r_frame_rate -split '/'
            [math]::Round([double]$parts[0] / [double]$parts[1], 2)
        } else { 30 }
        $duration = [math]::Round([double]$metadata.format.duration, 2)
        
        # Detectar profundidad de bits
        $bitDepth = 8  # Por defecto
        if ($pixFormat -match "10le|10be|p010") {
            $bitDepth = 10
        }
        
        Write-ColorOutput "✅ Análisis completado:" "Green"
        Write-ColorOutput "   📊 Bitrate: $bitrate kbps" "Gray"
        Write-ColorOutput "   🎞️ Codec: $codec" "Gray"
        Write-ColorOutput "   🎨 Profundidad: $bitDepth-bit ($pixFormat)" "Gray"
        Write-ColorOutput "   📐 Resolución: ${width}x${height}" "Gray"
        Write-ColorOutput "   ⏱️ Duración: $duration s" "Gray"
        
        return @{
            Success = $true
            Bitrate = $bitrate
            Codec = $codec
            BitDepth = $bitDepth
            Width = $width
            Height = $height
            FrameRate = $frameRate
            Duration = $duration
            PixFormat = $pixFormat
        }
    }
    catch {
        Write-ColorOutput "❌ Error durante análisis: $($_.Exception.Message)" "Red"
        return @{ Success = $false }
    }
}

function Calculate-AdaptiveCRF {
    param(
        [int]$OriginalBitrate,
        [string]$OriginalCodec,
        [int]$BitDepth,
        [int]$Width,
        [int]$Height
    )
    
    # Fórmula base mejorada: CRF = 23 + (Max(0, (BitrateMeta - BitrateOriginal)) / Divisor)
    $bitrateMeta = 3000  # Bitrate objetivo para calidad buena
    $baseCRF = 23
    $bitrateAdjustment = [math]::Max(0, ($bitrateMeta - $OriginalBitrate)) / 250
    $crf = $baseCRF + $bitrateAdjustment
    
    # Ajustes por características del video
    $adjustments = @{
        "hevc" = 3    # HEVC es más eficiente, necesita CRF más alto
        "h265" = 3
        "10bit" = -1  # 10-bit merece más calidad
        "4k" = 1      # Resolución 4K necesita más bitrate
    }
    
    if ($OriginalCodec -match "hevc|h265") {
        $crf += $adjustments["hevc"]
        Write-ColorOutput "   🎯 Ajuste HEVC: +$($adjustments['hevc'])" "Gray"
    }
    
    if ($BitDepth -eq 10) {
        $crf += $adjustments["10bit"]
        Write-ColorOutput "   🎯 Ajuste 10-bit: $($adjustments['10bit'])" "Gray"
    }
    
    if (($Width * $Height) -gt (1920 * 1080)) {
        $crf += $adjustments["4k"]
        Write-ColorOutput "   🎯 Ajuste >1080p: +$($adjustments['4k'])" "Gray"
    }
    
    # Límites de seguridad
    $crf = [math]::Max(18, [math]::Min(32, [math]::Round($crf)))
    
    Write-ColorOutput "🎯 CRF calculado: $crf (bitrate original: $OriginalBitrate kbps)" "Cyan"
    
    return $crf
}

function Estimate-Saving {
    param($VideoAnalysis, $FileSizeBytes)
    
    # Estimación basada en bitrate original vs bitrate meta
    $bitrateMeta = 2000  # Bitrate objetivo para compresión
    $originalBitrate = $VideoAnalysis.Bitrate
    
    if ($originalBitrate -le $bitrateMeta) {
        return 0  # No hay ahorro posible
    }
    
    $saving = (($originalBitrate - $bitrateMeta) / $originalBitrate) * 100
    return [math]::Min(70, [math]::Max(0, $saving))
}

function Should-SkipVideo {
    param(
        [hashtable]$VideoAnalysis,
        [long]$FileSizeBytes
    )
    
    $fileSizeMB = $FileSizeBytes / 1MB
    $bitrate = $VideoAnalysis.Bitrate
    
    # Umbrales configurables
    $thresholds = @{
        MinSizeMB = 50
        MinBitrateKbps = 1000
        MinHevcBitrateKbps = 2000
        MinDurationSeconds = 30
        MinEstimatedSaving = 15
    }
    
    # 1. Tamaño muy pequeño
    if ($fileSizeMB -lt $thresholds.MinSizeMB) {
        Write-ColorOutput "⏭️  Saltando: Archivo muy pequeño ($([math]::Round($fileSizeMB, 1)) MB < $($thresholds.MinSizeMB) MB)" "Yellow"
        return $true
    }
    
    # 2. Bitrate muy bajo
    if ($bitrate -lt $thresholds.MinBitrateKbps) {
        Write-ColorOutput "⏭️  Saltando: Bitrate muy bajo ($bitrate kbps < $($thresholds.MinBitrateKbps) kbps)" "Yellow"
        return $true
    }
    
    # 3. HEVC ya optimizado
    if ($VideoAnalysis.Codec -match "hevc|h265" -and $bitrate -lt $thresholds.MinHevcBitrateKbps) {
        Write-ColorOutput "⏭️  Saltando: HEVC ya optimizado ($bitrate kbps < $($thresholds.MinHevcBitrateKbps) kbps)" "Yellow"
        return $true
    }
    
    # 4. Duración muy corta
    if ($VideoAnalysis.Duration -lt $thresholds.MinDurationSeconds) {
        Write-ColorOutput "⏭️  Saltando: Video muy corto ($($VideoAnalysis.Duration)s < $($thresholds.MinDurationSeconds)s)" "Yellow"
        return $true
    }
    
    # 5. Estimar ahorro potencial
    $estimatedSavingPercent = Estimate-Saving $VideoAnalysis $FileSizeBytes
    if ($estimatedSavingPercent -lt $thresholds.MinEstimatedSaving) {
        Write-ColorOutput "⏭️  Saltando: Ahorro estimado muy bajo ($([math]::Round($estimatedSavingPercent, 1))% < $($thresholds.MinEstimatedSaving)%)" "Yellow"
        return $true
    }
    
    Write-ColorOutput "✅ Video será procesado (ahorro estimado: $([math]::Round($estimatedSavingPercent, 1))%)" "Green"
    return $false
}

function Compress-Video {
    param(
        [string]$InputFile,
        [hashtable]$EncoderConfig,
        [int]$CRF = 23  # Nuevo parámetro CRF con valor por defecto
    )
    
    try {
        # Validar que el archivo existe usando múltiples métodos
        $fileExists = $false
        
        # Método 1: Test-Path estándar
        if (Test-Path $InputFile) {
            $fileExists = $true
        }
        # Método 2: Test-Path con -LiteralPath
        elseif (Test-Path -LiteralPath $InputFile) {
            $fileExists = $true
        }
        # Método 3: System.IO.File.Exists
        elseif ([System.IO.File]::Exists($InputFile)) {
            $fileExists = $true
        }
        
        if (-not $fileExists) {
            Write-ColorOutput "❌ El archivo no existe o no es accesible: $InputFile" "Red"
            # Intentar listar el directorio para debug
            $parentDir = Split-Path $InputFile -Parent
            if (Test-Path $parentDir) {
                Write-ColorOutput "📁 Archivos en directorio padre:" "Yellow"
                try {
                    $filesInDir = Get-ChildItem $parentDir -Filter "*.mp4" | Select-Object -First 3
                    foreach ($f in $filesInDir) {
                        Write-ColorOutput "   • $($f.Name)" "Gray"
                    }
                } catch {
                    Write-ColorOutput "   Error listando directorio: $($_.Exception.Message)" "Gray"
                }
            }
            return @{ Success = $false }
        }
        
        # Obtener información del archivo usando diferentes métodos para compatibilidad
        $fileInfo = $null
        try {
            $fileInfo = Get-Item -LiteralPath $InputFile -ErrorAction Stop
        }
        catch {
            # Método alternativo usando System.IO
            $fileInfo = New-Object System.IO.FileInfo($InputFile)
        }
        
        if (-not $fileInfo) {
            Write-ColorOutput "❌ No se puede obtener información del archivo: $InputFile" "Red"
            return @{ Success = $false }
        }
        
        $directory = $fileInfo.Directory.FullName
        $baseName = $fileInfo.BaseName
        
        # Validar que tenemos valores válidos
        if ([string]::IsNullOrEmpty($directory) -or [string]::IsNullOrEmpty($baseName)) {
            Write-ColorOutput "❌ Error procesando ruta del archivo: $InputFile" "Red"
            Write-ColorOutput "   Directorio: '$directory', BaseName: '$baseName'" "Gray"
            return @{ Success = $false }
        }
        
        $outputFile = Join-Path $directory "$baseName compress.mp4"
    }
    catch {
        Write-ColorOutput "❌ Error procesando archivo: $($_.Exception.Message)" "Red"
        return @{ Success = $false }
    }
    
    # Verificar si ya existe la versión comprimida
    if (Test-Path $outputFile) {
        Write-ColorOutput "⏭️  Saltando: $($fileInfo.Name) (ya comprimido)" "Yellow"
        return $null
    }
    
    Write-ColorOutput "🎬 Procesando: $($fileInfo.Name)" "White"
    Write-ColorOutput "   Tamaño original: $(Get-FileSizeFormatted $fileInfo.Length)" "Gray"
    Write-ColorOutput "   🚀 Encoder: $($EncoderConfig.Name.ToUpper())" "Cyan"
    
    # Configurar argumentos según el encoder seleccionado
    $ffmpegArgs = @(
        "-i", "`"$InputFile`""
        "-c:v", $EncoderConfig.VideoCodec
        "-c:a", $EncoderConfig.AudioCodec
        "-b:a", "128k"
        "-y"  # Sobrescribir sin preguntar
        "`"$outputFile`""
    )
    
    # Configuración específica por encoder
    switch ($EncoderConfig.Name) {
        "cpu" {
            # CPU: usar CRF calculado adaptativo
            $ffmpegArgs = @(
                "-i", "`"$InputFile`""
                "-c:v", $EncoderConfig.VideoCodec
                "-crf", $CRF.ToString()
                "-preset", "medium"
                "-c:a", $EncoderConfig.AudioCodec
                "-b:a", "128k"
                "-y"
                "`"$outputFile`""
            )
        }
        "cpu-hevc" {
            # CPU HEVC para videos 10-bit
            $ffmpegArgs = @(
                "-i", "`"$InputFile`""
                "-c:v", $EncoderConfig.VideoCodec
                "-crf", $CRF.ToString()
                "-preset", "medium"
                "-c:a", $EncoderConfig.AudioCodec
                "-b:a", "128k"
                "-y"
                "`"$outputFile`""
            )
        }
        "nvenc" {
            # NVIDIA H.264: usar CQ calculado adaptativo
            $ffmpegArgs = @(
                "-i", "`"$InputFile`""
                "-c:v", $EncoderConfig.VideoCodec
                "-cq", $CRF.ToString()
                "-preset", "medium"
                "-c:a", $EncoderConfig.AudioCodec
                "-b:a", "128k"
                "-y"
                "`"$outputFile`""
            )
        }
        "nvenc-hevc" {
            # NVIDIA HEVC para videos 10-bit
            $ffmpegArgs = @(
                "-i", "`"$InputFile`""
                "-c:v", $EncoderConfig.VideoCodec
                "-cq", $CRF.ToString()
                "-preset", "medium"
                "-c:a", $EncoderConfig.AudioCodec
                "-b:a", "128k"
                "-y"
                "`"$outputFile`""
            )
        }
        "qsv" {
            # Intel QSV: usar global_quality calculado
            $ffmpegArgs = @(
                "-i", "`"$InputFile`""
                "-c:v", $EncoderConfig.VideoCodec
                "-global_quality", $CRF.ToString()
                "-c:a", $EncoderConfig.AudioCodec
                "-b:a", "128k"
                "-y"
                "`"$outputFile`""
            )
        }
        "amf" {
            # AMD AMF: usar CRF calculado
            $ffmpegArgs = @(
                "-i", "`"$InputFile`""
                "-c:v", $EncoderConfig.VideoCodec
                "-crf", $CRF.ToString()
                "-c:a", $EncoderConfig.AudioCodec
                "-b:a", "128k"
                "-y"
                "`"$outputFile`""
            )
        }
    }
    
    
    $startTime = Get-Date
    
    try {
        # Ejecutar FFmpeg y capturar salida
        $process = Start-Process -FilePath $FFmpegPath -ArgumentList $ffmpegArgs -NoNewWindow -PassThru -RedirectStandardError "error.tmp"
        
        # Registrar el proceso para poder terminarlo si es necesario
        $Global:ActiveFFmpegProcesses += $process
        
        # Esperar a que termine el proceso
        $process.WaitForExit()
        
        # Remover el proceso de la lista de activos
        $Global:ActiveFFmpegProcesses = $Global:ActiveFFmpegProcesses | Where-Object { $_.Id -ne $process.Id }
        
        # Verificar resultado con múltiples métodos
        $outputExists = $false
        if (Test-Path $outputFile) {
            $outputExists = $true
        } elseif ([System.IO.File]::Exists($outputFile)) {
            $outputExists = $true
        }
        
        if ($process.ExitCode -eq 0 -and $outputExists) {
            $endTime = Get-Date
            $duration = $endTime - $startTime
            
            # Obtener información del archivo de salida
            $outputInfo = $null
            try {
                $outputInfo = Get-Item -LiteralPath $outputFile
            } catch {
                $outputInfo = New-Object System.IO.FileInfo($outputFile)
            }
            
            $compressionRatio = Get-CompressionRatio $fileInfo.Length $outputInfo.Length
            
            # Validación post-compresión: verificar que no haya reducción negativa
            if ($outputInfo.Length -ge $fileInfo.Length) {
                Write-ColorOutput "❌ Reducción negativa detectada, descartando archivo comprimido" "Red"
                Write-ColorOutput "   Original: $(Get-FileSizeFormatted $fileInfo.Length)" "Gray"
                Write-ColorOutput "   Comprimido: $(Get-FileSizeFormatted $outputInfo.Length)" "Gray"
                Write-ColorOutput "   El archivo original ya está optimizado" "Yellow"
                
                # Eliminar archivo comprimido ineficiente
                Remove-Item $outputFile -Force -ErrorAction SilentlyContinue
                
                return @{
                    Success = $false
                    Reason = "NegativeReduction"
                    OriginalSize = $fileInfo.Length
                    CompressedSize = $outputInfo.Length
                    Duration = $duration
                }
            }
            
            Write-ColorOutput "✅ Completado en $($duration.ToString('mm\:ss'))" "Green"
            Write-ColorOutput "   Tamaño comprimido: $(Get-FileSizeFormatted $outputInfo.Length)" "Green"
            Write-ColorOutput "   Reducción: $compressionRatio" "Green"
            
            return @{
                OriginalSize = $fileInfo.Length
                CompressedSize = $outputInfo.Length
                CompressionRatio = $compressionRatio
                Duration = $duration
                Success = $true
            }
        } else {
            Write-ColorOutput "❌ Error al comprimir el archivo" "Red"
            if (Test-Path "error.tmp") {
                $errorContent = Get-Content "error.tmp" -Raw
                Write-ColorOutput "   Error FFmpeg: $errorContent" "Red"
                Remove-Item "error.tmp" -ErrorAction SilentlyContinue
            }
            return @{ Success = $false }
        }
    }
    catch {
        Write-ColorOutput "❌ Excepción durante la compresión: $($_.Exception.Message)" "Red"
        
        # Limpiar proceso de la lista si hay error
        if ($process) {
            $Global:ActiveFFmpegProcesses = $Global:ActiveFFmpegProcesses | Where-Object { $_.Id -ne $process.Id }
        }
        
        return @{ Success = $false }
    }
    finally {
        # Limpiar archivos temporales
        if (Test-Path "error.tmp") {
            Remove-Item "error.tmp" -ErrorAction SilentlyContinue
        }
        
        # Asegurar que el proceso se limpia de la lista
        if ($process) {
            $Global:ActiveFFmpegProcesses = $Global:ActiveFFmpegProcesses | Where-Object { $_.Id -ne $process.Id }
        }
    }
}

# SCRIPT PRINCIPAL
Write-Header


# Verificar FFmpeg
if (-not (Test-FFmpegInstalled)) {
    Write-ColorOutput "Presiona cualquier tecla para salir..." "Yellow"
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Detectar y configurar encoder
Write-Host ""
$availableEncoders = Test-GPUEncoders
$selectedEncoder = Get-OptimalEncoder $availableEncoders

Write-ColorOutput "🎯 Encoder seleccionado: $($selectedEncoder.Name.ToUpper())" "Green"
Write-ColorOutput "   Video: $($selectedEncoder.VideoCodec)" "Gray"
Write-ColorOutput "   Audio: $($selectedEncoder.AudioCodec)" "Gray"
Write-Host ""

# Verificar directorio de entrada
Write-ColorOutput "🔍 Verificando directorio: $InputPath" "Yellow"

try {
    $pathExists = Test-Path -Path $InputPath -PathType Container
    if (-not $pathExists) {
        # Intentar con diferentes métodos de verificación para caracteres especiales
        $alternativePath = [System.IO.Path]::GetFullPath($InputPath)
        $pathExists = [System.IO.Directory]::Exists($alternativePath)
        
        if (-not $pathExists) {
            Write-ColorOutput "❌ ERROR: El directorio no existe o no es accesible: $InputPath" "Red"
            Write-ColorOutput "   Sugerencia: Verifica que la ruta sea correcta y que tengas permisos de acceso" "Yellow"
            Write-ColorOutput "Presiona cualquier tecla para salir..." "Yellow"
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            exit 1
        } else {
            $InputPath = $alternativePath
        }
    }
    Write-ColorOutput "✅ Directorio verificado correctamente" "Green"
}
catch {
    Write-ColorOutput "❌ ERROR: No se puede acceder al directorio: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Presiona cualquier tecla para salir..." "Yellow"
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""

# Buscar todos los archivos MP4 recursivamente
Write-ColorOutput "🔍 Buscando archivos MP4..." "Yellow"

try {
    # Usar múltiples métodos para encontrar archivos MP4, especialmente con nombres en chino
    $mp4Files = @()
    
    # Método 1: Get-ChildItem estándar
    $files1 = Get-ChildItem -Path $InputPath -Filter "*.mp4" -Recurse -ErrorAction SilentlyContinue
    if ($files1) { $mp4Files += $files1 }
    
    # Método 2: Búsqueda directa con System.IO
    $allFiles = [System.IO.Directory]::GetFiles($InputPath, "*.mp4", [System.IO.SearchOption]::AllDirectories)
    foreach ($file in $allFiles) {
        $fileInfo = New-Object System.IO.FileInfo $file
        if ($mp4Files.FullName -notcontains $fileInfo.FullName) {
            $mp4Files += $fileInfo
        }
    }
    
    # Filtrar archivos que ya están comprimidos
    $mp4Files = $mp4Files | Where-Object { 
        -not $_.Name.EndsWith(" compress.mp4") 
    } | Sort-Object FullName
    
    $totalFiles = $mp4Files.Count
    
    Write-ColorOutput "📊 Total de archivos MP4 encontrados: $totalFiles" "Green"
    
    if ($totalFiles -eq 0) {
        Write-ColorOutput "❌ No se encontraron archivos MP4 para procesar" "Red"
        Write-ColorOutput "   Verifica que el directorio contenga archivos .mp4" "Yellow"
        Write-ColorOutput "Presiona cualquier tecla para salir..." "Yellow"
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 0
    }
    
    # Mostrar algunos archivos encontrados como muestra
    Write-ColorOutput "📄 Archivos encontrados (muestra):" "Cyan"
    $sampleFiles = $mp4Files | Select-Object -First 3
    foreach ($file in $sampleFiles) {
        Write-ColorOutput "   • $($file.Name)" "Gray"
    }
    if ($totalFiles -gt 3) {
        Write-ColorOutput "   ... y $($totalFiles - 3) más" "Gray"
    }
}
catch {
    Write-ColorOutput "❌ ERROR durante la búsqueda de archivos: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Presiona cualquier tecla para salir..." "Yellow"
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""

# Mostrar confirmación
Write-ColorOutput "¿Deseas continuar con la compresión? (S/N): " "Yellow" -NoNewLine
$confirmation = Read-Host
if ($confirmation -notmatch '^[SsYy]') {
    Write-ColorOutput "Operación cancelada por el usuario" "Yellow"
    exit 0
}

Write-Host ""
Write-ColorOutput "🚀 Iniciando proceso de compresión..." "Green"
Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"

# Variables para estadísticas
$processedFiles = 0
$successfulCompressions = 0
$totalOriginalSize = 0
$totalCompressedSize = 0
$startTimeTotal = Get-Date

# Procesar cada archivo
foreach ($file in $mp4Files) {
    $processedFiles++
    
    Write-Host ""
    Write-ColorOutput "📹 [$processedFiles/$totalFiles] Procesando..." "Cyan"
    
    # Obtener la ruta del archivo de manera robusta
    $filePath = ""
    if ($file -is [System.IO.FileInfo]) {
        $filePath = $file.FullName
    } elseif ($file.FullName) {
        $filePath = $file.FullName
    } else {
        $filePath = $file.ToString()
    }
    
    # ========== NUEVO SISTEMA INTELIGENTE ==========
    
    # 1. ANÁLISIS DE VIDEO
    Write-ColorOutput "🔍 Analizando video..." "Yellow"
    $videoAnalysis = Analyze-VideoWithFFprobe $filePath
    if (-not $videoAnalysis.Success) {
        Write-ColorOutput "❌ No se pudo analizar el video, saltando..." "Red"
        continue
    }
    
    # 2. DECISIÓN DE SALTO BASADA EN UMBRALES
    if (Should-SkipVideo $videoAnalysis $file.Length) {
        continue
    }
    
    # 3. CÁLCULO DE CRF ADAPTATIVO
    $crfValue = Calculate-AdaptiveCRF -OriginalBitrate $videoAnalysis.Bitrate `
                                      -OriginalCodec $videoAnalysis.Codec `
                                      -BitDepth $videoAnalysis.BitDepth `
                                      -Width $videoAnalysis.Width `
                                      -Height $videoAnalysis.Height
    
    # 4. SELECCIÓN INTELIGENTE DE ENCODER
    $smartEncoder = Get-SmartEncoder -VideoAnalysis $videoAnalysis -AvailableEncoders $availableEncoders
    
    Write-ColorOutput "🎬 Configuración final:" "White"
    Write-ColorOutput "   Encoder: $($smartEncoder.Name) ($($smartEncoder.VideoCodec))" "Cyan"
    Write-ColorOutput "   CRF: $crfValue" "Cyan"
    
    # 5. COMPRESIÓN CON PARÁMETROS CALCULADOS
    $result = Compress-Video -InputFile $filePath -EncoderConfig $smartEncoder -CRF $crfValue
    
    # 6. PROCESAMIENTO DE RESULTADO
    if ($result -and $result.Success) {
        $successfulCompressions++
        $totalOriginalSize += $result.OriginalSize
        $totalCompressedSize += $result.CompressedSize
    } elseif ($result -and $result.Reason -eq "NegativeReduction") {
        Write-ColorOutput "⚠️  Archivo original mantenido (ya optimizado)" "Yellow"
        # No contar como fallo, es una decisión inteligente
    }
    
    # Pequeña pausa para evitar sobrecarga del sistema
    Start-Sleep -Milliseconds 100
}

$endTimeTotal = Get-Date
$totalDuration = $endTimeTotal - $startTimeTotal

# Mostrar estadísticas finales
Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
Write-ColorOutput "📊 RESUMEN FINAL" "Green"
Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
Write-Host ""
Write-ColorOutput "   Archivos procesados: $processedFiles" "White"
Write-ColorOutput "   Compresiones exitosas: $successfulCompressions" "Green"
Write-ColorOutput "   Compresiones fallidas: $($processedFiles - $successfulCompressions)" "Red"
Write-Host ""

if ($successfulCompressions -gt 0) {
    $totalCompressionRatio = Get-CompressionRatio $totalOriginalSize $totalCompressedSize
    $spaceSaved = $totalOriginalSize - $totalCompressedSize
    
    Write-ColorOutput "   Tamaño original total: $(Get-FileSizeFormatted $totalOriginalSize)" "White"
    Write-ColorOutput "   Tamaño comprimido total: $(Get-FileSizeFormatted $totalCompressedSize)" "Green"
    Write-ColorOutput "   Espacio ahorrado: $(Get-FileSizeFormatted $spaceSaved)" "Green"
    Write-ColorOutput "   Reducción promedio: $totalCompressionRatio" "Green"
}

Write-Host ""
Write-ColorOutput "   Tiempo total: $($totalDuration.ToString('hh\:mm\:ss'))" "Cyan"
Write-Host ""
Write-ColorOutput "🎉 Proceso completado exitosamente!" "Green"

# Limpiar cualquier proceso FFmpeg restante
Stop-AllFFmpegProcesses

Write-ColorOutput "Presiona cualquier tecla para salir..." "Yellow"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")