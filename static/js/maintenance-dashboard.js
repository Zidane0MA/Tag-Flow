/**
 * 🔧 Maintenance Dashboard - JavaScript
 * Dashboard en tiempo real para operaciones de mantenimiento
 */

class MaintenanceDashboard {
    constructor() {
        this.websocket = null;
        this.reconnectInterval = 5000;
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = 0;
        this.isConnected = false;
        this.clientId = null;
        this.autoScroll = true;
        this.maxLogEntries = 100;
        
        // Configuración
        this.settings = {
            updateInterval: 1000,
            enableNotifications: true,
            logLevel: 'info',
            websocketUrl: 'ws://localhost:8765'
        };
        
        // Datos en tiempo real
        this.systemHealth = {};
        this.operations = new Map();
        this.logs = [];
        
        // Inicializar
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadSettings();
        this.connectWebSocket();
        this.startPeriodicUpdates();
        this.updateCurrentTime();
        
        console.log('🔧 Maintenance Dashboard iniciado');
    }
    
    setupEventListeners() {
        // Navegación
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.showSection(link.getAttribute('href').substring(1));
                this.updateActiveNav(link);
            });
        });
        
        // Formulario de configuración
        document.getElementById('settingsForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSettings();
        });
        
        // Eventos de teclado
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshAll();
            }
        });
        
        // Notificaciones del navegador
        this.requestNotificationPermission();
    }
    
    connectWebSocket() {
        try {
            this.websocket = new WebSocket(this.settings.websocketUrl);
            
            this.websocket.onopen = (event) => {
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                this.addLog('Conectado al servidor WebSocket', 'info');
                
                // Suscribirse a todas las operaciones
                this.subscribeToAllOperations();
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = (event) => {
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.addLog('Conexión WebSocket cerrada', 'warning');
                
                // Intentar reconectar
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.addLog(`Reintentando conexión (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'info');
                        this.connectWebSocket();
                    }, this.reconnectInterval);
                } else {
                    this.addLog('Máximo de intentos de reconexión alcanzado', 'error');
                }
            };
            
            this.websocket.onerror = (error) => {
                this.addLog(`Error WebSocket: ${error.message || 'Desconocido'}`, 'error');
            };
            
        } catch (error) {
            this.addLog(`Error conectando WebSocket: ${error.message}`, 'error');
            this.updateConnectionStatus(false);
        }
    }
    
    handleWebSocketMessage(message) {
        const { type, data, timestamp } = message;
        
        switch (type) {
            case 'operation_progress':
                this.updateOperationProgress(data);
                break;
                
            case 'operation_complete':
                this.handleOperationComplete(data);
                break;
                
            case 'operation_failed':
                this.handleOperationFailed(data);
                break;
                
            case 'operation_cancelled':
                this.handleOperationCancelled(data);
                break;
                
            case 'system_status':
                this.updateSystemStatus(data);
                break;
                
            case 'notification':
                this.handleNotification(data);
                break;
                
            case 'heartbeat':
                this.handleHeartbeat(data);
                break;
                
            default:
                console.log('Mensaje WebSocket desconocido:', type, data);
        }
    }
    
    updateOperationProgress(data) {
        const { operation_id, progress } = data;
        
        // Actualizar datos de operación
        this.operations.set(operation_id, progress);
        
        // Actualizar UI
        this.updateOperationCard(operation_id, progress);
        this.updateOperationStats();
        
        // Log
        this.addLog(`Operación ${operation_id}: ${progress.progress_percentage.toFixed(1)}%`, 'info');
    }
    
    handleOperationComplete(data) {
        const { operation_id, result } = data;
        
        // Actualizar operación
        if (this.operations.has(operation_id)) {
            const operation = this.operations.get(operation_id);
            operation.status = 'completed';
            operation.result = result;
            this.operations.set(operation_id, operation);
        }
        
        // Actualizar UI
        this.updateOperationCard(operation_id, result);
        this.updateOperationStats();
        
        // Notificación
        this.showNotification(`Operación completada: ${result.operation_type}`, 'success');
        this.addLog(`Operación ${operation_id} completada exitosamente`, 'success');
    }
    
    handleOperationFailed(data) {
        const { operation_id, error } = data;
        
        // Actualizar operación
        if (this.operations.has(operation_id)) {
            const operation = this.operations.get(operation_id);
            operation.status = 'failed';
            operation.error_message = error.error_message;
            this.operations.set(operation_id, operation);
        }
        
        // Actualizar UI
        this.updateOperationCard(operation_id, error);
        this.updateOperationStats();
        
        // Notificación
        this.showNotification(`Operación falló: ${error.operation_type}`, 'error');
        this.addLog(`Operación ${operation_id} falló: ${error.error_message}`, 'error');
    }
    
    handleOperationCancelled(data) {
        const { operation_id } = data;
        
        // Actualizar operación
        if (this.operations.has(operation_id)) {
            const operation = this.operations.get(operation_id);
            operation.status = 'cancelled';
            this.operations.set(operation_id, operation);
        }
        
        // Actualizar UI
        this.updateOperationCard(operation_id, data);
        this.updateOperationStats();
        
        // Notificación
        this.showNotification(`Operación cancelada: ${operation_id}`, 'warning');
        this.addLog(`Operación ${operation_id} cancelada`, 'warning');
    }
    
    updateSystemStatus(data) {
        this.systemHealth = data;
        this.updateSystemHealthUI();
    }
    
    handleNotification(data) {
        const { message, level, data: notificationData } = data;
        
        // Mostrar notificación
        this.showNotification(message, level);
        
        // Agregar al log
        this.addLog(message, level);
        
        // Notificación del navegador
        if (this.settings.enableNotifications && level === 'error') {
            this.showBrowserNotification(message, level);
        }
    }
    
    handleHeartbeat(data) {
        if (data.type === 'ping') {
            // Actualizar estadísticas del servidor
            if (data.server_stats) {
                this.updateWebSocketStats(data.server_stats);
            }
        }
    }
    
    updateOperationCard(operationId, data) {
        const container = document.getElementById('operationsList');
        let card = document.getElementById(`operation-${operationId}`);
        
        if (!card) {
            card = this.createOperationCard(operationId, data);
            container.appendChild(card);
        } else {
            this.updateExistingOperationCard(card, data);
        }
    }
    
    createOperationCard(operationId, data) {
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-3';
        card.id = `operation-${operationId}`;
        
        const statusClass = this.getStatusClass(data.status);
        const progressWidth = data.progress_percentage || 0;
        
        card.innerHTML = `
            <div class="operation-card">
                <div class="operation-header">
                    <div class="operation-title">${data.operation_type}</div>
                    <span class="operation-status ${statusClass}">${data.status}</span>
                </div>
                
                <div class="progress mb-3">
                    <div class="progress-bar" role="progressbar" style="width: ${progressWidth}%">
                        ${progressWidth.toFixed(1)}%
                    </div>
                </div>
                
                <div class="operation-details">
                    <div class="text-muted small">${data.current_step || 'Esperando...'}</div>
                    <div class="text-muted small mt-1">
                        ${data.processed_items || 0} / ${data.total_items || 0} items
                    </div>
                </div>
                
                <div class="operation-metrics">
                    <div class="metric-small">
                        <div class="value">${data.items_per_second?.toFixed(1) || '0.0'}</div>
                        <div class="label">Items/s</div>
                    </div>
                    <div class="metric-small">
                        <div class="value">${data.memory_usage_mb?.toFixed(1) || '0.0'}</div>
                        <div class="label">MB</div>
                    </div>
                    <div class="metric-small">
                        <div class="value">${data.cpu_usage_percent?.toFixed(1) || '0.0'}</div>
                        <div class="label">CPU%</div>
                    </div>
                </div>
                
                <div class="operation-actions mt-3">
                    <button class="btn btn-sm btn-warning" onclick="dashboard.pauseOperation('${operationId}')">
                        <i class="fas fa-pause"></i>
                    </button>
                    <button class="btn btn-sm btn-success" onclick="dashboard.resumeOperation('${operationId}')">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="dashboard.cancelOperation('${operationId}')">
                        <i class="fas fa-stop"></i>
                    </button>
                </div>
            </div>
        `;
        
        return card;
    }
    
    updateExistingOperationCard(card, data) {
        const statusClass = this.getStatusClass(data.status);
        const progressWidth = data.progress_percentage || 0;
        
        // Actualizar estado
        const statusElement = card.querySelector('.operation-status');
        statusElement.className = `operation-status ${statusClass}`;
        statusElement.textContent = data.status;
        
        // Actualizar progreso
        const progressBar = card.querySelector('.progress-bar');
        progressBar.style.width = `${progressWidth}%`;
        progressBar.textContent = `${progressWidth.toFixed(1)}%`;
        
        // Actualizar detalles
        const details = card.querySelector('.operation-details');
        details.innerHTML = `
            <div class="text-muted small">${data.current_step || 'Esperando...'}</div>
            <div class="text-muted small mt-1">
                ${data.processed_items || 0} / ${data.total_items || 0} items
            </div>
        `;
        
        // Actualizar métricas
        const metrics = card.querySelectorAll('.metric-small .value');
        metrics[0].textContent = data.items_per_second?.toFixed(1) || '0.0';
        metrics[1].textContent = data.memory_usage_mb?.toFixed(1) || '0.0';
        metrics[2].textContent = data.cpu_usage_percent?.toFixed(1) || '0.0';
    }
    
    updateOperationStats() {
        const activeOps = Array.from(this.operations.values()).filter(op => 
            ['pending', 'running', 'paused'].includes(op.status)
        ).length;
        
        const completedOps = Array.from(this.operations.values()).filter(op => 
            op.status === 'completed'
        ).length;
        
        const failedOps = Array.from(this.operations.values()).filter(op => 
            op.status === 'failed'
        ).length;
        
        // Actualizar UI
        document.getElementById('activeOperations').textContent = activeOps;
        document.getElementById('totalOperations').textContent = this.operations.size;
        document.getElementById('completedOperations').textContent = completedOps;
        document.getElementById('failedOperations').textContent = failedOps;
    }
    
    updateSystemHealthUI() {
        if (!this.systemHealth.system) return;
        
        const { system, health_score } = this.systemHealth;
        
        // Actualizar puntuación de salud
        const healthElement = document.getElementById('healthScore');
        healthElement.textContent = health_score || 0;
        healthElement.className = `health-score ${this.getHealthClass(health_score)}`;
        
        // Actualizar métricas del sistema
        document.getElementById('cpuUsage').textContent = `${system.cpu_percent?.toFixed(1) || 0}%`;
        document.getElementById('memoryUsage').textContent = `${system.memory_percent?.toFixed(1) || 0}%`;
        document.getElementById('diskUsage').textContent = `${system.disk_percent?.toFixed(1) || 0}%`;
        
        // Actualizar barras de progreso
        document.getElementById('cpuProgress').style.width = `${system.cpu_percent || 0}%`;
        document.getElementById('memoryProgress').style.width = `${system.memory_percent || 0}%`;
        document.getElementById('diskProgress').style.width = `${system.disk_percent || 0}%`;
        
        // Actualizar métricas de BD y thumbnails
        if (this.systemHealth.database) {
            const { database } = this.systemHealth;
            document.getElementById('dbTotalVideos').textContent = database.total_videos || 0;
            document.getElementById('dbSize').textContent = `${(database.database_size_mb || 0).toFixed(1)} MB`;
        }
        
        if (this.systemHealth.thumbnails) {
            const { thumbnails } = this.systemHealth;
            document.getElementById('thumbnailsTotal').textContent = thumbnails.total_files || 0;
            document.getElementById('thumbnailsSize').textContent = `${(thumbnails.total_size_mb || 0).toFixed(1)} MB`;
        }
    }
    
    updateWebSocketStats(stats) {
        document.getElementById('wsActiveConnections').textContent = stats.active_connections || 0;
        document.getElementById('wsTotalConnections').textContent = stats.total_connections || 0;
        document.getElementById('wsMessagesSent').textContent = stats.messages_sent || 0;
        document.getElementById('wsMessagesFailed').textContent = stats.messages_failed || 0;
    }
    
    addLog(message, level = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            message,
            level,
            id: Date.now() + Math.random()
        };
        
        this.logs.push(logEntry);
        
        // Mantener límite de logs
        if (this.logs.length > this.maxLogEntries) {
            this.logs.shift();
        }
        
        // Actualizar UI
        this.updateLogDisplay();
    }
    
    updateLogDisplay() {
        const container = document.getElementById('logContainer');
        
        // Limpiar contenedor
        container.innerHTML = '';
        
        // Agregar logs
        this.logs.forEach(log => {
            const logElement = document.createElement('div');
            logElement.className = `log-entry log-${log.level}`;
            logElement.innerHTML = `
                <span class="text-muted">[${log.timestamp}]</span>
                <span class="text-${this.getLogColor(log.level)}">[${log.level.toUpperCase()}]</span>
                ${log.message}
            `;
            container.appendChild(logElement);
        });
        
        // Auto-scroll
        if (this.autoScroll) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    showNotification(message, level = 'info') {
        const container = document.getElementById('notificationContainer');
        const toast = document.createElement('div');
        toast.className = `toast show mb-2`;
        toast.setAttribute('role', 'alert');
        
        const levelIcon = this.getLevelIcon(level);
        const levelColor = this.getLogColor(level);
        
        toast.innerHTML = `
            <div class="toast-header">
                <i class="fas ${levelIcon} text-${levelColor} me-2"></i>
                <strong class="me-auto">Notificación</strong>
                <small>${new Date().toLocaleTimeString()}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto-remove después de 5 segundos
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
    
    showBrowserNotification(message, level) {
        if (Notification.permission === 'granted') {
            const notification = new Notification(`Tag-Flow V2 - ${level.toUpperCase()}`, {
                body: message,
                icon: '/static/icons/maintenance.png',
                tag: 'maintenance-dashboard'
            });
            
            setTimeout(() => notification.close(), 5000);
        }
    }
    
    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    // Utilidades
    getStatusClass(status) {
        return `status-${status}`;
    }
    
    getHealthClass(score) {
        if (score >= 90) return 'health-excellent';
        if (score >= 70) return 'health-good';
        if (score >= 50) return 'health-warning';
        return 'health-critical';
    }
    
    getLogColor(level) {
        const colors = {
            'info': 'info',
            'success': 'success',
            'warning': 'warning',
            'error': 'danger'
        };
        return colors[level] || 'secondary';
    }
    
    getLevelIcon(level) {
        const icons = {
            'info': 'fa-info-circle',
            'success': 'fa-check-circle',
            'warning': 'fa-exclamation-triangle',
            'error': 'fa-exclamation-circle'
        };
        return icons[level] || 'fa-bell';
    }
    
    // Navegación
    showSection(sectionId) {
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });
        document.getElementById(sectionId).style.display = 'block';
    }
    
    updateActiveNav(activeLink) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        activeLink.classList.add('active');
    }
    
    // Acciones
    pauseOperation(operationId) {
        this.sendMessage({
            action: 'pause_operation',
            operation_id: operationId
        });
    }
    
    resumeOperation(operationId) {
        this.sendMessage({
            action: 'resume_operation',
            operation_id: operationId
        });
    }
    
    cancelOperation(operationId) {
        if (confirm('¿Estás seguro de que quieres cancelar esta operación?')) {
            this.sendMessage({
                action: 'cancel_operation',
                operation_id: operationId
            });
        }
    }
    
    pauseAllOperations() {
        if (confirm('¿Pausar todas las operaciones activas?')) {
            this.operations.forEach((operation, operationId) => {
                if (operation.status === 'running') {
                    this.pauseOperation(operationId);
                }
            });
        }
    }
    
    cancelAllOperations() {
        if (confirm('¿Cancelar todas las operaciones activas?')) {
            this.operations.forEach((operation, operationId) => {
                if (['running', 'pending', 'paused'].includes(operation.status)) {
                    this.cancelOperation(operationId);
                }
            });
        }
    }
    
    refreshOperations() {
        this.sendMessage({
            action: 'get_operations'
        });
    }
    
    refreshAll() {
        this.sendMessage({
            action: 'get_status'
        });
        this.refreshOperations();
    }
    
    clearLogs() {
        this.logs = [];
        this.updateLogDisplay();
    }
    
    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        const button = document.querySelector('[onclick="toggleAutoScroll()"]');
        button.innerHTML = this.autoScroll ? 
            '<i class="fas fa-arrows-alt-v"></i> Auto-scroll' : 
            '<i class="fas fa-arrows-alt-v"></i> Manual';
    }
    
    // Configuración
    loadSettings() {
        const saved = localStorage.getItem('maintenanceDashboardSettings');
        if (saved) {
            this.settings = { ...this.settings, ...JSON.parse(saved) };
        }
        
        // Actualizar form
        document.getElementById('updateInterval').value = this.settings.updateInterval / 1000;
        document.getElementById('enableNotifications').checked = this.settings.enableNotifications;
        document.getElementById('logLevel').value = this.settings.logLevel;
    }
    
    saveSettings() {
        this.settings.updateInterval = document.getElementById('updateInterval').value * 1000;
        this.settings.enableNotifications = document.getElementById('enableNotifications').checked;
        this.settings.logLevel = document.getElementById('logLevel').value;
        
        localStorage.setItem('maintenanceDashboardSettings', JSON.stringify(this.settings));
        
        this.showNotification('Configuración guardada', 'success');
    }
    
    // Comunicación
    sendMessage(message) {
        if (this.isConnected && this.websocket) {
            this.websocket.send(JSON.stringify(message));
        }
    }
    
    subscribeToAllOperations() {
        this.sendMessage({
            action: 'subscribe_all'
        });
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (connected) {
            statusElement.className = 'connection-status connection-connected';
            statusElement.innerHTML = '<i class="fas fa-wifi"></i> Conectado';
        } else {
            statusElement.className = 'connection-status connection-disconnected';
            statusElement.innerHTML = '<i class="fas fa-wifi"></i> Desconectado';
        }
    }
    
    startPeriodicUpdates() {
        setInterval(() => {
            if (this.isConnected) {
                this.sendMessage({
                    action: 'get_status'
                });
            }
        }, this.settings.updateInterval);
    }
    
    updateCurrentTime() {
        const updateTime = () => {
            document.getElementById('currentTime').textContent = 
                new Date().toLocaleTimeString();
        };
        
        updateTime();
        setInterval(updateTime, 1000);
    }
}

// Inicializar dashboard
const dashboard = new MaintenanceDashboard();
window.dashboard = dashboard;