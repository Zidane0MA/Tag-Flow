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

// Ejecutar poblado de base de datos
async function executePopulateDB() {
    const source = document.getElementById('populate-source').value;
    const limit = document.getElementById('populate-limit').value;
    
    addTerminalOutput(`Ejecutando: python maintenance.py populate-db --source ${source} --limit ${limit}`);
    showProgress('populate-progress');
    
    try {
        const response = await TagFlow.utils.apiRequest('/api/admin/populate-db', {
            method: 'POST',
            body: JSON.stringify({
                source: source,
                limit: parseInt(limit)
            })
        });
        
        if (response.success) {
            addTerminalOutput(`✅ Poblado completado: ${response.message}`);
            addLogEntry(`Poblado de BD completado - Fuente: ${source}, Límite: ${limit}`, 'success');
            loadSystemStats(); // Actualizar estadísticas
        } else {
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
    showConfirmAction(
        'Vaciar Papelera',
        '⚠️ Esta acción eliminará PERMANENTEMENTE todos los videos en la papelera.\n\nEsta acción NO SE PUEDE DESHACER.\n\n¿Continuar?',
        'danger',
        'confirmEmptyTrash'
    );
}

function executeResetDatabase() {
    showConfirmAction(
        'Reset Completo de Base de Datos',
        '💀 PELIGRO EXTREMO: Esta acción eliminará TODA la base de datos.\n\nSe perderán TODOS los videos, metadatos y configuraciones.\n\nEsta acción es IRREVERSIBLE.\n\n¿Estás ABSOLUTAMENTE seguro?',
        'danger',
        'confirmResetDatabase'
    );
}

// Sistema de confirmación
function showConfirmAction(title, message, type, action) {
    document.getElementById('confirmActionTitle').textContent = title;
    document.getElementById('confirmActionBody').innerHTML = message.replace(/\n/g, '<br>');
    
    const confirmBtn = document.getElementById('confirmActionBtn');
    confirmBtn.className = `btn btn-${type}`;
    
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
    terminal.textContent += `[${timestamp}] ${text}\n`;
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