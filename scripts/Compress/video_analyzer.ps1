# Video Analyzer Script - PowerShell
# Análisis completo de videos MP4 sin compresión para comparación y optimización
# Autor: Tag-Flow System
# Genera reportes JSON y HTML para análisis comparativo

param(
    [Parameter(Mandatory=$false)]
    [string]$InputPath,
    
    [Parameter(Mandatory=$false)]
    [string]$FFmpegPath,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputFormat = "both",  # json, html, both
    
    [Parameter(Mandatory=$false)]
    [string]$OutputFile = "video_analysis_report"
)

# Configurar codificación UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

# Asignar valores por defecto
if ([string]::IsNullOrEmpty($InputPath)) {
    $InputPath = 'D:\4K Video Downloader+\Liked videos\'
}

if ([string]::IsNullOrEmpty($FFmpegPath)) {
    $FFmpegPath = 'C:\ffmpeg\ffmpeg.exe'
}

# Configuración
$Host.UI.RawUI.WindowTitle = "Video Analyzer Tool - Tag-Flow"

function Write-ColorOutput {
    param([string]$Text, [string]$ForegroundColor = "White")
    Write-Host $Text -ForegroundColor $ForegroundColor
}

function Write-Header {
    Clear-Host
    Write-ColorOutput "╔══════════════════════════════════════════════════════════════════════════════╗" "Cyan"
    Write-ColorOutput "║                          VIDEO ANALYZER TOOL                                ║" "Cyan"
    Write-ColorOutput "║                            Tag-Flow System                                 ║" "Cyan"
    Write-ColorOutput "╚══════════════════════════════════════════════════════════════════════════════╝" "Cyan"
    Write-Host ""
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

function Analyze-VideoExtended {
    param([string]$VideoPath)
    
    $fileInfo = Get-Item -LiteralPath $VideoPath -ErrorAction SilentlyContinue
    if (-not $fileInfo) {
        $fileInfo = New-Object System.IO.FileInfo($VideoPath)
    }
    
    try {
        # Obtener ffprobe path
        $ffprobePath = $FFmpegPath -replace "ffmpeg\.exe$", "ffprobe.exe"
        
        if (-not (Test-Path $ffprobePath)) {
            return @{
                Success = $false
                Error = "ffprobe no encontrado"
                FileName = $fileInfo.Name
            }
        }
        
        # Ejecutar ffprobe para metadata completa
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
            return @{
                Success = $false
                Error = "Error ejecutando ffprobe"
                FileName = $fileInfo.Name
            }
        }
        
        # Parsear JSON
        $metadata = $output | ConvertFrom-Json
        
        # Extraer stream de video
        $videoStream = $metadata.streams | Where-Object { $_.codec_type -eq "video" } | Select-Object -First 1
        $audioStream = $metadata.streams | Where-Object { $_.codec_type -eq "audio" } | Select-Object -First 1
        
        if (-not $videoStream) {
            return @{
                Success = $false
                Error = "No se encontró stream de video"
                FileName = $fileInfo.Name
            }
        }
        
        # Extraer datos básicos
        $bitrate = [int]($metadata.format.bit_rate -as [int]) / 1000  # kbps
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
        $bitDepth = 8
        if ($pixFormat -match "10le|10be|p010") {
            $bitDepth = 10
        }
        
        # Calcular métricas avanzadas
        $totalPixels = $width * $height
        $bitratePerPixel = $bitrate / $totalPixels * 1000  # bits por pixel
        $bitratePerSecond = if ($duration -gt 0) { $bitrate / $duration * 1000 } else { 0 }
        $bitsPerPixelPerSecond = if ($frameRate -gt 0) { $bitratePerPixel / $frameRate } else { 0 }
        
        # Clasificar resolución
        $resolutionClass = "Unknown"
        if ($totalPixels -ge 3840 * 2160 * 0.8) { $resolutionClass = "4K" }
        elseif ($totalPixels -ge 2560 * 1440 * 0.8) { $resolutionClass = "1440p" }
        elseif ($totalPixels -ge 1920 * 1080 * 0.8) { $resolutionClass = "1080p" }
        elseif ($totalPixels -ge 1280 * 720 * 0.8) { $resolutionClass = "720p" }
        else { $resolutionClass = "SD" }
        
        # Detectar orientación
        $orientation = if ($width -gt $height) { "Landscape" } elseif ($height -gt $width) { "Portrait" } else { "Square" }
        
        # Análisis de eficiencia de compresión actual
        $bytesPerSecond = if ($duration -gt 0) { $fileInfo.Length / $duration } else { 0 }
        $compressionEfficiency = if ($bitrate -gt 0) { ($fileInfo.Length * 8) / ($bitrate * $duration * 1000) } else { 0 }
        
        # Estimación de bitrate óptimo por categoría
        $optimalBitrates = @{
            "4K" = @{ "h264" = 35000; "hevc" = 20000 }
            "1440p" = @{ "h264" = 16000; "hevc" = 10000 }
            "1080p" = @{ "h264" = 8000; "hevc" = 5000 }
            "720p" = @{ "h264" = 5000; "hevc" = 3000 }
            "SD" = @{ "h264" = 2500; "hevc" = 1500 }
        }
        
        $codecFamily = if ($codec -match "hevc|h265") { "hevc" } else { "h264" }
        $optimalBitrate = $optimalBitrates[$resolutionClass][$codecFamily]
        $bitrateEfficiency = if ($optimalBitrate -gt 0) { $optimalBitrate / $bitrate } else { 1 }
        
        # Información de audio
        $audioInfo = @{
            Codec = if ($audioStream) { $audioStream.codec_name } else { "N/A" }
            Bitrate = if ($audioStream -and $audioStream.bit_rate) { [int]$audioStream.bit_rate / 1000 } else { 0 }
            SampleRate = if ($audioStream) { $audioStream.sample_rate } else { 0 }
            Channels = if ($audioStream) { $audioStream.channels } else { 0 }
        }
        
        return @{
            Success = $true
            # Información básica del archivo
            FileName = $fileInfo.Name
            FilePath = $VideoPath
            FileSize = $fileInfo.Length
            FileSizeFormatted = Get-FileSizeFormatted $fileInfo.Length
            CreationTime = $fileInfo.CreationTime
            
            # Información de video
            VideoCodec = $codec
            PixelFormat = $pixFormat
            BitDepth = $bitDepth
            Width = $width
            Height = $height
            Resolution = "${width}x${height}"
            ResolutionClass = $resolutionClass
            Orientation = $orientation
            FrameRate = $frameRate
            Duration = $duration
            DurationFormatted = [TimeSpan]::FromSeconds($duration).ToString("hh\:mm\:ss")
            
            # Información de bitrate
            Bitrate = $bitrate
            BitrateFormatted = "{0:N0} kbps" -f $bitrate
            
            # Métricas calculadas
            TotalPixels = $totalPixels
            BitratePerPixel = [math]::Round($bitratePerPixel, 6)
            BitratePerSecond = [math]::Round($bitratePerSecond, 0)
            BitsPerPixelPerSecond = [math]::Round($bitsPerPixelPerSecond, 8)
            BytesPerSecond = [math]::Round($bytesPerSecond, 0)
            CompressionEfficiency = [math]::Round($compressionEfficiency, 3)
            
            # Análisis de optimización
            OptimalBitrate = $optimalBitrate
            BitrateEfficiency = [math]::Round($bitrateEfficiency, 3)
            IsOverBitrate = $bitrate -gt ($optimalBitrate * 1.5)
            IsUnderBitrate = $bitrate -lt ($optimalBitrate * 0.5)
            
            # Información de audio
            Audio = $audioInfo
            
            # Metadatos adicionales
            Container = $metadata.format.format_name
            HasMetadata = $metadata.format.tags -ne $null
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
            FileName = $fileInfo.Name
        }
    }
}

function Export-AnalysisToJSON {
    param(
        [array]$AnalysisResults,
        [string]$OutputPath
    )
    
    $report = @{
        GeneratedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Tool = "Video Analyzer Tool - Tag-Flow"
        TotalFiles = $AnalysisResults.Count
        SuccessfulAnalysis = ($AnalysisResults | Where-Object { $_.Success }).Count
        FailedAnalysis = ($AnalysisResults | Where-Object { -not $_.Success }).Count
        Summary = @{
            TotalSize = ($AnalysisResults | Where-Object { $_.Success } | Measure-Object FileSize -Sum).Sum
            TotalDuration = ($AnalysisResults | Where-Object { $_.Success } | Measure-Object Duration -Sum).Sum
            AverageBitrate = ($AnalysisResults | Where-Object { $_.Success } | Measure-Object Bitrate -Average).Average
            ResolutionDistribution = ($AnalysisResults | Where-Object { $_.Success } | Group-Object ResolutionClass | ForEach-Object { @{ Resolution = $_.Name; Count = $_.Count } })
            CodecDistribution = ($AnalysisResults | Where-Object { $_.Success } | Group-Object VideoCodec | ForEach-Object { @{ Codec = $_.Name; Count = $_.Count } })
        }
        Results = $AnalysisResults
    }
    
    $jsonContent = $report | ConvertTo-Json -Depth 10 -Compress:$false
    Set-Content -Path $OutputPath -Value $jsonContent -Encoding UTF8
}

function Export-AnalysisToHTML {
    param(
        [array]$AnalysisResults,
        [string]$OutputPath
    )
    
    $successfulResults = $AnalysisResults | Where-Object { $_.Success }
    $totalFiles = $AnalysisResults.Count
    $successCount = $successfulResults.Count
    $totalSize = Get-FileSizeFormatted (($successfulResults | Measure-Object FileSize -Sum).Sum)
    $totalDuration = [TimeSpan]::FromSeconds(($successfulResults | Measure-Object Duration -Sum).Sum).ToString("hh\:mm\:ss")
    $avgBitrate = [math]::Round(($successfulResults | Measure-Object Bitrate -Average).Average, 0)
    $currentDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Construir HTML usando variables procesadas
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Video Analysis Report - Tag-Flow</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
        .summary { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .summary h3 { margin-top: 0; color: #333; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }
        .stat-value { font-size: 1.8em; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #667eea; color: white; font-weight: 600; }
        tr:hover { background-color: #f5f5f5; }
        .resolution-4K { color: #e74c3c; font-weight: bold; }
        .resolution-1440p { color: #f39c12; font-weight: bold; }
        .resolution-1080p { color: #27ae60; font-weight: bold; }
        .bitrate-high { color: #e74c3c; }
        .bitrate-optimal { color: #27ae60; }
        .bitrate-low { color: #f39c12; }
        .codec-hevc { background-color: #e8f5e8; }
        .codec-h264 { background-color: #e8f0ff; }
        .bit-depth-10 { background-color: #fff3e0; font-weight: bold; }
        .efficiency-good { color: #27ae60; font-weight: bold; }
        .efficiency-bad { color: #e74c3c; font-weight: bold; }
        
        /* Estilos para videos comprimidos */
        .compressed-video { opacity: 0.85; border-left: 4px solid #3498db; }
        .compressed-video .resolution-4K { color: #c0392b; }
        .compressed-video .resolution-1440p { color: #e67e22; }
        .compressed-video .resolution-1080p { color: #229954; }
        .compressed-video .bitrate-high { color: #cb4335; background-color: #fadbd8; }
        .compressed-video .bitrate-optimal { color: #229954; background-color: #d5f4e6; }
        .compressed-video .bitrate-low { color: #e67e22; background-color: #fdeaa7; }
        .compressed-video .codec-hevc { background-color: #d5f4e6; }
        .compressed-video .codec-h264 { background-color: #d6eaf8; }
        
        /* Leyenda de videos comprimidos */
        .legend { background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #3498db; }
        .legend h4 { margin: 0 0 8px 0; color: #2c3e50; font-size: 14px; }
        .legend p { margin: 0; font-size: 12px; color: #7f8c8d; }
        
        /* Estilos para enlaces de video */
        .video-link { 
            color: #2c3e50; 
            text-decoration: none; 
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .video-link:hover { 
            color: #3498db; 
            text-decoration: underline;
            cursor: pointer;
        }
        .video-link:visited { 
            color: #8e44ad; 
        }
        .compressed-video .video-link {
            color: #5d6d7e;
        }
        .compressed-video .video-link:hover {
            color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Video Analysis Report</h1>
        <p>Generated on $currentDate by Tag-Flow System</p>
    </div>
    
    <div class="summary">
        <h3>📈 Summary Statistics</h3>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">$totalFiles</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$successCount</div>
                <div class="stat-label">Successfully Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$totalSize</div>
                <div class="stat-label">Total Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$totalDuration</div>
                <div class="stat-label">Total Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$avgBitrate</div>
                <div class="stat-label">Avg Bitrate (kbps)</div>
            </div>
        </div>
    </div>
    
    <div class="legend">
        <h4>📋 Leyenda de Videos</h4>
        <p><strong>Videos Originales:</strong> Colores normales | <strong>Videos Comprimidos (con "compress"):</strong> Colores atenuados con borde azul izquierdo</p>
        <p><strong>💡 Tip:</strong> Haz click en el nombre del archivo para abrir el video directamente</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>📹 File Name</th>
                <th>📏 Resolution</th>
                <th>🎞️ Codec</th>
                <th>🎨 Bit Depth</th>
                <th>📊 Bitrate (kbps)</th>
                <th>💾 Size</th>
                <th>⏱️ Duration</th>
                <th>📈 Efficiency</th>
                <th>🎯 Optimal Bitrate</th>
                <th>⚖️ Status</th>
            </tr>
        </thead>
        <tbody>
"@

    foreach ($result in $successfulResults) {
        # Detectar si es un video comprimido
        $isCompressed = $result.FileName -match "compress"
        $compressedClass = if ($isCompressed) { "compressed-video" } else { "" }
        
        $resolutionClass = switch ($result.ResolutionClass) {
            "4K" { "resolution-4K" }
            "1440p" { "resolution-1440p" }
            "1080p" { "resolution-1080p" }
            default { "" }
        }
        
        $bitrateClass = if ($result.IsOverBitrate) { "bitrate-high" } 
                       elseif ($result.IsUnderBitrate) { "bitrate-low" } 
                       else { "bitrate-optimal" }
        
        $codecClass = if ($result.VideoCodec -match "hevc|h265") { "codec-hevc" } else { "codec-h264" }
        $bitDepthClass = if ($result.BitDepth -eq 10) { "bit-depth-10" } else { "" }
        $efficiencyClass = if ($result.BitrateEfficiency -gt 0.8 -and $result.BitrateEfficiency -lt 1.2) { "efficiency-good" } else { "efficiency-bad" }
        
        $status = if ($result.IsOverBitrate) { "🔴 High Bitrate" }
                 elseif ($result.IsUnderBitrate) { "🟡 Low Bitrate" }
                 else { "🟢 Optimal" }
        
        # Crear enlace para abrir el video (codificar caracteres especiales)
        $fileUri = ($result.FilePath -replace '\\', '/')
        # Primero codificar % para evitar doble codificación
        $fileUri = $fileUri.Replace('%', '%25')
        # Luego codificar otros caracteres especiales
        $fileUri = $fileUri.Replace(' ', '%20')
        $fileUri = $fileUri.Replace('#', '%23')
        $fileUri = $fileUri.Replace('&', '%26')
        $fileUri = $fileUri.Replace('?', '%3F')
        $fileUri = $fileUri.Replace('+', '%2B')
        $fileUri = $fileUri.Replace('[', '%5B')
        $fileUri = $fileUri.Replace(']', '%5D')
        $fileUri = $fileUri.Replace('(', '%28')
        $fileUri = $fileUri.Replace(')', '%29')
        if (-not $fileUri.StartsWith('file://')) {
            $fileUri = "file:///$fileUri"
        }
        
        # Construir cada fila usando variables procesadas
        $html += @"
            <tr class="$codecClass $bitDepthClass $compressedClass">
                <td title="Click para abrir: $($result.FilePath)">
                    <a href="$fileUri" class="video-link" target="_blank">$($result.FileName)</a>
                </td>
                <td class="$resolutionClass">$($result.Resolution) ($($result.ResolutionClass))</td>
                <td class="$codecClass">$($result.VideoCodec.ToUpper())</td>
                <td>$($result.BitDepth)-bit</td>
                <td class="$bitrateClass">$([math]::Round($result.Bitrate, 0))</td>
                <td>$($result.FileSizeFormatted)</td>
                <td>$($result.DurationFormatted)</td>
                <td class="$efficiencyClass">$($result.BitrateEfficiency)</td>
                <td>$([math]::Round($result.OptimalBitrate, 0))</td>
                <td>$status</td>
            </tr>
"@
    }
    
    $html += @"
        </tbody>
    </table>
</body>
</html>
"@
    
    Set-Content -Path $OutputPath -Value $html -Encoding UTF8
}

# SCRIPT PRINCIPAL
Write-Header

# Verificar FFmpeg/ffprobe
$ffprobePath = $FFmpegPath -replace "ffmpeg\.exe$", "ffprobe.exe"
if (-not (Test-Path $ffprobePath)) {
    Write-ColorOutput "❌ ffprobe no encontrado en: $ffprobePath" "Red"
    Write-ColorOutput "   Asegúrate de que ffprobe.exe esté en el mismo directorio que ffmpeg.exe" "Yellow"
    exit 1
}

Write-ColorOutput "✅ ffprobe encontrado: $ffprobePath" "Green"

# Verificar directorio
if (-not (Test-Path $InputPath)) {
    Write-ColorOutput "❌ Directorio no encontrado: $InputPath" "Red"
    exit 1
}

Write-ColorOutput "📁 Directorio de análisis: $InputPath" "Cyan"
Write-Host ""

# Buscar archivos de video
Write-ColorOutput "🔍 Buscando archivos de video (MP4, MKV, MOV)..." "Yellow"
$videoFiles = @()
$videoExtensions = @("*.mp4", "*.mkv", "*.mov")

try {
    # Método 1: Get-ChildItem estándar para cada extensión
    foreach ($extension in $videoExtensions) {
        $files1 = Get-ChildItem -Path $InputPath -Filter $extension -Recurse -ErrorAction SilentlyContinue
        if ($files1) { $videoFiles += $files1 }
    }

    # Método 2: System.IO para caracteres especiales
    foreach ($extension in $videoExtensions) {
        $allFiles = [System.IO.Directory]::GetFiles($InputPath, $extension, [System.IO.SearchOption]::AllDirectories)
        foreach ($file in $allFiles) {
            $fileInfo = New-Object System.IO.FileInfo $file
            if ($videoFiles.FullName -notcontains $fileInfo.FullName) {
                $videoFiles += $fileInfo
            }
        }
    }

    $videoFiles = $videoFiles | Sort-Object FullName
}
catch {
    Write-ColorOutput "❌ Error buscando archivos: $($_.Exception.Message)" "Red"
    exit 1
}

$totalFiles = $videoFiles.Count

if ($totalFiles -eq 0) {
    Write-ColorOutput "❌ No se encontraron archivos de video" "Red"
    exit 0
}

Write-ColorOutput "📊 Archivos encontrados: $totalFiles" "Green"
Write-Host ""

# Procesar archivos
Write-ColorOutput "🚀 Iniciando análisis de videos..." "Green"
Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"

$analysisResults = @()
$processedFiles = 0

foreach ($file in $videoFiles) {
    $processedFiles++
    
    Write-ColorOutput "📹 [$processedFiles/$totalFiles] Analizando: $($file.Name)" "Cyan"
    
    $filePath = $file.FullName
    $result = Analyze-VideoExtended $filePath
    $analysisResults += $result
    
    if ($result.Success) {
        Write-ColorOutput "   ✅ $($result.ResolutionClass) | $($result.VideoCodec) | $($result.BitDepth)-bit | $($result.BitrateFormatted)" "Green"
    } else {
        Write-ColorOutput "   ❌ $($result.Error)" "Red"
    }
    
    # Pequeña pausa
    Start-Sleep -Milliseconds 50
}

Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"

# Generar reportes
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDir = Join-Path (Split-Path $InputPath -Parent) "VideoAnalysis_$timestamp"

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

if ($OutputFormat -eq "json" -or $OutputFormat -eq "both") {
    $jsonPath = Join-Path $outputDir "$OutputFile.json"
    Export-AnalysisToJSON -AnalysisResults $analysisResults -OutputPath $jsonPath
    Write-ColorOutput "📄 Reporte JSON generado: $jsonPath" "Green"
}

if ($OutputFormat -eq "html" -or $OutputFormat -eq "both") {
    $htmlPath = Join-Path $outputDir "$OutputFile.html"
    Export-AnalysisToHTML -AnalysisResults $analysisResults -OutputPath $htmlPath
    Write-ColorOutput "🌐 Reporte HTML generado: $htmlPath" "Green"
}

# Estadísticas finales
$successfulAnalysis = $analysisResults | Where-Object { $_.Success }
Write-Host ""
Write-ColorOutput "📊 RESUMEN FINAL" "Green"
Write-ColorOutput "   Archivos analizados: $($analysisResults.Count)" "White"
Write-ColorOutput "   Análisis exitosos: $($successfulAnalysis.Count)" "Green"
Write-ColorOutput "   Análisis fallidos: $(($analysisResults | Where-Object { -not $_.Success }).Count)" "Red"

if ($successfulAnalysis.Count -gt 0) {
    Write-ColorOutput "   Tamaño total: $(Get-FileSizeFormatted (($successfulAnalysis | Measure-Object FileSize -Sum).Sum))" "White"
    Write-ColorOutput "   Duración total: $([TimeSpan]::FromSeconds(($successfulAnalysis | Measure-Object Duration -Sum).Sum).ToString("hh\:mm\:ss"))" "White"
    Write-ColorOutput "   Bitrate promedio: $([math]::Round(($successfulAnalysis | Measure-Object Bitrate -Average).Average, 0)) kbps" "White"
}

Write-Host ""
Write-ColorOutput "✅ Análisis completado. Revisa los reportes generados." "Green"
Write-ColorOutput "Presiona cualquier tecla para salir..." "Yellow"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")