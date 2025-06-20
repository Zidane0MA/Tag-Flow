/**
 * Tag-Flow V2 - JavaScript Principal
 * Funcionalidades básicas y utilidades globales
 */

// Variables globales
window.TagFlow = {
    apiBase: '/api',
    currentModal: null,
    notifications: {
        container: null,
        toast: null
    }
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Inicializar la aplicación
 */
function initializeApp() {
    console.log('🎬 Tag-Flow V2 iniciado');
    
    // Inicializar componentes
    initializeNotifications();
    initializeTooltips();
    initializeLoadingOverlay();
    
    // Event listeners globales
    setupGlobalEventListeners();
    
    console.log('✅ Aplicación inicializada correctamente');
}

/**
 * Inicializar sistema de notificaciones
 */
function initializeNotifications() {
    const toastContainer = document.querySelector('.toast-container');
    const toast = document.getElementById('notification-toast');
    
    if (toastContainer && toast) {
        TagFlow.notifications.container = toastContainer;
        TagFlow.notifications.toast = new bootstrap.Toast(toast);
    }
}

/**
 * Inicializar tooltips de Bootstrap
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Inicializar overlay de carga
 */
function initializeLoadingOverlay() {
    if (!document.getElementById('loading-overlay')) {
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.style.display = 'none';
        overlay.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        `;
        document.body.appendChild(overlay);
    }
}

/**
 * Event listeners globales
 */
function setupGlobalEventListeners() {
    // Cerrar modales con escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && TagFlow.currentModal) {
            TagFlow.currentModal.hide();
        }
    });
    
    // Manejo de errores AJAX globales
    setupAjaxErrorHandling();
}

/**
 * Manejo de errores AJAX globales
 */
function setupAjaxErrorHandling() {
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Error no manejado:', event.reason);
        showNotification('Error inesperado en la aplicación', 'error');
    });
}

/**
 * Mostrar overlay de carga
 */
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

/**
 * Ocultar overlay de carga
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * Mostrar notificación toast
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo: 'success', 'error', 'warning', 'info'
 */
function showNotification(message, type = 'info') {
    if (!TagFlow.notifications.toast) {
        console.warn('Sistema de notificaciones no inicializado');
        return;
    }
    
    const toastElement = document.getElementById('notification-toast');
    const messageElement = document.getElementById('toast-message');
    const iconElement = toastElement.querySelector('.toast-header i');
    
    // Configurar mensaje
    messageElement.textContent = message;
    
    // Configurar icono y color según el tipo
    const typeConfig = {
        success: { icon: 'fas fa-check-circle text-success', class: 'toast-success' },
        error: { icon: 'fas fa-exclamation-circle text-danger', class: 'toast-error' },
        warning: { icon: 'fas fa-exclamation-triangle text-warning', class: 'toast-warning' },
        info: { icon: 'fas fa-info-circle text-primary', class: 'toast-info' }
    };
    
    const config = typeConfig[type] || typeConfig.info;
    iconElement.className = config.icon;
    
    // Limpiar clases anteriores y agregar nueva
    toastElement.className = `toast ${config.class}`;
    
    // Mostrar toast
    TagFlow.notifications.toast.show();
}

/**
 * Realizar petición AJAX con manejo de errores
 * @param {string} url - URL de la petición
 * @param {object} options - Opciones de fetch
 * @returns {Promise} Promesa con la respuesta
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const config = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        showLoading();
        
        const response = await fetch(url, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        
        if (!data.success) {
            throw new Error(data.error || 'Error en la respuesta del servidor');
        }
        
        return data;
        
    } catch (error) {
        console.error('Error en petición API:', error);
        showNotification(`Error: ${error.message}`, 'error');
        throw error;
    } finally {
        hideLoading();
    }
}

/**
 * Debounce para funciones que se ejecutan frecuentemente
 * @param {Function} func - Función a ejecutar
 * @param {number} wait - Tiempo de espera en ms
 * @returns {Function} Función con debounce aplicado
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Formatear duración en segundos a formato legible
 * @param {number} seconds - Duración en segundos
 * @returns {string} Duración formateada
 */
function formatDuration(seconds) {
    if (!seconds || seconds < 0) return 'N/A';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (minutes > 0) {
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    } else {
        return `${remainingSeconds}s`;
    }
}

/**
 * Formatear tamaño de archivo
 * @param {number} bytes - Tamaño en bytes
 * @returns {string} Tamaño formateado
 */
function formatFileSize(bytes) {
    if (!bytes || bytes < 0) return 'N/A';
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * Validar que una cadena no esté vacía
 * @param {string} str - Cadena a validar
 * @returns {boolean} True si es válida
 */
function isValidString(str) {
    return str && typeof str === 'string' && str.trim().length > 0;
}

/**
 * Limpiar y normalizar texto
 * @param {string} text - Texto a limpiar
 * @returns {string} Texto limpio
 */
function cleanText(text) {
    if (!text) return '';
    return text.trim().replace(/\s+/g, ' ');
}

// Exportar funciones para uso global
window.TagFlow.utils = {
    showLoading,
    hideLoading,
    showNotification,
    apiRequest,
    debounce,
    formatDuration,
    formatFileSize,
    isValidString,
    cleanText
};

console.log('📦 Tag-Flow V2 JavaScript cargado');