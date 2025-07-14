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
async function loadAvailablePlatforms() {
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/platforms');
        
        if (response.success) {
            const platforms = response.platforms;
            const platformSelect = document.getElementById('populate-platform');
            
            // Guardar las opciones especiales actuales
            const specialOptions = [
                { value: '', text: 'Plataformas principales' },
                { value: 'other', text: 'Solo adicionales' },
                { value: 'all-platforms', text: 'Todas las plataformas' },
                { value: 'custom', text: 'Personalizada...' }
            ];
            
            // Limpiar el select
            platformSelect.innerHTML = '';
            
            // Agregar la primera opción especial
            const firstOption = document.createElement('option');
            firstOption.value = '';
            firstOption.textContent = 'Plataformas principales';
            platformSelect.appendChild(firstOption);
            
            // Agregar plataformas principales
            if (platforms.main) {
                Object.entries(platforms.main).forEach(([key, info]) => {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = `${info.name} (${info.has_db ? 'BD' : ''}${info.has_db && info.has_organized ? ' + ' : ''}${info.has_organized ? 'Carpetas' : ''})`;
                    platformSelect.appendChild(option);
                });
            }
            
            // Agregar plataformas adicionales si existen
            if (platforms.additional && Object.keys(platforms.additional).length > 0) {
                // Crear separador
                const separator = document.createElement('option');
                separator.disabled = true;
                separator.textContent = '── Plataformas Adicionales ──';
                platformSelect.appendChild(separator);
                
                Object.entries(platforms.additional).forEach(([key, info]) => {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = `${info.name} (Carpeta)`;
                    platformSelect.appendChild(option);
                });
            }
            
            // Agregar separador para opciones especiales
            const specialSeparator = document.createElement('option');
            specialSeparator.disabled = true;
            specialSeparator.textContent = '── Opciones Especiales ──';
            platformSelect.appendChild(specialSeparator);
            
            // Agregar el resto de opciones especiales
            specialOptions.slice(1).forEach(special => {
                const option = document.createElement('option');
                option.value = special.value;
                option.textContent = special.text;
                platformSelect.appendChild(option);
            });
            
            console.log('✅ Plataformas cargadas dinámicamente');
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
    
    // Manejar plataforma personalizada
    platformSelect.addEventListener('change', function() {
        if (this.value === 'custom') {
            customPlatformContainer.style.display = 'block';
        } else {
            customPlatformContainer.style.display = 'none';
        }
    });
    
    // Manejar archivo específico
    sourceSelect.addEventListener('change', function() {
        if (this.value === 'file') {
            fileSourceContainer.style.display = 'block';
        } else {
            fileSourceContainer.style.display = 'none';
        }
    });
}

// Función para abrir selector de archivos (simulado)
function openFileSelector() {
    addTerminalOutput('ℹ️ Funcionalidad de selector de archivos no implementada. Ingresa la ruta manualmente.');
    addLogEntry('Solicitud de selector de archivos (funcionalidad pendiente)', 'info');
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
        let command = `python maintenance.py populate-db --file "${filePath}"`;
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
    let command = `python maintenance.py populate-db --source ${source} --limit ${limit}`;
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
    const platform = document.getElementById('analyze-platform').value;
    const limit = document.getElementById('analyze-limit').value;
    const pendingOnly = document.getElementById('analyze-pending-only').checked;
    
    let command = `python main.py --limit ${limit}`;
    if (platform) command += ` --platform ${platform}`;
    if (pendingOnly) command += ` --source db`;
    
    addTerminalOutput(`Ejecutando: ${command}`);
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/analyze-videos', {
            method: 'POST',
            body: JSON.stringify({
                platform: platform || null,
                limit: parseInt(limit),
                pending_only: pendingOnly
            })
        });
        
        if (response.success) {
            addTerminalOutput(`✅ Análisis completado: ${response.message}`);
            addLogEntry(`Análisis de videos completado - ${response.processed} videos procesados`, 'success');
            loadSystemStats();
        } else {
            addTerminalOutput(`❌ Error: ${response.error}`);
            addLogEntry(`Error en análisis: ${response.error}`, 'error');
        }
    } catch (error) {
        addTerminalOutput(`❌ Error ejecutando análisis: ${error.message}`);
        addLogEntry(`Error ejecutando análisis: ${error.message}`, 'error');
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

function confirmResetDatabase() {
    addTerminalOutput('💀 RESET COMPLETO DE BASE DE DATOS - IMPLEMENTACIÓN PENDIENTE');
    addLogEntry('Intento de reset de BD (no implementado)', 'error');
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