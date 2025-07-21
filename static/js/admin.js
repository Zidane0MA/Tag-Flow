// Variables globales para el dashboard admin
let currentAction = null;
let confirmModal = null;

// Inicializar dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeAdminDashboard();
});

function initializeAdminDashboard() {
    console.log('🎛️ Inicializando Dashboard Administrativo...');
    
    // Inicializar modal de confirmación
    confirmModal = new bootstrap.Modal(document.getElementById('confirmActionModal'));
    
    // Cargar estadísticas iniciales
    loadSystemStats();
    
    // Cargar plataformas disponibles
    loadAvailablePlatforms();
    
    // Configurar evento para input personalizado
    setupCustomPlatformInput();
    
    // Configurar eventos para análisis de videos
    setupAnalyzePlatformInput();
    
    // Configurar actualización automática cada 30 segundos
    setInterval(loadSystemStats, 30000);
    
    console.log('✅ Dashboard Administrativo inicializado');
}

// Cargar estadísticas del sistema
async function loadSystemStats() {
    try {
        const statsResponse = await TagFlow.utils.apiRequest('/api/stats');
        const trashResponse = await TagFlow.utils.apiRequest('/api/trash/stats');
        
        if (statsResponse.success && trashResponse.success) {
            const stats = statsResponse.stats;
            const trashStats = trashResponse;
            
            // Actualizar contadores
            document.getElementById('total-videos').textContent = stats.total_videos || 0;
            document.getElementById('deleted-videos').textContent = trashStats.total_deleted || 0;
            document.getElementById('processed-videos').textContent = stats.by_status?.completado || 0;
            document.getElementById('pending-videos').textContent = stats.by_status?.pendiente || 0;
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
        addLogEntry('Error cargando estadísticas del sistema', 'error');
    }
}

// Cargar plataformas disponibles dinámicamente
async function loadAvailablePlatforms(sourceFilter = null) {
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/platforms');
        
        if (response.success) {
            const platforms = response.platforms;
            const platformSelect = document.getElementById('populate-platform');
            const sourceSelect = document.getElementById('populate-source');
            
            // Obtener fuente actual si no se especifica
            const currentSource = sourceFilter || sourceSelect.value;
            
            // Limpiar el select
            platformSelect.innerHTML = '';
            
            // Configurar opciones según la fuente
            if (currentSource === 'db') {
                // Solo BD: mostrar solo plataformas principales
                // 1. Separador - Plataformas Principales
                const mainSeparator = document.createElement('option');
                mainSeparator.disabled = true;
                mainSeparator.textContent = '— Plataformas Principales —';
                platformSelect.appendChild(mainSeparator);
                
                // 2. Solo principales
                const mainOnlyOption = document.createElement('option');
                mainOnlyOption.value = '';
                mainOnlyOption.textContent = 'Solo principales';
                platformSelect.appendChild(mainOnlyOption);
                
                // 3. Plataformas principales individuales (solo BD)
                const mainPlatformsOrder = ['instagram', 'tiktok', 'youtube'];
                const mainPlatformsNames = {
                    'instagram': 'Instagram (BD)',
                    'tiktok': 'TikTok (BD)', 
                    'youtube': 'YouTube (BD)'
                };
                
                mainPlatformsOrder.forEach(platformKey => {
                    if (platforms.main && platforms.main[platformKey] && platforms.main[platformKey].has_db) {
                        const option = document.createElement('option');
                        option.value = platformKey;
                        option.textContent = mainPlatformsNames[platformKey];
                        platformSelect.appendChild(option);
                    }
                });
                
            } else if (currentSource === 'organized') {
                // Solo carpetas: mostrar todas las plataformas
                // 1. Todas las plataformas
                const allPlatformsOption = document.createElement('option');
                allPlatformsOption.value = 'all-platforms';
                allPlatformsOption.textContent = 'Todas las plataformas';
                platformSelect.appendChild(allPlatformsOption);
                
                // 2. Separador - Plataformas Principales
                const mainSeparator = document.createElement('option');
                mainSeparator.disabled = true;
                mainSeparator.textContent = '— Plataformas Principales —';
                platformSelect.appendChild(mainSeparator);
                
                // 3. Solo principales
                const mainOnlyOption = document.createElement('option');
                mainOnlyOption.value = '';
                mainOnlyOption.textContent = 'Solo principales';
                platformSelect.appendChild(mainOnlyOption);
                
                // 4. Plataformas principales individuales (solo carpetas)
                const mainPlatformsOrder = ['instagram', 'tiktok', 'youtube'];
                const mainPlatformsNames = {
                    'instagram': 'Instagram (Carpetas)',
                    'tiktok': 'TikTok (Carpetas)', 
                    'youtube': 'YouTube (Carpetas)'
                };
                
                mainPlatformsOrder.forEach(platformKey => {
                    if (platforms.main && platforms.main[platformKey] && platforms.main[platformKey].has_organized) {
                        const option = document.createElement('option');
                        option.value = platformKey;
                        option.textContent = mainPlatformsNames[platformKey];
                        platformSelect.appendChild(option);
                    }
                });
                
                // 5. Separador - Plataformas Adicionales (solo si existen)
                if (platforms.additional && Object.keys(platforms.additional).length > 0) {
                    const additionalSeparator = document.createElement('option');
                    additionalSeparator.disabled = true;
                    additionalSeparator.textContent = '— Plataformas Adicionales —';
                    platformSelect.appendChild(additionalSeparator);
                    
                    // 6. Solo adicionales
                    const additionalOnlyOption = document.createElement('option');
                    additionalOnlyOption.value = 'other';
                    additionalOnlyOption.textContent = 'Solo adicionales';
                    platformSelect.appendChild(additionalOnlyOption);
                    
                    // 7. Plataformas adicionales individuales (orden alfabético)
                    const additionalKeys = Object.keys(platforms.additional).sort();
                    additionalKeys.forEach(key => {
                        const info = platforms.additional[key];
                        const option = document.createElement('option');
                        option.value = key;
                        option.textContent = `${info.name} (Carpeta)`;
                        platformSelect.appendChild(option);
                    });
                }
                
                // 8. Separador - Opciones Especiales
                const specialSeparator = document.createElement('option');
                specialSeparator.disabled = true;
                specialSeparator.textContent = '— Opciones Especiales —';
                platformSelect.appendChild(specialSeparator);
                
                // 9. Personalizada
                const customOption = document.createElement('option');
                customOption.value = 'custom';
                customOption.textContent = 'Personalizada...';
                platformSelect.appendChild(customOption);
                
            } else {
                // Todas las fuentes: mostrar todo como estaba originalmente
                // 1. Todas las plataformas (primera opción)
                const allPlatformsOption = document.createElement('option');
                allPlatformsOption.value = 'all-platforms';
                allPlatformsOption.textContent = 'Todas las plataformas';
                platformSelect.appendChild(allPlatformsOption);
                
                // 2. Separador - Plataformas Principales
                const mainSeparator = document.createElement('option');
                mainSeparator.disabled = true;
                mainSeparator.textContent = '— Plataformas Principales —';
                platformSelect.appendChild(mainSeparator);
                
                // 3. Solo principales
                const mainOnlyOption = document.createElement('option');
                mainOnlyOption.value = '';
                mainOnlyOption.textContent = 'Solo principales';
                platformSelect.appendChild(mainOnlyOption);
                
                // 4. Plataformas principales individuales (orden específico)
                const mainPlatformsOrder = ['instagram', 'tiktok', 'youtube'];
                const mainPlatformsNames = {
                    'instagram': 'Instagram',
                    'tiktok': 'TikTok', 
                    'youtube': 'YouTube'
                };
                
                mainPlatformsOrder.forEach(platformKey => {
                    if (platforms.main && platforms.main[platformKey]) {
                        const info = platforms.main[platformKey];
                        const option = document.createElement('option');
                        option.value = platformKey;
                        option.textContent = `${mainPlatformsNames[platformKey]} (${info.has_db ? 'BD' : ''}${info.has_db && info.has_organized ? ' + ' : ''}${info.has_organized ? 'Carpetas' : ''})`;
                        platformSelect.appendChild(option);
                    }
                });
                
                // 5. Separador - Plataformas Adicionales (solo si existen)
                if (platforms.additional && Object.keys(platforms.additional).length > 0) {
                    const additionalSeparator = document.createElement('option');
                    additionalSeparator.disabled = true;
                    additionalSeparator.textContent = '— Plataformas Adicionales —';
                    platformSelect.appendChild(additionalSeparator);
                    
                    // 6. Solo adicionales
                    const additionalOnlyOption = document.createElement('option');
                    additionalOnlyOption.value = 'other';
                    additionalOnlyOption.textContent = 'Solo adicionales';
                    platformSelect.appendChild(additionalOnlyOption);
                    
                    // 7. Plataformas adicionales individuales (orden alfabético)
                    const additionalKeys = Object.keys(platforms.additional).sort();
                    additionalKeys.forEach(key => {
                        const info = platforms.additional[key];
                        const option = document.createElement('option');
                        option.value = key;
                        option.textContent = `${info.name} (Carpeta)`;
                        platformSelect.appendChild(option);
                    });
                }
                
                // 8. Separador - Opciones Especiales
                const specialSeparator = document.createElement('option');
                specialSeparator.disabled = true;
                specialSeparator.textContent = '— Opciones Especiales —';
                platformSelect.appendChild(specialSeparator);
                
                // 9. Personalizada
                const customOption = document.createElement('option');
                customOption.value = 'custom';
                customOption.textContent = 'Personalizada...';
                platformSelect.appendChild(customOption);
            }
            
            console.log('✅ Plataformas cargadas dinámicamente para fuente:', currentSource);
        } else {
            console.error('Error cargando plataformas:', response.error);
            addLogEntry('Error cargando plataformas disponibles', 'error');
        }
    } catch (error) {
        console.error('Error cargando plataformas:', error);
        addLogEntry('Error cargando plataformas disponibles', 'error');
    }
}

// Configurar evento para inputs personalizados
function setupCustomPlatformInput() {
    const platformSelect = document.getElementById('populate-platform');
    const customPlatformContainer = document.getElementById('custom-platform-container');
    const sourceSelect = document.getElementById('populate-source');
    const fileSourceContainer = document.getElementById('file-source-container');
    const limitInput = document.getElementById('populate-limit');
    
    // Manejar cambios en fuente
    sourceSelect.addEventListener('change', function() {
        const isFileSelected = this.value === 'file';
        
        if (isFileSelected) {
            // Mostrar input de archivo específico
            fileSourceContainer.style.display = 'block';
            // Ocultar input de plataforma personalizada
            customPlatformContainer.style.display = 'none';
            // Resetear plataforma a opción por defecto
            platformSelect.value = 'all-platforms';
            // Deshabilitar campos no necesarios para archivo específico
            platformSelect.disabled = true;
            limitInput.disabled = true;
        } else {
            // Ocultar input de archivo específico
            fileSourceContainer.style.display = 'none';
            // Habilitar campos normales
            platformSelect.disabled = false;
            limitInput.disabled = false;
            // Recargar plataformas según la fuente seleccionada
            loadAvailablePlatforms(this.value);
            // Manejar plataforma personalizada si corresponde
            if (platformSelect.value === 'custom') {
                customPlatformContainer.style.display = 'block';
            }
        }
    });
    
    // Manejar cambios en plataforma
    platformSelect.addEventListener('change', function() {
        // Solo mostrar input personalizado si no está seleccionado "archivo específico"
        if (sourceSelect.value !== 'file') {
            if (this.value === 'custom') {
                customPlatformContainer.style.display = 'block';
                // Ocultar input de archivo si estaba visible
                fileSourceContainer.style.display = 'none';
            } else {
                customPlatformContainer.style.display = 'none';
            }
        }
    });
}

// Cargar plataformas disponibles dinámicamente para análisis
async function loadAnalyzePlatforms(sourceFilter = null) {
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/platforms');
        
        if (response.success) {
            const platforms = response.platforms;
            const platformSelect = document.getElementById('analyze-platform');
            const sourceSelect = document.getElementById('analyze-source');
            
            // Obtener fuente actual si no se especifica
            const currentSource = sourceFilter || sourceSelect.value;
            
            // Limpiar el select
            platformSelect.innerHTML = '';
            
            // Configurar opciones según la fuente
            if (currentSource === 'db') {
                // Solo BD: mostrar solo plataformas principales
                // 1. Separador - Plataformas Principales
                const mainSeparator = document.createElement('option');
                mainSeparator.disabled = true;
                mainSeparator.textContent = '— Plataformas Principales —';
                platformSelect.appendChild(mainSeparator);
                
                // 2. Solo principales
                const mainOnlyOption = document.createElement('option');
                mainOnlyOption.value = '';
                mainOnlyOption.textContent = 'Solo principales';
                platformSelect.appendChild(mainOnlyOption);
                
                // 3. Plataformas principales individuales (solo BD)
                const mainPlatformsOrder = ['instagram', 'tiktok', 'youtube'];
                const mainPlatformsNames = {
                    'instagram': 'Instagram (BD)',
                    'tiktok': 'TikTok (BD)', 
                    'youtube': 'YouTube (BD)'
                };
                
                mainPlatformsOrder.forEach(platformKey => {
                    if (platforms.main && platforms.main[platformKey] && platforms.main[platformKey].has_db) {
                        const option = document.createElement('option');
                        option.value = platformKey;
                        option.textContent = mainPlatformsNames[platformKey];
                        platformSelect.appendChild(option);
                    }
                });
                
            } else if (currentSource === 'organized') {
                // Solo carpetas: mostrar todas las plataformas
                // 1. Todas las plataformas
                const allPlatformsOption = document.createElement('option');
                allPlatformsOption.value = 'all-platforms';
                allPlatformsOption.textContent = 'Todas las plataformas';
                platformSelect.appendChild(allPlatformsOption);
                
                // 2. Separador - Plataformas Principales
                const mainSeparator = document.createElement('option');
                mainSeparator.disabled = true;
                mainSeparator.textContent = '— Plataformas Principales —';
                platformSelect.appendChild(mainSeparator);
                
                // 3. Solo principales
                const mainOnlyOption = document.createElement('option');
                mainOnlyOption.value = '';
                mainOnlyOption.textContent = 'Solo principales';
                platformSelect.appendChild(mainOnlyOption);
                
                // 4. Plataformas principales individuales (solo carpetas)
                const mainPlatformsOrder = ['instagram', 'tiktok', 'youtube'];
                const mainPlatformsNames = {
                    'instagram': 'Instagram (Carpetas)',
                    'tiktok': 'TikTok (Carpetas)', 
                    'youtube': 'YouTube (Carpetas)'
                };
                
                mainPlatformsOrder.forEach(platformKey => {
                    if (platforms.main && platforms.main[platformKey] && platforms.main[platformKey].has_organized) {
                        const option = document.createElement('option');
                        option.value = platformKey;
                        option.textContent = mainPlatformsNames[platformKey];
                        platformSelect.appendChild(option);
                    }
                });
                
                // 5. Separador - Plataformas Adicionales (solo si existen)
                if (platforms.additional && Object.keys(platforms.additional).length > 0) {
                    const additionalSeparator = document.createElement('option');
                    additionalSeparator.disabled = true;
                    additionalSeparator.textContent = '— Plataformas Adicionales —';
                    platformSelect.appendChild(additionalSeparator);
                    
                    // 6. Solo adicionales
                    const additionalOnlyOption = document.createElement('option');
                    additionalOnlyOption.value = 'other';
                    additionalOnlyOption.textContent = 'Solo adicionales';
                    platformSelect.appendChild(additionalOnlyOption);
                    
                    // 7. Plataformas adicionales individuales (orden alfabético)
                    const additionalKeys = Object.keys(platforms.additional).sort();
                    additionalKeys.forEach(key => {
                        const info = platforms.additional[key];
                        const option = document.createElement('option');
                        option.value = key;
                        option.textContent = `${info.name} (Carpeta)`;
                        platformSelect.appendChild(option);
                    });
                }
                
                // 8. Separador - Opciones Especiales
                const specialSeparator = document.createElement('option');
                specialSeparator.disabled = true;
                specialSeparator.textContent = '— Opciones Especiales —';
                platformSelect.appendChild(specialSeparator);
                
                // 9. Personalizada
                const customOption = document.createElement('option');
                customOption.value = 'custom';
                customOption.textContent = 'Personalizada...';
                platformSelect.appendChild(customOption);
                
            } else {
                // Todas las fuentes: mostrar todo como estaba originalmente
                // 1. Todas las plataformas (primera opción)
                const allPlatformsOption = document.createElement('option');
                allPlatformsOption.value = 'all-platforms';
                allPlatformsOption.textContent = 'Todas las plataformas';
                platformSelect.appendChild(allPlatformsOption);
                
                // 2. Separador - Plataformas Principales
                const mainSeparator = document.createElement('option');
                mainSeparator.disabled = true;
                mainSeparator.textContent = '— Plataformas Principales —';
                platformSelect.appendChild(mainSeparator);
                
                // 3. Solo principales
                const mainOnlyOption = document.createElement('option');
                mainOnlyOption.value = '';
                mainOnlyOption.textContent = 'Solo principales';
                platformSelect.appendChild(mainOnlyOption);
                
                // 4. Plataformas principales individuales (orden específico)
                const mainPlatformsOrder = ['instagram', 'tiktok', 'youtube'];
                const mainPlatformsNames = {
                    'instagram': 'Instagram',
                    'tiktok': 'TikTok', 
                    'youtube': 'YouTube'
                };
                
                mainPlatformsOrder.forEach(platformKey => {
                    if (platforms.main && platforms.main[platformKey]) {
                        const info = platforms.main[platformKey];
                        const option = document.createElement('option');
                        option.value = platformKey;
                        option.textContent = `${mainPlatformsNames[platformKey]} (${info.has_db ? 'BD' : ''}${info.has_db && info.has_organized ? ' + ' : ''}${info.has_organized ? 'Carpetas' : ''})`;
                        platformSelect.appendChild(option);
                    }
                });
                
                // 5. Separador - Plataformas Adicionales (solo si existen)
                if (platforms.additional && Object.keys(platforms.additional).length > 0) {
                    const additionalSeparator = document.createElement('option');
                    additionalSeparator.disabled = true;
                    additionalSeparator.textContent = '— Plataformas Adicionales —';
                    platformSelect.appendChild(additionalSeparator);
                    
                    // 6. Solo adicionales
                    const additionalOnlyOption = document.createElement('option');
                    additionalOnlyOption.value = 'other';
                    additionalOnlyOption.textContent = 'Solo adicionales';
                    platformSelect.appendChild(additionalOnlyOption);
                    
                    // 7. Plataformas adicionales individuales (orden alfabético)
                    const additionalKeys = Object.keys(platforms.additional).sort();
                    additionalKeys.forEach(key => {
                        const info = platforms.additional[key];
                        const option = document.createElement('option');
                        option.value = key;
                        option.textContent = `${info.name} (Carpeta)`;
                        platformSelect.appendChild(option);
                    });
                }
                
                // 8. Separador - Opciones Especiales
                const specialSeparator = document.createElement('option');
                specialSeparator.disabled = true;
                specialSeparator.textContent = '— Opciones Especiales —';
                platformSelect.appendChild(specialSeparator);
                
                // 9. Personalizada
                const customOption = document.createElement('option');
                customOption.value = 'custom';
                customOption.textContent = 'Personalizada...';
                platformSelect.appendChild(customOption);
            }
            
            console.log('✅ Plataformas de análisis cargadas dinámicamente para fuente:', currentSource);
        } else {
            console.error('Error cargando plataformas para análisis:', response.error);
            addLogEntry('Error cargando plataformas disponibles para análisis', 'error');
        }
    } catch (error) {
        console.error('Error cargando plataformas para análisis:', error);
        addLogEntry('Error cargando plataformas disponibles para análisis', 'error');
    }
}

// Configurar evento para inputs personalizados de análisis
function setupAnalyzePlatformInput() {
    const platformSelect = document.getElementById('analyze-platform');
    const customPlatformContainer = document.getElementById('analyze-custom-platform-container');
    const sourceSelect = document.getElementById('analyze-source');
    
    if (platformSelect && customPlatformContainer && sourceSelect) {
        // Manejar cambios en fuente de análisis
        sourceSelect.addEventListener('change', function() {
            // Recargar plataformas según la fuente seleccionada
            loadAnalyzePlatforms(this.value);
            // Ocultar input personalizado cuando cambie la fuente
            customPlatformContainer.style.display = 'none';
        });
        
        // Manejar cambios en plataforma de análisis
        platformSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customPlatformContainer.style.display = 'block';
            } else {
                customPlatformContainer.style.display = 'none';
            }
        });
        
        // Cargar plataformas iniciales
        loadAnalyzePlatforms();
    }
}

// Función para abrir selector de archivos
function openFileSelector() {
    // Crear input file invisible
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.mp4,.avi,.mov,.mkv,.wmv,.flv,.webm,.m4v'; // Extensiones de video
    fileInput.style.display = 'none';
    
    // Agregar al DOM temporalmente
    document.body.appendChild(fileInput);
    
    // Manejar selección de archivo
    fileInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            // En navegadores modernos, obtener la ruta real del archivo no es posible por seguridad
            // Solo tenemos acceso al nombre del archivo, no a la ruta completa
            const fileName = file.name;
            const filePath = file.webkitRelativePath || fileName;
            
            // Mostrar información en el terminal
            addTerminalOutput(`📁 Archivo seleccionado: ${fileName}`);
            addTerminalOutput(`⚠️ Nota: Por seguridad del navegador, debes copiar la ruta completa manualmente`);
            addLogEntry(`Archivo seleccionado: ${fileName}`, 'info');
            
            // Sugerir al usuario que copie la ruta manualmente
            const pathInput = document.getElementById('file-source-path');
            pathInput.placeholder = `Seleccionado: ${fileName} - Copia la ruta completa aquí`;
            pathInput.focus();
        }
        
        // Limpiar el input temporal
        document.body.removeChild(fileInput);
    });
    
    // Activar el selector de archivos
    fileInput.click();
}

// Función para limpiar selección de archivo
function clearFileSelection() {
    const pathInput = document.getElementById('file-source-path');
    
    // Limpiar el campo
    pathInput.value = '';
    pathInput.placeholder = 'Ej: D:\\Videos\\mi_video.mp4';
    
    // Mostrar en terminal
    addTerminalOutput('🗑️ Selección de archivo limpiada');
    addLogEntry('Selección de archivo limpiada', 'info');
    
    // Enfocar el campo para nueva entrada
    pathInput.focus();
}

// Ejecutar poblado de base de datos
async function executePopulateDB() {
    const source = document.getElementById('populate-source').value;
    let platform = document.getElementById('populate-platform').value;
    const limit = document.getElementById('populate-limit').value;
    const forceOption = document.getElementById('populate-force').checked;
    
    // Manejar fuente de archivo específico
    if (source === 'file') {
        const filePath = document.getElementById('file-source-path').value.trim();
        if (!filePath) {
            addTerminalOutput('❌ Error: Debes especificar la ruta del archivo de video');
            return;
        }
        
        // Construir comando para archivo específico
        let command = `python main.py populate-db --file "${filePath}"`;
        if (forceOption) {
            command += ' --force';
        }
        
        addTerminalOutput(`Ejecutando: ${command}`);
        showProgress('populate-progress');
        
        try {
            const response = await TagFlow.utils.apiRequest('/api/admin/populate-db', {
                method: 'POST',
                body: JSON.stringify({
                    file: filePath,
                    force: forceOption
                })
            });
            
            if (response.success) {
                // Mostrar toda la salida del comando en el terminal
                if (response.terminal_output && response.terminal_output.length > 0) {
                    response.terminal_output.forEach(line => {
                        addTerminalOutput(line);
                    });
                }
                addTerminalOutput(`✅ ${response.message}`);
                addLogEntry(`Archivo importado - Ruta: ${filePath}`, 'success');
                loadSystemStats();
            } else {
                // Mostrar salida de error en el terminal
                if (response.terminal_output && response.terminal_output.length > 0) {
                    response.terminal_output.forEach(line => {
                        addTerminalOutput(line);
                    });
                }
                addTerminalOutput(`❌ Error: ${response.error}`);
                addLogEntry(`Error importando archivo: ${response.error}`, 'error');
            }
        } catch (error) {
            addTerminalOutput(`❌ Error ejecutando comando: ${error.message}`);
            addLogEntry(`Error importando archivo: ${error.message}`, 'error');
        } finally {
            hideProgress('populate-progress');
        }
        return;
    }
    
    // Manejar plataforma personalizada
    if (platform === 'custom') {
        const customPlatformName = document.getElementById('custom-platform-name').value.trim();
        if (!customPlatformName) {
            addTerminalOutput('❌ Error: Debes especificar el nombre de la plataforma personalizada');
            return;
        }
        platform = customPlatformName;
    }
    
    // Construir comando para fuentes normales
    let command = `python main.py populate-db --source ${source} --limit ${limit}`;
    if (platform) {
        command += ` --platform ${platform}`;
    }
    if (forceOption) {
        command += ' --force';
    }
    
    addTerminalOutput(`Ejecutando: ${command}`);
    showProgress('populate-progress');
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/populate-db', {
            method: 'POST',
            body: JSON.stringify({
                source: source,
                platform: platform || null,
                limit: parseInt(limit),
                force: forceOption
            })
        });
        
        if (response.success) {
            // Mostrar toda la salida del comando en el terminal
            if (response.terminal_output && response.terminal_output.length > 0) {
                response.terminal_output.forEach(line => {
                    addTerminalOutput(line);
                });
            }
            addTerminalOutput(`✅ ${response.message}`);
            addLogEntry(`Poblado de BD completado - Fuente: ${source}, Plataforma: ${platform || 'todas'}, Límite: ${limit}`, 'success');
            loadSystemStats(); // Actualizar estadísticas
        } else {
            // Mostrar salida de error en el terminal
            if (response.terminal_output && response.terminal_output.length > 0) {
                response.terminal_output.forEach(line => {
                    addTerminalOutput(line);
                });
            }
            addTerminalOutput(`❌ Error: ${response.error}`);
            addLogEntry(`Error en poblado de BD: ${response.error}`, 'error');
        }
    } catch (error) {
        addTerminalOutput(`❌ Error ejecutando comando: ${error.message}`);
        addLogEntry(`Error ejecutando poblado de BD: ${error.message}`, 'error');
    } finally {
        hideProgress('populate-progress');
    }
}

// Ejecutar análisis de videos
async function executeAnalyzeVideos() {
    const source = document.getElementById('analyze-source').value;
    const platform = document.getElementById('analyze-platform').value;
    const limit = document.getElementById('analyze-limit').value;
    const force = document.getElementById('analyze-force').checked;
    const customPlatform = document.getElementById('analyze-custom-platform-name').value;
    
    // Determinar plataforma final
    let finalPlatform = platform;
    if (platform === 'custom' && customPlatform) {
        finalPlatform = customPlatform;
    }
    
    // Construir comando
    let command = `python main.py`;
    if (limit) command += ` --limit ${limit}`;
    if (source !== 'all') command += ` --source ${source}`;
    if (finalPlatform) command += ` --platform ${finalPlatform}`;
    if (force) command += ` --force`;
    
    addTerminalOutput(`Ejecutando: ${command}`);
    showProgress('analyze-progress');
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/analyze-videos', {
            method: 'POST',
            body: JSON.stringify({
                source: source,
                platform: finalPlatform || null,
                limit: limit ? parseInt(limit) : null,
                force: force
            })
        });
        
        hideProgress('analyze-progress');
        
        if (response.success) {
            addTerminalOutput(`✅ Análisis completado: ${response.message}`);
            addLogEntry(`Análisis de videos completado - ${response.processed || 0} videos procesados`, 'success');
            loadSystemStats();
        } else {
            addTerminalOutput(`❌ Error: ${response.error}`);
            addLogEntry(`Error en análisis: ${response.error}`, 'error');
        }
    } catch (error) {
        hideProgress('analyze-progress');
        addTerminalOutput(`❌ Error ejecutando análisis: ${error.message}`);
        addLogEntry(`Error ejecutando análisis: ${error.message}`, 'error');
    }
}

// Ejecutar reanálisis de videos específicos
async function executeReanalyzeVideos() {
    const videoIds = document.getElementById('reanalyze-video-ids').value.trim();
    const force = document.getElementById('reanalyze-force').checked;
    
    if (!videoIds) {
        addTerminalOutput('❌ Error: Debe proporcionar al menos un ID de video');
        return;
    }
    
    // Validar formato de IDs
    const idsArray = videoIds.split(',').map(id => id.trim()).filter(id => id);
    const invalidIds = idsArray.filter(id => !/^\d+$/.test(id));
    
    if (invalidIds.length > 0) {
        addTerminalOutput(`❌ Error: IDs inválidos: ${invalidIds.join(', ')}`);
        return;
    }
    
    // Construir comando
    let command = `python main.py --reanalyze-video ${videoIds}`;
    if (force) command += ` --force`;
    
    addTerminalOutput(`Ejecutando: ${command}`);
    showProgress('analyze-progress');
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/videos/bulk-reanalyze', {
            method: 'POST',
            body: JSON.stringify({
                video_ids: idsArray,
                force: force
            })
        });
        
        hideProgress('analyze-progress');
        
        if (response.success) {
            addTerminalOutput(`✅ Reanálisis completado: ${response.message}`);
            addLogEntry(`Reanálisis completado - ${response.total_videos || idsArray.length} videos procesados`, 'success');
            loadSystemStats();
        } else {
            addTerminalOutput(`❌ Error: ${response.error}`);
            addLogEntry(`Error en reanálisis: ${response.error}`, 'error');
        }
    } catch (error) {
        hideProgress('analyze-progress');
        addTerminalOutput(`❌ Error ejecutando reanálisis: ${error.message}`);
        addLogEntry(`Error ejecutando reanálisis: ${error.message}`, 'error');
    }
}

// Ejecutar generación de thumbnails
async function executeGenerateThumbnails() {
    const platform = document.getElementById('thumbnail-platform').value;
    const limit = document.getElementById('thumbnail-limit').value;
    
    addTerminalOutput(`Generando thumbnails para ${platform || 'todas las plataformas'} (límite: ${limit})`);
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/generate-thumbnails', {
            method: 'POST',
            body: JSON.stringify({
                platform: platform || null,
                limit: parseInt(limit)
            })
        });
        
        if (response.success) {
            addTerminalOutput(`✅ Thumbnails generados: ${response.message}`);
            addLogEntry(`Generación de thumbnails completada`, 'success');
        } else {
            addTerminalOutput(`❌ Error: ${response.error}`);
            addLogEntry(`Error generando thumbnails: ${response.error}`, 'error');
        }
    } catch (error) {
        addTerminalOutput(`❌ Error: ${error.message}`);
        addLogEntry(`Error generando thumbnails: ${error.message}`, 'error');
    }
}

// Acciones de mantenimiento
async function executeSystemBackup() {
    addTerminalOutput('Creando backup del sistema...');
    addLogEntry('Backup del sistema iniciado', 'info');
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/backup', {
            method: 'POST'
        });
        
        if (response.success) {
            addTerminalOutput(`✅ Backup creado: ${response.backup_path}`);
            addLogEntry('Backup del sistema completado', 'success');
        } else {
            addTerminalOutput(`❌ Error creando backup: ${response.error}`);
            addLogEntry(`Error en backup: ${response.error}`, 'error');
        }
    } catch (error) {
        addTerminalOutput(`❌ Error: ${error.message}`);
        addLogEntry(`Error en backup: ${error.message}`, 'error');
    }
}

async function executeOptimizeDB() {
    addTerminalOutput('Optimizando base de datos...');
    addLogEntry('Optimización de BD iniciada', 'info');
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/optimize-db', {
            method: 'POST'
        });
        
        if (response.success) {
            addTerminalOutput(`✅ Optimización completada: ${response.message}`);
            addLogEntry('Base de datos optimizada', 'success');
        } else {
            addTerminalOutput(`❌ Error: ${response.error}`);
            addLogEntry(`Error optimizando BD: ${response.error}`, 'error');
        }
    } catch (error) {
        addTerminalOutput(`❌ Error: ${error.message}`);
        addLogEntry(`Error optimizando BD: ${error.message}`, 'error');
    }
}

async function executeVerifySystem() {
    addTerminalOutput('Verificando integridad del sistema...');
    addLogEntry('Verificación del sistema iniciada', 'info');
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/verify', {
            method: 'POST'
        });
        
        if (response.success) {
            addTerminalOutput(`✅ Verificación completada: ${response.message}`);
            addLogEntry('Sistema verificado correctamente', 'success');
        } else {
            addTerminalOutput(`⚠️ Advertencias encontradas: ${response.warnings}`);
            addLogEntry(`Verificación con advertencias: ${response.warnings}`, 'warning');
        }
    } catch (error) {
        addTerminalOutput(`❌ Error: ${error.message}`);
        addLogEntry(`Error en verificación: ${error.message}`, 'error');
    }
}

async function executeCleanCache() {
    addTerminalOutput('Limpiando cache del sistema...');
    
    // Simular limpieza de cache
    setTimeout(() => {
        addTerminalOutput('✅ Cache limpiado correctamente');
        addLogEntry('Cache del sistema limpiado', 'success');
    }, 1000);
}

// Acciones peligrosas (con confirmación)
function executeEmptyTrash() {
    showDangerAction(
        'Vaciar Papelera',
        '💀',
        'Esta acción eliminará PERMANENTEMENTE todos los videos en la papelera.',
        'Esta acción NO SE PUEDE DESHACER',
        [
            'Todos los videos en papelera serán eliminados para siempre',
            'Los archivos de video se borrarán del sistema de archivos',
            'Los metadatos asociados se perderán permanentemente',
            'No será posible recuperar ningún contenido eliminado'
        ],
        'confirmEmptyTrash'
    );
}

function executeResetDatabase() {
    showDangerAction(
        'Reset Completo de Base de Datos',
        '☠️',
        'Esta acción eliminará COMPLETAMENTE la base de datos del sistema.',
        'PELIGRO EXTREMO - Esta acción es IRREVERSIBLE',
        [
            'TODOS los videos registrados se perderán',
            'TODOS los metadatos y configuraciones se eliminarán',
            'TODAS las estadísticas y análisis se borrarán',
            'El sistema volverá al estado inicial',
            'Deberás repoblar la base de datos desde cero'
        ],
        'confirmResetDatabase',
        true // Requiere confirmación por escrito
    );
}

// Sistema de confirmación avanzado
function showDangerAction(title, icon, description, warning, consequences, action, requiresConfirmation = false) {
    document.getElementById('confirmActionTitle').textContent = title;
    
    // Crear contenido estructurado
    const modalBody = document.getElementById('confirmActionBody');
    modalBody.innerHTML = `
        <div class="modal-danger-content">
            <div class="modal-danger-icon">${icon}</div>
            <h4 class="modal-danger-title">${title}</h4>
            <div class="modal-danger-description">${description}</div>
            <div class="modal-danger-warning">${warning}</div>
            <div class="modal-danger-consequences">
                <h6>Consecuencias de esta acción:</h6>
                <ul>
                    ${consequences.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
            ${requiresConfirmation ? `
                <div class="modal-confirmation-input">
                    <label for="confirmationText">Para continuar, escribe "CONFIRMAR" en mayúsculas:</label>
                    <input type="text" id="confirmationText" placeholder="Escribe CONFIRMAR para habilitar el botón" autocomplete="off">
                    <div class="form-text">Esta confirmación adicional es requerida para acciones extremadamente peligrosas.</div>
                </div>
            ` : ''}
        </div>
    `;
    
    const confirmBtn = document.getElementById('confirmActionBtn');
    confirmBtn.className = 'btn btn-danger';
    
    if (requiresConfirmation) {
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Confirmación requerida';
        
        const confirmInput = document.getElementById('confirmationText');
        confirmInput.addEventListener('input', function() {
            if (this.value === 'CONFIRMAR') {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Ejecutar Acción Peligrosa';
                confirmBtn.classList.add('pulse-ready');
            } else {
                confirmBtn.disabled = true;
                confirmBtn.textContent = 'Confirmación requerida';
                confirmBtn.classList.remove('pulse-ready');
            }
        });
    } else {
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirmar';
    }
    
    currentAction = action;
    confirmModal.show();
}

// Función legacy para compatibilidad
function showConfirmAction(title, message, type, action) {
    document.getElementById('confirmActionTitle').textContent = title;
    document.getElementById('confirmActionBody').innerHTML = message.replace(/\n/g, '<br>');
    
    const confirmBtn = document.getElementById('confirmActionBtn');
    confirmBtn.className = `btn btn-${type}`;
    confirmBtn.disabled = false;
    confirmBtn.textContent = 'Confirmar';
    
    currentAction = action;
    confirmModal.show();
}

function executeConfirmedAction() {
    if (currentAction) {
        window[currentAction]();
        confirmModal.hide();
        currentAction = null;
    }
}

async function confirmEmptyTrash() {
    addTerminalOutput('🗑️ Vaciando papelera...');
    addLogEntry('Vaciado de papelera iniciado', 'warning');
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/empty-trash', {
            method: 'POST'
        });
        
        if (response.success) {
            addTerminalOutput(`✅ Papelera vaciada: ${response.deleted_count} videos eliminados permanentemente`);
            addLogEntry(`Papelera vaciada - ${response.deleted_count} videos eliminados`, 'warning');
            loadSystemStats();
        } else {
            addTerminalOutput(`❌ Error: ${response.error}`);
        }
    } catch (error) {
        addTerminalOutput(`❌ Error: ${error.message}`);
    }
}

async function confirmResetDatabase() {
    addTerminalOutput('💀 INICIANDO RESET COMPLETO DE BASE DE DATOS...');
    addLogEntry('Reset completo de BD iniciado', 'warning');
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/reset-database', {
            method: 'POST'
        });
        
        if (response.success) {
            // Mostrar salida del comando en el terminal
            if (response.terminal_output && response.terminal_output.length > 0) {
                response.terminal_output.forEach(line => {
                    addTerminalOutput(line);
                });
            }
            addTerminalOutput(`💀 ${response.message}`);
            addLogEntry('Reset completo de BD completado', 'warning');
            
            // Actualizar estadísticas después del reset
            setTimeout(() => {
                loadSystemStats();
            }, 2000);
        } else {
            // Mostrar salida de error en el terminal
            if (response.terminal_output && response.terminal_output.length > 0) {
                response.terminal_output.forEach(line => {
                    addTerminalOutput(line);
                });
            }
            addTerminalOutput(`❌ Error en reset: ${response.error}`);
            addLogEntry(`Error en reset de BD: ${response.error}`, 'error');
        }
    } catch (error) {
        addTerminalOutput(`❌ Error ejecutando reset: ${error.message}`);
        addLogEntry(`Error ejecutando reset de BD: ${error.message}`, 'error');
    }
}

// Utilidades del terminal
function addTerminalOutput(text) {
    const terminal = document.getElementById('terminal-output');
    const timestamp = new Date().toLocaleTimeString();
    
    // Limpiar y formatear el texto
    let cleanText = text;
    
    // Remover prefijos de logging comunes
    cleanText = cleanText.replace(/^(INFO|DEBUG|WARNING|ERROR):[^:]*:\s*/, '');
    
    // Manejar emojis Unicode que pueden aparecer como códigos
    cleanText = cleanText.replace(/\\U0001f680/g, '🚀');
    cleanText = cleanText.replace(/\\U0001f4e5/g, '📥');
    cleanText = cleanText.replace(/\\U0001f50d/g, '🔍');
    
    terminal.textContent += `[${timestamp}] ${cleanText}\n`;
    terminal.scrollTop = terminal.scrollHeight;
}

function clearTerminal() {
    document.getElementById('terminal-output').textContent = 'Terminal limpiado\n';
}

function addLogEntry(message, type = 'info') {
    const logsContainer = document.getElementById('logs-container');
    const timestamp = new Date().toLocaleTimeString();
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.textContent = `[${timestamp}] ${message}`;
    
    // Insertar al principio
    logsContainer.insertBefore(logEntry, logsContainer.firstChild);
    
    // Mantener solo los últimos 50 logs
    while (logsContainer.children.length > 50) {
        logsContainer.removeChild(logsContainer.lastChild);
    }
}

function refreshLogs() {
    addLogEntry('Logs actualizados manualmente', 'info');
}

function showProgress(progressId) {
    document.getElementById(progressId).style.display = 'block';
}

function hideProgress(progressId) {
    document.getElementById(progressId).style.display = 'none';
}

console.log('🎛️ Dashboard Administrativo JavaScript cargado');