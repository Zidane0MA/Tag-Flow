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
            // Actualizar badge de estado de edición
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
            // Actualizar badge de estado de procesamiento
            else if (badge.textContent.includes('Pendiente') || badge.textContent.includes('Procesando') || badge.textContent.includes('Completo') || badge.textContent.includes('Error')) {
                const processingStatusMap = {
                    'pendiente': { text: 'Pendiente', class: 'bg-light text-dark' },
                    'procesando': { text: 'Procesando', class: 'bg-info' },
                    'completado': { text: 'Completo', class: 'bg-success' },
                    'error': { text: 'Error', class: 'bg-danger' }
                };
                const processingStatus = processingStatusMap[updatedVideo.processing_status] || processingStatusMap['pendiente'];
                badge.textContent = processingStatus.text;
                badge.className = `badge ${processingStatus.class}`;
            }
        });
        
        // Actualizar información de música (con truncado)
        const musicInfo = videoCard.querySelector('.fa-music')?.parentElement;
        const truncate = (str, n) => str && str.length > n ? str.slice(0, n) + '...' : str;
        const music = updatedVideo.final_music || updatedVideo.detected_music;
        const artist = updatedVideo.final_music_artist || updatedVideo.detected_music_artist;
        const isAutoDetected = !updatedVideo.final_music && updatedVideo.detected_music;
        
        if (musicInfo) {
            if (music) {
                musicInfo.innerHTML = `
                    <i class="fas fa-music text-primary me-1"></i>
                    <small>
                        <strong>${truncate(music, 60)}</strong>
                        ${artist ? ` - ${truncate(artist, 40)}` : ''}
                        ${isAutoDetected ? ' <span class="text-muted">(auto)</span>' : ''}
                    </small>
                `;
            }
        } else if (music) {
            // Si no existía la sección de música pero ahora hay música, crearla
            const cardBody = videoCard.querySelector('.card-body');
            const musicDiv = document.createElement('div');
            musicDiv.className = 'mt-2';
            musicDiv.innerHTML = `
                <small class="text-primary">
                    <i class="fas fa-music text-primary me-1"></i>
                    <strong>${truncate(music, 60)}</strong>
                    ${artist ? ` - ${truncate(artist, 40)}` : ''}
                    ${isAutoDetected ? ' <span class="text-muted">(auto)</span>' : ''}
                </small>
            `;
            cardBody.appendChild(musicDiv);
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
        } else if (updatedVideo.final_characters?.length > 0 || updatedVideo.detected_characters?.length > 0) {
            // Si no existía la sección de personajes pero ahora hay personajes, crearla
            const cardBody = videoCard.querySelector('.card-body');
            const charactersDiv = document.createElement('div');
            charactersDiv.className = 'mt-2';
            const characters = updatedVideo.final_characters || updatedVideo.detected_characters || [];
            const displayChars = characters.slice(0, 2).join(', ');
            const moreText = characters.length > 2 ? `<span class="text-muted">+${characters.length - 2} más</span>` : '';
            charactersDiv.innerHTML = `
                <small class="text-success">
                    <i class="fas fa-user-friends text-success me-1"></i>
                    ${displayChars} ${moreText}
                </small>
            `;
            cardBody.appendChild(charactersDiv);
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

/**
 * Eliminar video (soft delete)
 */
async function deleteVideo(videoId) {
    try {
        // Convertir videoId a número si es string
        const numericVideoId = parseInt(videoId);
        if (isNaN(numericVideoId)) {
            TagFlow.utils.showNotification('ID de video inválido', 'error');
            return;
        }
        
        // Confirmar eliminación
        const confirmed = confirm('¿Estás seguro de que quieres eliminar este video?\n\nSe moverá a la papelera y podrás restaurarlo más tarde.');
        if (!confirmed) return;
        
        // Obtener razón opcional
        const reason = prompt('Razón de eliminación (opcional):') || 'Eliminado desde galería';
        
        const response = await TagFlow.utils.apiRequest(
            `${TagFlow.apiBase}/video/${numericVideoId}/delete`,
            {
                method: 'POST',
                body: JSON.stringify({ 
                    reason: reason,
                    deleted_by: 'web_user'
                })
            }
        );
        
        if (response.success) {
            TagFlow.utils.showNotification('Video eliminado y movido a papelera', 'success');
            
            // Remover video de la vista con animación
            const videoCard = document.querySelector(`[data-video-id="${numericVideoId}"]`);
            if (videoCard) {
                videoCard.style.transition = 'all 0.3s ease';
                videoCard.style.opacity = '0';
                videoCard.style.transform = 'scale(0.8)';
                
                setTimeout(() => {
                    videoCard.remove();
                    
                    // Verificar si quedan videos en la página
                    const remainingCards = document.querySelectorAll('.video-card-wrapper');
                    if (remainingCards.length === 0) {
                        // Si no quedan videos, mostrar mensaje o recargar
                        setTimeout(() => {
                            window.location.reload();
                        }, 500);
                    }
                }, 300);
            }
        } else {
            TagFlow.utils.showNotification(`Error: ${response.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Error eliminando video:', error);
        TagFlow.utils.showNotification('Error eliminando video', 'error');
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

// ===== FUNCIONALIDADES DE EDICIÓN MASIVA =====

// Variables para edición masiva
let selectedVideos = new Set();
let bulkEditModal = null;

// Inicializar modal de edición masiva
document.addEventListener('DOMContentLoaded', function() {
    const bulkModalElement = document.getElementById('bulkEditModal');
    if (bulkModalElement) {
        bulkEditModal = new bootstrap.Modal(bulkModalElement);
        
        // Limpiar formulario al cerrar modal
        bulkModalElement.addEventListener('hidden.bs.modal', function() {
            clearBulkEditForm();
        });
    }
});

/**
 * Actualizar selección de videos para edición masiva
 */
function updateBulkSelection() {
    const checkboxes = document.querySelectorAll('.video-select:checked');
    const panel = document.getElementById('bulk-edit-panel');
    const counter = document.getElementById('selection-count');
    const selectAllCheckbox = document.getElementById('select-all-videos');
    
    // Actualizar conjunto de videos seleccionados
    selectedVideos.clear();
    checkboxes.forEach(checkbox => {
        selectedVideos.add(parseInt(checkbox.value));
    });
    
    const count = selectedVideos.size;
    
    // Mostrar/ocultar panel de edición masiva
    if (count > 0) {
        panel.style.display = 'block';
        counter.textContent = `${count} video${count !== 1 ? 's' : ''} seleccionado${count !== 1 ? 's' : ''}`;
    } else {
        panel.style.display = 'none';
    }
    
    // Actualizar estado del checkbox "Seleccionar todo"
    const allCheckboxes = document.querySelectorAll('.video-select');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = allCheckboxes.length > 0 && checkboxes.length === allCheckboxes.length;
        selectAllCheckbox.indeterminate = checkboxes.length > 0 && checkboxes.length < allCheckboxes.length;
    }
    
    console.log(`📝 Selección actualizada: ${count} videos`);
}

/**
 * Alternar selección de todos los videos
 */
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all-videos');
    const videoCheckboxes = document.querySelectorAll('.video-select');
    
    videoCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateBulkSelection();
}

/**
 * Limpiar selección de videos
 */
function clearBulkSelection() {
    document.querySelectorAll('.video-select').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    const selectAllCheckbox = document.getElementById('select-all-videos');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
    
    selectedVideos.clear();
    updateBulkSelection();
}

/**
 * Acciones rápidas de estado masivo
 */
async function bulkSetStatus(newStatus) {
    if (selectedVideos.size === 0) {
        TagFlow.utils.showNotification('No hay videos seleccionados', 'warning');
        return;
    }
    
    const statusLabels = {
        'nulo': 'Sin Edición',
        'en_proceso': 'En proceso', 
        'hecho': 'Completado'
    };
    
    const confirmed = confirm(`¿Cambiar estado de ${selectedVideos.size} videos a "${statusLabels[newStatus]}"?`);
    if (!confirmed) return;
    
    try {
        TagFlow.utils.showLoading();
        
        const response = await TagFlow.utils.apiRequest('/api/videos/bulk-update', {
            method: 'POST',
            body: JSON.stringify({
                video_ids: Array.from(selectedVideos),
                updates: { edit_status: newStatus }
            })
        });
        
        if (response.success) {
            TagFlow.utils.showNotification(response.message, 'success');
            
            // Actualizar cards en el DOM
            selectedVideos.forEach(videoId => {
                const videoCard = document.querySelector(`[data-video-id="${videoId}"]`);
                if (videoCard) {
                    videoCard.dataset.status = newStatus;
                    
                    // Actualizar badge de estado
                    const statusBadge = videoCard.querySelector('.badge');
                    if (statusBadge && statusBadge.textContent.match(/(Sin Edición|En proceso|Completado)/)) {
                        const statusClasses = { 'nulo': 'bg-secondary', 'en_proceso': 'bg-warning', 'hecho': 'bg-success' };
                        statusBadge.className = `badge ${statusClasses[newStatus]}`;
                        statusBadge.textContent = statusLabels[newStatus];
                    }
                    
                    // Actualizar botones de estado
                    const statusButtons = videoCard.querySelectorAll('.btn-group .btn');
                    statusButtons.forEach(btn => btn.classList.remove('active'));
                    const statusMap = { 'nulo': 0, 'en_proceso': 1, 'hecho': 2 };
                    const buttonIndex = statusMap[newStatus];
                    if (buttonIndex !== undefined && statusButtons[buttonIndex]) {
                        statusButtons[buttonIndex].classList.add('active');
                    }
                }
            });
            
            clearBulkSelection();
        } else {
            TagFlow.utils.showNotification(`Error: ${response.error}`, 'error');
        }
    } catch (error) {
        console.error('Error en actualización masiva:', error);
        TagFlow.utils.showNotification('Error en actualización masiva', 'error');
    } finally {
        TagFlow.utils.hideLoading();
    }
}

/**
 * Eliminar videos seleccionados masivamente
 */
async function bulkDeleteVideos() {
    if (selectedVideos.size === 0) {
        TagFlow.utils.showNotification('No hay videos seleccionados', 'warning');
        return;
    }
    
    const confirmed = confirm(`¿Eliminar ${selectedVideos.size} videos seleccionados?\n\nSe moverán a la papelera y podrás restaurarlos más tarde.`);
    if (!confirmed) return;
    
    const reason = prompt('Razón de eliminación (opcional):') || 'Eliminación masiva desde galería';
    
    try {
        TagFlow.utils.showLoading();
        
        const response = await TagFlow.utils.apiRequest('/api/videos/bulk-delete', {
            method: 'POST',
            body: JSON.stringify({
                video_ids: Array.from(selectedVideos),
                reason: reason,
                deleted_by: 'web_user'
            })
        });
        
        if (response.success) {
            TagFlow.utils.showNotification(response.message, 'success');
            
            // Remover videos de la vista con animación
            selectedVideos.forEach(videoId => {
                const videoCard = document.querySelector(`[data-video-id="${videoId}"]`);
                if (videoCard) {
                    videoCard.style.transition = 'all 0.3s ease';
                    videoCard.style.opacity = '0';
                    videoCard.style.transform = 'scale(0.8)';
                    
                    setTimeout(() => {
                        videoCard.remove();
                    }, 300);
                }
            });
            
            clearBulkSelection();
            
            // Recargar página si no quedan videos
            setTimeout(() => {
                const remainingCards = document.querySelectorAll('.video-card-wrapper');
                if (remainingCards.length === 0) {
                    window.location.reload();
                }
            }, 1000);
            
        } else {
            TagFlow.utils.showNotification(`Error: ${response.error}`, 'error');
        }
    } catch (error) {
        console.error('Error en eliminación masiva:', error);
        TagFlow.utils.showNotification('Error en eliminación masiva', 'error');
    } finally {
        TagFlow.utils.hideLoading();
    }
}

/**
 * Abrir modal de edición masiva
 */
function openBulkEditModal() {
    if (selectedVideos.size === 0) {
        TagFlow.utils.showNotification('No hay videos seleccionados', 'warning');
        return;
    }
    
    if (!bulkEditModal) {
        TagFlow.utils.showNotification('Modal de edición no disponible', 'error');
        return;
    }
    
    // Actualizar contador en el modal
    document.getElementById('bulk-video-count').textContent = selectedVideos.size;
    
    // Mostrar modal
    bulkEditModal.show();
}

/**
 * Limpiar formulario de edición masiva
 */
function clearBulkEditForm() {
    const form = document.getElementById('bulk-edit-form');
    if (form) {
        form.reset();
        
        // Limpiar checkboxes específicos
        ['bulk-clear-music', 'bulk-clear-artist', 'bulk-clear-characters', 'bulk-clear-notes', 
         'bulk-reprocess', 'bulk-regenerate-thumbnails', 'bulk-revert-analysis'].forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox) checkbox.checked = false;
        });
    }
}

/**
 * Vista previa de cambios masivos
 */
function previewBulkChanges() {
    const changes = getBulkChangesData();
    
    if (Object.keys(changes.updates).length === 0 && !changes.options.clear_music && 
        !changes.options.clear_artist && !changes.options.clear_characters && !changes.options.clear_notes &&
        !changes.options.revert_analysis) {
        TagFlow.utils.showNotification('No hay cambios para aplicar', 'warning');
        return;
    }
    
    let preview = `Cambios que se aplicarán a ${selectedVideos.size} videos:\n\n`;
    
    if (changes.updates.edit_status) {
        const statusLabels = { 'nulo': 'Sin Edición', 'en_proceso': 'En proceso', 'hecho': 'Completado' };
        preview += `• Estado: ${statusLabels[changes.updates.edit_status]}\n`;
    }
    
    if (changes.updates.difficulty_level) {
        preview += `• Dificultad: ${changes.updates.difficulty_level.charAt(0).toUpperCase() + changes.updates.difficulty_level.slice(1)}\n`;
    }
    
    if (changes.updates.final_music) {
        preview += `• Música: ${changes.updates.final_music}\n`;
    }
    
    if (changes.updates.final_music_artist) {
        preview += `• Artista: ${changes.updates.final_music_artist}\n`;
    }
    
    if (changes.updates.final_characters && changes.updates.final_characters.length > 0) {
        preview += `• Personajes: ${changes.updates.final_characters.join(', ')}\n`;
    }
    
    if (changes.updates.notes) {
        preview += `• Notas: ${changes.updates.notes.substring(0, 50)}${changes.updates.notes.length > 50 ? '...' : ''}\n`;
    }
    
    // Operaciones de limpieza
    if (changes.options.clear_music) preview += `• ❌ Limpiar música existente\n`;
    if (changes.options.clear_artist) preview += `• ❌ Limpiar artista existente\n`;
    if (changes.options.clear_characters) preview += `• ❌ Limpiar personajes existentes\n`;
    if (changes.options.clear_notes) preview += `• ❌ Limpiar notas existentes\n`;
    
    // Opciones avanzadas
    if (changes.options.reprocess) preview += `• 🔄 Reprocesar automáticamente\n`;
    if (changes.options.regenerate_thumbnails) preview += `• 🖼️ Regenerar thumbnails\n`;
    if (changes.options.revert_analysis) preview += `• 🔄 Revertir análisis - Borrar información detectada\n`;
    
    alert(preview);
}

/**
 * Obtener datos de cambios masivos del formulario
 */
function getBulkChangesData() {
    const updates = {};
    const options = {};
    
    // Campos de actualización
    const editStatus = document.getElementById('bulk-edit-status').value;
    if (editStatus) updates.edit_status = editStatus;
    
    const difficulty = document.getElementById('bulk-difficulty-level').value;
    if (difficulty) updates.difficulty_level = difficulty;
    
    const music = TagFlow.utils.cleanText(document.getElementById('bulk-final-music').value);
    if (music) updates.final_music = music;
    
    const artist = TagFlow.utils.cleanText(document.getElementById('bulk-final-music-artist').value);
    if (artist) updates.final_music_artist = artist;
    
    const charactersText = TagFlow.utils.cleanText(document.getElementById('bulk-final-characters').value);
    if (charactersText) {
        updates.final_characters = charactersText.split(',').map(c => c.trim()).filter(c => c);
    }
    
    const notes = TagFlow.utils.cleanText(document.getElementById('bulk-notes').value);
    if (notes) updates.notes = notes;
    
    // Opciones de limpieza
    options.clear_music = document.getElementById('bulk-clear-music').checked;
    options.clear_artist = document.getElementById('bulk-clear-artist').checked;
    options.clear_characters = document.getElementById('bulk-clear-characters').checked;
    options.clear_notes = document.getElementById('bulk-clear-notes').checked;
    
    // Opciones avanzadas
    options.reprocess = document.getElementById('bulk-reprocess').checked;
    options.regenerate_thumbnails = document.getElementById('bulk-regenerate-thumbnails').checked;
    options.revert_analysis = document.getElementById('bulk-revert-analysis').checked;
    
    return { updates, options };
}

/**
 * Aplicar cambios masivos
 */
async function applyBulkChanges() {
    if (selectedVideos.size === 0) {
        TagFlow.utils.showNotification('No hay videos seleccionados', 'warning');
        return;
    }
    
    const changes = getBulkChangesData();
    
    if (Object.keys(changes.updates).length === 0 && !changes.options.clear_music && 
        !changes.options.clear_artist && !changes.options.clear_characters && !changes.options.clear_notes &&
        !changes.options.revert_analysis) {
        TagFlow.utils.showNotification('No hay cambios para aplicar', 'warning');
        return;
    }
    
    try {
        TagFlow.utils.showLoading();
        
        const response = await TagFlow.utils.apiRequest('/api/videos/bulk-edit', {
            method: 'POST',
            body: JSON.stringify({
                video_ids: Array.from(selectedVideos),
                updates: changes.updates,
                options: changes.options
            })
        });
        
        if (response.success) {
            TagFlow.utils.showNotification(response.message, 'success');
            
            // Cerrar modal
            bulkEditModal.hide();
            clearBulkSelection();
            
            // Recargar página para mostrar cambios
            setTimeout(() => {
                window.location.reload();
            }, 1000);
            
        } else {
            TagFlow.utils.showNotification(`Error: ${response.error}`, 'error');
        }
    } catch (error) {
        console.error('Error aplicando cambios masivos:', error);
        TagFlow.utils.showNotification('Error aplicando cambios masivos', 'error');
    } finally {
        TagFlow.utils.hideLoading();
    }
}

// ===== FUNCIONALIDADES DE REANÁLISIS =====

/**
 * Reanalizar un video individual
 * @param {string|number} videoId - ID del video a reanalizar
 * @param {boolean} force - Forzar reanálisis aunque ya esté procesado
 */
async function reanalyzeVideo(videoId, force = true) {
    const numericVideoId = parseInt(videoId);
    if (!numericVideoId) {
        TagFlow.utils.showNotification('ID de video inválido', 'error');
        return;
    }
    
    // Confirmación del usuario
    const confirmed = confirm(
        force ? 
        '¿Forzar reanálisis del video? Esto sobrescribirá los datos existentes.' :
        '¿Reanalizar este video para detectar música y personajes?'
    );
    
    if (!confirmed) return;
    
    try {
        TagFlow.utils.showLoading();
        
        // Actualizar indicador visual en la tarjeta
        const videoCard = document.querySelector(`[data-video-id="${numericVideoId}"]`);
        if (videoCard) {
            // Agregar indicador de procesamiento
            let processIndicator = videoCard.querySelector('.reanalyze-indicator');
            if (!processIndicator) {
                processIndicator = document.createElement('div');
                processIndicator.className = 'reanalyze-indicator position-absolute';
                processIndicator.style.cssText = 'top: 0.5rem; right: 0.5rem; z-index: 15;';
                processIndicator.innerHTML = '<i class="fas fa-sync fa-spin text-warning"></i>';
                videoCard.querySelector('.card').appendChild(processIndicator);
            }
        }
        
        const response = await TagFlow.utils.apiRequest(
            `${TagFlow.apiBase}/video/${numericVideoId}/reanalyze`,
            {
                method: 'POST',
                body: JSON.stringify({ force: force })
            }
        );
        
        console.log('Reanalysis response:', response); // Debug
        
        if (response && response.success) {
            TagFlow.utils.showNotification(
                `Reanálisis completado para video ${numericVideoId}`,
                'success'
            );
            
            // Actualizar datos del video después de un breve delay
            setTimeout(async () => {
                try {
                    // Recargar los datos del video desde la API
                    const videoResponse = await TagFlow.utils.apiRequest(
                        `${TagFlow.apiBase}/video/${numericVideoId}`
                    );
                    
                    if (videoResponse && videoResponse.success) {
                        // Actualizar la tarjeta del video con los nuevos datos
                        updateVideoCardInDOM(videoResponse.video);
                    } else {
                        // Si falla la actualización individual, recargar toda la galería
                        console.log('Fallback: recargando galería completa');
                        setTimeout(() => {
                            window.location.reload();
                        }, 2500);
                    }
                } catch (error) {
                    console.error('Error updating video data after reanalysis:', error);
                    // En caso de error, recargar la galería completa
                    setTimeout(() => {
                        window.location.reload();
                    }, 2500);
                }
            }, 2500);
            
            // Remover indicador después de 3 segundos
            setTimeout(() => {
                if (videoCard) {
                    const indicator = videoCard.querySelector('.reanalyze-indicator');
                    if (indicator) indicator.remove();
                }
            }, 3000);
            
        } else {
            TagFlow.utils.showNotification(`Error: ${response.error}`, 'error');
            
            // Remover indicador en caso de error
            if (videoCard) {
                const indicator = videoCard.querySelector('.reanalyze-indicator');
                if (indicator) indicator.remove();
            }
        }
        
    } catch (error) {
        console.error('Error reanalizing video:', error);
        TagFlow.utils.showNotification('Error reanalizing video', 'error');
        
        // Remover indicador en caso de error
        const videoCard = document.querySelector(`[data-video-id="${numericVideoId}"]`);
        if (videoCard) {
            const indicator = videoCard.querySelector('.reanalyze-indicator');
            if (indicator) indicator.remove();
        }
    } finally {
        TagFlow.utils.hideLoading();
    }
}

/**
 * Reanalizar videos seleccionados en masa
 * @param {boolean} force - Forzar reanálisis aunque ya estén procesados
 */
async function bulkReanalyzeVideos(force = false) {
    if (selectedVideos.size === 0) {
        TagFlow.utils.showNotification('No hay videos seleccionados para reanalizar', 'warning');
        return;
    }
    
    const videoCount = selectedVideos.size;
    const confirmed = confirm(
        force ?
        `¿Forzar reanálisis de ${videoCount} video(s)? Esto sobrescribirá los datos existentes.` :
        `¿Reanalizar ${videoCount} video(s) seleccionado(s) para detectar música y personajes?`
    );
    
    if (!confirmed) return;
    
    try {
        TagFlow.utils.showLoading();
        
        const videoIds = Array.from(selectedVideos);
        
        // Usar el nuevo endpoint de reanálisis masivo
        const response = await TagFlow.utils.apiRequest(
            `${TagFlow.apiBase}/videos/bulk-reanalyze`,
            {
                method: 'POST',
                body: JSON.stringify({ 
                    video_ids: videoIds,
                    force: force 
                })
            }
        );
        
        if (response.success) {
            TagFlow.utils.showNotification(
                `Reanálisis masivo completado exitosamente para ${response.total_videos} videos`,
                'success'
            );
        } else {
            TagFlow.utils.showNotification(
                `Error en reanálisis masivo: ${response.error}`,
                'error'
            );
        }
        
        // Limpiar selección
        clearBulkSelection();
        
        // Recargar página después de un tiempo para mostrar cambios
        setTimeout(() => {
            window.location.reload();
        }, 3000);
        
    } catch (error) {
        console.error('Error en reanálisis masivo:', error);
        TagFlow.utils.showNotification('Error en reanálisis masivo', 'error');
    } finally {
        TagFlow.utils.hideLoading();
    }
}

/**
 * Forzar reanálisis de un video (sobrescribe datos existentes)
 * @param {string|number} videoId - ID del video
 */
function forceReanalyzeVideo(videoId) {
    reanalyzeVideo(videoId, true);
}

/**
 * Forzar reanálisis masivo (sobrescribe datos existentes)
 */
function bulkForceReanalyzeVideos() {
    bulkReanalyzeVideos(true);
}

// ===== FUNCIONALIDADES DE CARGA DINÁMICA =====

// Variables para scroll infinito
let currentLoadingMode = 'pagination'; // 'pagination' o 'infinite'
let currentPage = 1;
let totalPages = 1;
let isLoading = false;
let hasMorePages = true;

/**
 * Configurar el modo de carga (paginación o scroll infinito)
 * @param {string} mode - 'pagination' o 'infinite'
 */
function setLoadingMode(mode) {
    currentLoadingMode = mode;
    
    // Guardar preferencia en localStorage
    localStorage.setItem('tagflow-loading-mode', mode);
    
    // Sincronizar ambos sets de radio buttons (gallery y navbar global)
    const paginationRadios = [
        document.getElementById('pagination-mode'),
        document.getElementById('global-pagination-mode')
    ].filter(el => el !== null);
    
    const infiniteRadios = [
        document.getElementById('infinite-mode'),
        document.getElementById('global-infinite-mode')
    ].filter(el => el !== null);
    
    // Actualizar estado de todos los radio buttons
    if (mode === 'infinite') {
        infiniteRadios.forEach(radio => radio.checked = true);
        paginationRadios.forEach(radio => radio.checked = false);
    } else {
        paginationRadios.forEach(radio => radio.checked = true);
        infiniteRadios.forEach(radio => radio.checked = false);
    }
    
    // Solo aplicar lógica de visualización si estamos en la página de galería
    if (!document.getElementById('videos-container')) {
        console.log(`🔄 Modo ${mode} guardado, aplicará en próxima visita a galería`);
        return;
    }
    
    if (mode === 'pagination') {
        // Mostrar controles de paginación
        const paginationControls = document.getElementById('pagination-controls');
        if (paginationControls) {
            paginationControls.style.display = 'block';
        }
        
        // Ocultar indicadores de scroll infinito
        const infiniteLoading = document.getElementById('infinite-loading');
        const infiniteEnd = document.getElementById('infinite-end');
        if (infiniteLoading) infiniteLoading.style.display = 'none';
        if (infiniteEnd) infiniteEnd.style.display = 'none';
        
        // Remover listener de scroll
        window.removeEventListener('scroll', handleInfiniteScroll);
        
        console.log('📄 Modo paginación activado');
        TagFlow.utils.showNotification('Modo paginación activado', 'info');
        
    } else if (mode === 'infinite') {
        // Ocultar controles de paginación
        const paginationControls = document.getElementById('pagination-controls');
        if (paginationControls) {
            paginationControls.style.display = 'none';
        }
        
        // Inicializar scroll infinito
        initializeInfiniteScroll();
        
        console.log('♾️ Modo scroll infinito activado');
        TagFlow.utils.showNotification('Modo scroll infinito activado', 'info');
    }
}

/**
 * Inicializar scroll infinito
 */
function initializeInfiniteScroll() {
    // Obtener información de paginación actual de la página
    const urlParams = new URLSearchParams(window.location.search);
    currentPage = parseInt(urlParams.get('page')) || 1;
    
    // Obtener información de paginación del contenedor
    const videosContainer = document.getElementById('videos-container');
    const totalVideos = parseInt(videosContainer.dataset.totalVideos) || 0;
    const perPage = parseInt(videosContainer.dataset.perPage) || 20;
    const serverCurrentPage = parseInt(videosContainer.dataset.currentPage) || 1;
    
    // Actualizar variables globales
    currentPage = serverCurrentPage;
    totalPages = Math.ceil(totalVideos / perPage);
    
    console.log(`📊 Datos de paginación: ${totalVideos} videos, ${perPage} por página, página actual: ${currentPage}/${totalPages}`);
    
    hasMorePages = currentPage < totalPages;
    
    // Agregar listener de scroll
    window.addEventListener('scroll', TagFlow.utils.throttle(handleInfiniteScroll, 200));
    
    console.log(`♾️ Scroll infinito inicializado - Página ${currentPage}/${totalPages}`);
}

/**
 * Manejar el evento de scroll para carga infinita
 */
function handleInfiniteScroll() {
    // Solo proceder si estamos en modo infinito y no estamos cargando
    if (currentLoadingMode !== 'infinite' || isLoading || !hasMorePages) {
        return;
    }
    
    // Detectar si estamos cerca del final de la página
    const scrollPosition = window.scrollY + window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const triggerPoint = documentHeight - 800; // Cargar cuando falten 800px para el final
    
    if (scrollPosition >= triggerPoint) {
        loadMoreVideos();
    }
}

/**
 * Cargar más videos para scroll infinito
 */
async function loadMoreVideos() {
    if (isLoading || !hasMorePages) return;
    
    isLoading = true;
    
    // Mostrar indicador de carga
    document.getElementById('infinite-loading').style.display = 'block';
    
    try {
        const nextPage = currentPage + 1;
        
        // Construir URL para la siguiente página manteniendo filtros actuales
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('page', nextPage.toString());
        
        const response = await fetch(`${window.location.pathname}?${urlParams.toString()}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const html = await response.text();
        
        // Parsear HTML para extraer los nuevos videos
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newVideos = doc.querySelectorAll('#videos-container .video-card-wrapper');
        
        if (newVideos.length > 0) {
            // Agregar nuevos videos al contenedor existente
            const videosContainer = document.getElementById('videos-container');
            
            newVideos.forEach(videoCard => {
                videosContainer.appendChild(videoCard.cloneNode(true));
            });
            
            currentPage = nextPage;
            
            // Verificar si hay más páginas
            const paginationInNewPage = doc.querySelector('#pagination-controls');
            hasMorePages = paginationInNewPage && doc.querySelector('.page-item:not(.disabled) .fa-angle-right');
            
            console.log(`✅ Cargada página ${currentPage} - ${newVideos.length} videos agregados`);
            
            // Actualizar contador de videos seleccionados si existe
            if (typeof updateBulkSelection === 'function') {
                updateBulkSelection();
            }
            
        } else {
            // No hay más videos
            hasMorePages = false;
            console.log('📄 No hay más videos para cargar');
        }
        
    } catch (error) {
        console.error('Error cargando más videos:', error);
        TagFlow.utils.showNotification('Error cargando más videos', 'error');
        hasMorePages = false;
    } finally {
        isLoading = false;
        
        // Ocultar indicador de carga
        document.getElementById('infinite-loading').style.display = 'none';
        
        // Mostrar mensaje de fin si no hay más páginas
        if (!hasMorePages) {
            document.getElementById('infinite-end').style.display = 'block';
        }
    }
}

/**
 * Inicializar modo de carga basado en preferencia guardada
 */
function initializeLoadingMode() {
    const savedMode = localStorage.getItem('tagflow-loading-mode') || 'pagination';
    
    // Buscar radio buttons tanto en gallery como en navbar global
    const paginationRadio = document.getElementById('pagination-mode') || document.getElementById('global-pagination-mode');
    const infiniteRadio = document.getElementById('infinite-mode') || document.getElementById('global-infinite-mode');
    
    if (!paginationRadio || !infiniteRadio) {
        console.log('Switches de modo de visualización no encontrados en esta página');
        return;
    }
    
    // Actualizar estado de los radio buttons
    if (savedMode === 'infinite') {
        infiniteRadio.checked = true;
        paginationRadio.checked = false;
        setLoadingMode('infinite');
    } else {
        paginationRadio.checked = true;
        infiniteRadio.checked = false;
        setLoadingMode('pagination');
    }
    
    console.log(`🔄 Modo de visualización inicializado: ${savedMode}`);
}

// Inicializar modo de carga al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    // Retrasar inicialización para asegurar que otros elementos estén listos
    setTimeout(initializeLoadingMode, 100);
});

// Exponer funciones globalmente para uso en HTML
window.setLoadingMode = setLoadingMode;

console.log('🎨 Gallery JavaScript cargado completo - Edición masiva, reanálisis y scroll infinito habilitados');