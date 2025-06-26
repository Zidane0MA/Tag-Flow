/**
 * Tag-Flow V2 - JavaScript de la Galería
 * Funcionalidades específicas para la gestión de videos
 */

// Variables específicas de la galería
let currentVideoData = null;
let editModal = null;
let filteredVideos = [];

// Inicialización específica de la galería
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('videos-container')) {
        initializeGallery();
    }
});

/**
 * Inicializar funcionalidades de la galería
 */
function initializeGallery() {
    console.log('🎨 Inicializando galería...');
    
    // Inicializar modal de edición
    const editModalElement = document.getElementById('editVideoModal');
    if (editModalElement) {
        editModal = new bootstrap.Modal(editModalElement);
        TagFlow.currentModal = editModal;
    }
    
    // Event listeners específicos
    setupGalleryEventListeners();
    setupFilterEventListeners();
    
    // Aplicar filtros iniciales si existen
    applyInitialFilters();
    
    console.log('✅ Galería inicializada');
}

/**
 * Event listeners específicos de la galería
 */
function setupGalleryEventListeners() {
    // Búsqueda mejorada - enviar al servidor
    const searchInput = document.getElementById('search-input');
    const searchForm = document.getElementById('filter-form');
    
    if (searchInput && searchForm) {
        // Enviar formulario al presionar Enter
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchForm.submit();
            }
        });
        
        // Limpiar búsqueda con Escape
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                searchInput.value = '';
                searchForm.submit();
            }
        });
    }
    
    // Auto-submit en filtros con debounce para búsqueda
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                if (searchInput.value.length === 0 || searchInput.value.length >= 3) {
                    searchForm.submit();
                }
            }, 500); // Esperar 500ms después de que el usuario deje de escribir
        });
    }
}

/**
 * Event listeners para filtros - simplificados
 */
function setupFilterEventListeners() {
    // Los filtros se manejan automáticamente con onchange="this.form.submit()" en el HTML
    console.log('✅ Filtros configurados para envío automático al servidor');
}

/**
 * Aplicar filtros iniciales desde URL - ya no necesario
 */
function applyInitialFilters() {
    // Los filtros se aplican automáticamente desde el servidor
    console.log('✅ Filtros iniciales aplicados desde el servidor');
}

/**
 * Aplicar filtros - simplificado para recargar página
 */
function applyFilters() {
    const form = document.getElementById('filter-form');
    if (form) {
        form.submit();
    }
}

/**
 * Filtrar videos visualmente - removido, ahora se maneja en el servidor
 */
function filterVideosVisually() {
    // Esta función ya no es necesaria
    console.log('ℹ️ Filtros manejados por el servidor');
}

/**
 * Actualizar URL - ya no es necesario
 */
function updateURL() {
    // El formulario maneja la URL automáticamente
}

/**
 * Realizar búsqueda - simplificado
 */
function performSearch() {
    const form = document.getElementById('filter-form');
    if (form) {
        form.submit();
    }
}

/**
 * Limpiar todos los filtros - redirigir a página limpia
 */
function clearAllFilters() {
    window.location.href = window.location.pathname;
}
/**
 * Reproducir video en modal
 */
async function playVideo(videoId) {
    if (!videoId) {
        TagFlow.utils.showNotification('ID de video no válido', 'error');
        return;
    }
    
    try {
        // Convertir videoId a número si es string
        const numericVideoId = parseInt(videoId);
        if (isNaN(numericVideoId)) {
            TagFlow.utils.showNotification('ID de video inválido', 'error');
            return;
        }
        
        // Obtener información del video
        const response = await TagFlow.utils.apiRequest(`${TagFlow.apiBase}/video/${numericVideoId}/play`);
        
        if (!response.success) {
            TagFlow.utils.showNotification('Error obteniendo información del video', 'error');
            return;
        }
        
        // Configurar modal de video
        const modal = new bootstrap.Modal(document.getElementById('videoPlayerModal'));
        const videoPlayer = document.getElementById('video-player');
        const videoSource = document.getElementById('video-source');
        const videoInfo = document.getElementById('video-info');
        
        // Configurar fuente del video
        videoSource.src = `/video-stream/${numericVideoId}`;
        videoPlayer.load();
        
        // Mostrar información del video
        videoInfo.innerHTML = `
            <div class="row text-start">
                <div class="col-md-6">
                    <strong>Archivo:</strong> ${response.file_name}<br>
                    <strong>Tamaño:</strong> ${TagFlow.utils.formatFileSize(response.file_size)}<br>
                </div>
                <div class="col-md-6">
                    <strong>Duración:</strong> ${TagFlow.utils.formatDuration(response.duration)}<br>
                    <strong>Tipo:</strong> ${response.mime_type || 'Video'}
                </div>
            </div>
        `;
        
        // Guardar ruta para función de abrir en sistema
        window.currentVideoPath = response.video_path;
        window.currentVideoId = numericVideoId;
        
        // Mostrar modal
        modal.show();
        
    } catch (error) {
        console.error('Error reproduciendo video:', error);
        TagFlow.utils.showNotification('Error al cargar el video', 'error');
    }
}

/**
 * Abrir video en reproductor del sistema
 */
async function openVideoInSystem() {
    if (!window.currentVideoId) {
        TagFlow.utils.showNotification('No hay video seleccionado', 'error');
        return;
    }
    
    try {
        const numericVideoId = parseInt(window.currentVideoId);
        if (isNaN(numericVideoId)) {
            TagFlow.utils.showNotification('ID de video inválido', 'error');
            return;
        }
        
        await TagFlow.utils.apiRequest(
            `${TagFlow.apiBase}/video/${numericVideoId}/open-folder`,
            { method: 'POST' }
        );
        TagFlow.utils.showNotification('Abriendo carpeta del video...', 'info');
    } catch (error) {
        console.error('Error abriendo video en sistema:', error);
        TagFlow.utils.showNotification('Error abriendo carpeta', 'error');
    }
}

/**
 * Abrir modal de edición de video
 */
async function editVideo(videoId) {
    if (!videoId || !editModal) {
        TagFlow.utils.showNotification('Error abriendo editor', 'error');
        return;
    }
    
    try {
        // Convertir videoId a número si es string
        const numericVideoId = parseInt(videoId);
        if (isNaN(numericVideoId)) {
            TagFlow.utils.showNotification('ID de video inválido', 'error');
            return;
        }
        
        // Obtener datos del video específico
        const response = await TagFlow.utils.apiRequest(`${TagFlow.apiBase}/video/${numericVideoId}`);
        
        if (!response.success || !response.video) {
            TagFlow.utils.showNotification('Video no encontrado', 'error');
            return;
        }
        
        // Cargar datos en el modal
        loadVideoDataInModal(response.video);
        
        // Mostrar modal
        editModal.show();
        currentVideoData = response.video;
        
    } catch (error) {
        console.error('Error cargando video para edición:', error);
        TagFlow.utils.showNotification('Error cargando datos del video', 'error');
    }
}

/**
 * Cargar datos del video en el modal de edición
 */
function loadVideoDataInModal(video) {
    // Campos de solo lectura
    document.getElementById('edit-video-id').value = video.id;
    document.getElementById('edit-creator-name').value = video.creator_name || '';
    document.getElementById('edit-file-name').value = video.file_name || '';
    document.getElementById('edit-platform').value = video.platform || 'tiktok';
    
    // Campos editables
    document.getElementById('edit-final-music').value = video.final_music || '';
    document.getElementById('edit-final-music-artist').value = video.final_music_artist || '';
    document.getElementById('edit-difficulty-level').value = video.difficulty_level || '';
    document.getElementById('edit-status').value = video.edit_status || 'nulo';
    document.getElementById('edit-notes').value = video.notes || '';
    
    // Personajes (convertir array a string)
    const characters = video.final_characters || video.detected_characters || [];
    const charactersText = Array.isArray(characters) ? characters.join(', ') : '';
    document.getElementById('edit-final-characters').value = charactersText;
    
    // Información detectada automáticamente
    const detectedMusicInfo = document.getElementById('detected-music-info');
    if (video.detected_music) {
        const confidence = video.detected_music_confidence ? 
            ` (${Math.round(video.detected_music_confidence * 100)}% confianza)` : '';
        detectedMusicInfo.innerHTML = `
            <strong>${video.detected_music}</strong><br>
            <small class="text-muted">
                ${video.detected_music_artist || 'Artista desconocido'} 
                ${confidence}
                <br>Fuente: ${video.music_source || 'N/A'}
            </small>
        `;
    } else {
        detectedMusicInfo.textContent = 'No detectada';
    }
    
    const detectedCharactersInfo = document.getElementById('detected-characters-info');
    if (video.detected_characters && video.detected_characters.length > 0) {
        detectedCharactersInfo.innerHTML = video.detected_characters.map(char => 
            `<span class="badge bg-secondary me-1">${char}</span>`
        ).join('');
    } else {
        detectedCharactersInfo.textContent = 'No detectados';
    }
}

/**
 * Guardar cambios del video
 */
async function saveVideoChanges() {
    if (!currentVideoData) {
        TagFlow.utils.showNotification('No hay video seleccionado', 'error');
        return;
    }
    
    try {
        // Recopilar datos del formulario
        const formData = {
            final_music: TagFlow.utils.cleanText(document.getElementById('edit-final-music').value),
            final_music_artist: TagFlow.utils.cleanText(document.getElementById('edit-final-music-artist').value),
            difficulty_level: document.getElementById('edit-difficulty-level').value,
            edit_status: document.getElementById('edit-status').value,
            notes: TagFlow.utils.cleanText(document.getElementById('edit-notes').value)
        };
        
        // Procesar personajes (string a array)
        const charactersText = TagFlow.utils.cleanText(document.getElementById('edit-final-characters').value);
        if (charactersText) {
            formData.final_characters = charactersText.split(',').map(c => c.trim()).filter(c => c);
        } else {
            formData.final_characters = [];
        }
        
        // Enviar actualización
        const response = await TagFlow.utils.apiRequest(
            `${TagFlow.apiBase}/video/${currentVideoData.id}/update`,
            {
                method: 'POST',
                body: JSON.stringify(formData)
            }
        );
        
        // Actualizar UI inmediatamente
        updateVideoCardInDOM(response.video);
        
        // Cerrar modal
        editModal.hide();
        currentVideoData = null;
        
        TagFlow.utils.showNotification('Video actualizado exitosamente', 'success');
        
        // Reapliar filtros para asegurar que los cambios se reflejen
        setTimeout(() => {
            applyFilters();
        }, 100);
        
    } catch (error) {
        console.error('Error guardando cambios:', error);
        TagFlow.utils.showNotification('Error guardando cambios', 'error');
    }
}

/**
 * Actualizar card de video en el DOM
 */
function updateVideoCardInDOM(updatedVideo) {
    const videoCard = document.querySelector(`[data-video-id="${updatedVideo.id}"]`);
    if (videoCard) {
        // Actualizar badges de estado de edición
        const statusBadges = videoCard.querySelectorAll('.badge');
        statusBadges.forEach(badge => {
            if (badge.textContent.includes('Sin Edición') || badge.textContent.includes('En proceso') || badge.textContent.includes('Completado')) {
                const statusMap = {
                    'nulo': { text: 'Sin Edición', class: 'bg-secondary' },
                    'en_proceso': { text: 'En proceso', class: 'bg-warning' },
                    'hecho': { text: 'Completado', class: 'bg-success' }
                };
                const status = statusMap[updatedVideo.edit_status] || statusMap['nulo'];
                badge.textContent = status.text;
                badge.className = `badge ${status.class}`;
            }
        });
        
        // Actualizar información de música
        const musicInfo = videoCard.querySelector('.fa-music')?.parentElement;
        if (musicInfo) {
            const music = updatedVideo.final_music || updatedVideo.detected_music;
            const artist = updatedVideo.final_music_artist || updatedVideo.detected_music_artist;
            const isAutoDetected = !updatedVideo.final_music && updatedVideo.detected_music;
            
            if (music) {
                musicInfo.innerHTML = `
                    <i class="fas fa-music text-primary me-1"></i>
                    <small>
                        <strong>${music}</strong>
                        ${artist ? ` - ${artist}` : ''}
                        ${isAutoDetected ? ' <span class="text-muted">(auto)</span>' : ''}
                    </small>
                `;
            }
        }
        
        // Actualizar información de personajes
        const charactersInfo = videoCard.querySelector('.fa-user-friends')?.parentElement;
        if (charactersInfo) {
            const characters = updatedVideo.final_characters || updatedVideo.detected_characters || [];
            if (characters.length > 0) {
                const displayChars = characters.slice(0, 2).join(', ');
                const moreText = characters.length > 2 ? `<span class="text-muted">+${characters.length - 2} más</span>` : '';
                charactersInfo.innerHTML = `
                    <i class="fas fa-user-friends text-success me-1"></i>
                    <small>${displayChars} ${moreText}</small>
                `;
            }
        }
        
        // Actualizar notas si existen
        const notesInfo = videoCard.querySelector('.fa-sticky-note')?.parentElement;
        if (updatedVideo.notes && updatedVideo.notes.trim()) {
            if (!notesInfo) {
                // Crear elemento de notas si no existe
                const cardBody = videoCard.querySelector('.card-body');
                const notesDiv = document.createElement('div');
                notesDiv.className = 'mt-2';
                notesDiv.innerHTML = `
                    <small class="text-info">
                        <i class="fas fa-sticky-note me-1"></i>${updatedVideo.notes.substring(0, 50)}...
                    </small>
                `;
                cardBody.appendChild(notesDiv);
            } else {
                notesInfo.innerHTML = `
                    <i class="fas fa-sticky-note me-1"></i>${updatedVideo.notes.substring(0, 50)}...
                `;
            }
        } else if (notesInfo) {
            // Remover notas si están vacías
            notesInfo.parentElement.remove();
        }
        
        // Actualizar atributos de datos para filtros
        videoCard.dataset.status = updatedVideo.edit_status || 'nulo';
        videoCard.dataset.processingStatus = updatedVideo.processing_status || 'pendiente';
        videoCard.dataset.difficulty = updatedVideo.difficulty_level || '';
        
        // Animar actualización
        videoCard.style.transform = 'scale(0.98)';
        setTimeout(() => {
            videoCard.style.transform = 'scale(1)';
        }, 200);
    }
}

/**
 * Actualización rápida de estado
 */
async function quickUpdateStatus(videoId, newStatus) {
    try {
        // Convertir videoId a número si es string
        const numericVideoId = parseInt(videoId);
        if (isNaN(numericVideoId)) {
            TagFlow.utils.showNotification('ID de video inválido', 'error');
            return;
        }
        
        // Validar estado
        const validStatuses = ['nulo', 'en_proceso', 'hecho'];
        if (!validStatuses.includes(newStatus)) {
            TagFlow.utils.showNotification('Estado inválido', 'error');
            return;
        }
        
        console.log(`Actualizando video ${numericVideoId} a estado: ${newStatus}`);
        
        const response = await TagFlow.utils.apiRequest(
            `${TagFlow.apiBase}/video/${numericVideoId}/update`,
            {
                method: 'POST',
                body: JSON.stringify({ edit_status: newStatus })
            }
        );
        
        if (!response.success) {
            throw new Error(response.error || 'Error desconocido actualizando video');
        }
        
        // Actualizar UI completa
        updateVideoCardInDOM(response.video);
        
        // Actualizar botones de estado activo
        const wrapper = document.querySelector(`[data-video-id="${numericVideoId}"]`);
        if (wrapper) {
            const statusButtons = wrapper.querySelectorAll('.btn-group .btn');
            statusButtons.forEach(btn => btn.classList.remove('active'));
            
            const statusMap = { 'nulo': 0, 'en_proceso': 1, 'hecho': 2 };
            const buttonIndex = statusMap[newStatus];
            if (buttonIndex !== undefined && statusButtons[buttonIndex]) {
                statusButtons[buttonIndex].classList.add('active');
            }
            
            // Actualizar datasets para filtros
            wrapper.dataset.status = newStatus;
        }
        
        const statusLabels = {
            'nulo': 'Sin Edición',
            'en_proceso': 'En proceso', 
            'hecho': 'Completado'
        };
        
        TagFlow.utils.showNotification(
            `Estado actualizado: ${statusLabels[newStatus]}`, 
            'success'
        );
        
        // Reapliar filtros si hay alguno activo
        const hasActiveFilters = document.getElementById('filter-status')?.value || 
                               document.getElementById('filter-processing')?.value ||
                               document.getElementById('search-input')?.value;
        
        if (hasActiveFilters) {
            setTimeout(() => applyFilters(), 100);
        }
        
    } catch (error) {
        console.error('Error actualizando estado:', error);
        TagFlow.utils.showNotification(`Error: ${error.message}`, 'error');
    }
}

/**
 * Abrir carpeta del video en el explorador
 */
async function openVideoFolder(videoId) {
    try {
        // Convertir videoId a número si es string
        const numericVideoId = parseInt(videoId);
        if (isNaN(numericVideoId)) {
            TagFlow.utils.showNotification('ID de video inválido', 'error');
            return;
        }
        
        const response = await TagFlow.utils.apiRequest(
            `${TagFlow.apiBase}/video/${numericVideoId}/open-folder`,
            { method: 'POST' }
        );
        
        TagFlow.utils.showNotification('Carpeta abierta', 'success');
        
    } catch (error) {
        console.error('Error abriendo carpeta:', error);
        TagFlow.utils.showNotification('Error abriendo carpeta', 'error');
    }
}

/**
 * Recargar galería con filtros actuales
 */
async function reloadGallery() {
    try {
        TagFlow.utils.showLoading();
        
        // Obtener parámetros actuales
        const urlParams = new URLSearchParams(window.location.search);
        const currentUrl = window.location.pathname + '?' + urlParams.toString();
        
        // Recargar página
        window.location.href = currentUrl;
        
    } catch (error) {
        console.error('Error recargando galería:', error);
        TagFlow.utils.showNotification('Error recargando galería', 'error');
    } finally {
        TagFlow.utils.hideLoading();
    }
}

// Event listeners para el modal de edición
document.addEventListener('DOMContentLoaded', function() {
    // Cerrar modal al hacer clic fuera
    const editModalElement = document.getElementById('editVideoModal');
    if (editModalElement) {
        editModalElement.addEventListener('hidden.bs.modal', function() {
            currentVideoData = null;
            document.getElementById('edit-video-form').reset();
        });
    }
    
    // Auto-save con debounce en campos de texto
    const autoSaveFields = ['edit-notes', 'edit-final-music', 'edit-final-music-artist'];
    autoSaveFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('blur', TagFlow.utils.debounce(function() {
                if (currentVideoData) {
                    console.log('Auto-guardado activado para:', fieldId);
                    // Implementar auto-guardado si se desea
                }
            }, 1000));
        }
    });
});

console.log('🎨 Gallery JavaScript cargado completo');