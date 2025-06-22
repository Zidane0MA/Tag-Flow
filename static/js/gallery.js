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
    // Filtros en tiempo real
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', TagFlow.utils.debounce(performSearch, 300));
    }
    
    // Botón de búsqueda
    const searchBtn = document.getElementById('search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', performSearch);
    }
    
    // Enter en búsqueda
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
    
    // Limpiar filtros
    const clearFiltersBtn = document.getElementById('clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
}

/**
 * Event listeners para filtros
 */
function setupFilterEventListeners() {
    const filterSelects = ['filter-creator', 'filter-platform', 'filter-status', 'filter-processing', 'filter-difficulty'];
    
    filterSelects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.addEventListener('change', applyFilters);
        }
    });
}

/**
 * Aplicar filtros iniciales desde URL
 */
function applyInitialFilters() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Aplicar filtros desde URL
    const filterMap = {
        'creator': 'filter-creator',
        'platform': 'filter-platform', 
        'status': 'filter-status',
        'processing_status': 'filter-processing',
        'difficulty': 'filter-difficulty',
        'search': 'search-input'
    };
    
    Object.entries(filterMap).forEach(([param, elementId]) => {
        const value = urlParams.get(param);
        const element = document.getElementById(elementId);
        if (value && element) {
            element.value = value;
        }
    });
}

/**
 * Aplicar filtros a los videos
 */
function applyFilters() {
    const filters = {
        creator: document.getElementById('filter-creator')?.value || '',
        platform: document.getElementById('filter-platform')?.value || '',
        status: document.getElementById('filter-status')?.value || '',
        processing_status: document.getElementById('filter-processing')?.value || '',
        difficulty: document.getElementById('filter-difficulty')?.value || '',
        search: document.getElementById('search-input')?.value || ''
    };
    
    // Actualizar URL sin recargar página
    updateURL(filters);
    
    // Filtrar videos visualmente
    filterVideosVisually(filters);
}

/**
 * Filtrar videos visualmente (client-side)
 */
function filterVideosVisually(filters) {
    const videoCards = document.querySelectorAll('.video-card-wrapper');
    let visibleCount = 0;
    
    videoCards.forEach(card => {
        let shouldShow = true;
        
        // Verificar cada filtro
        if (filters.creator && !card.dataset.creator.toLowerCase().includes(filters.creator.toLowerCase())) {
            shouldShow = false;
        }
        
        if (filters.platform && card.dataset.platform !== filters.platform) {
            shouldShow = false;
        }
        
        if (filters.status && card.dataset.status !== filters.status) {
            shouldShow = false;
        }
        
        if (filters.processing_status && card.dataset.processingStatus !== filters.processing_status) {
            shouldShow = false;
        }
        
        if (filters.difficulty && card.dataset.difficulty !== filters.difficulty) {
            shouldShow = false;
        }
        
        // Búsqueda por texto
        if (filters.search) {
            const searchText = filters.search.toLowerCase();
            const cardText = card.textContent.toLowerCase();
            if (!cardText.includes(searchText)) {
                shouldShow = false;
            }
        }
        
        // Aplicar filtro visual
        if (shouldShow) {
            card.classList.remove('filtered-out');
            card.style.display = '';
            visibleCount++;
        } else {
            card.classList.add('filtered-out');
            setTimeout(() => {
                if (card.classList.contains('filtered-out')) {
                    card.style.display = 'none';
                }
            }, 300);
        }
    });
    
    // Mostrar mensaje si no hay resultados
    showNoResultsMessage(visibleCount === 0);
}

/**
 * Mostrar/ocultar mensaje de sin resultados
 */
function showNoResultsMessage(show) {
    let noResultsDiv = document.getElementById('no-results-message');
    
    if (show && !noResultsDiv) {
        noResultsDiv = document.createElement('div');
        noResultsDiv.id = 'no-results-message';
        noResultsDiv.className = 'col-12 text-center py-5';
        noResultsDiv.innerHTML = `
            <i class="fas fa-search fa-3x text-muted mb-3"></i>
            <h4 class="text-muted">No se encontraron videos</h4>
            <p class="text-muted">Intenta ajustar los filtros de búsqueda</p>
            <button onclick="clearAllFilters()" class="btn btn-outline-primary">
                <i class="fas fa-times me-2"></i>Limpiar Filtros
            </button>
        `;
        document.getElementById('videos-container').appendChild(noResultsDiv);
    } else if (!show && noResultsDiv) {
        noResultsDiv.remove();
    }
}

/**
 * Actualizar URL con parámetros de filtro
 */
function updateURL(filters) {
    const url = new URL(window.location);
    
    // Limpiar parámetros existentes
    ['creator', 'platform', 'status', 'processing_status', 'difficulty', 'search'].forEach(param => {
        url.searchParams.delete(param);
    });
    
    // Agregar parámetros no vacíos
    Object.entries(filters).forEach(([key, value]) => {
        if (value) {
            url.searchParams.set(key, value);
        }
    });
    
    // Actualizar URL sin recargar
    window.history.pushState({}, '', url);
}

/**
 * Realizar búsqueda
 */
function performSearch() {
    applyFilters();
}

/**
 * Limpiar todos los filtros
 */
function clearAllFilters() {
    // Limpiar campos de filtro
    document.getElementById('search-input').value = '';
    document.getElementById('filter-creator').value = '';
    document.getElementById('filter-platform').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-processing').value = '';
    document.getElementById('filter-difficulty').value = '';
    
    // Aplicar filtros vacíos
    applyFilters();
    
    TagFlow.utils.showNotification('Filtros limpiados', 'info');
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
            if (badge.textContent.includes('Sin procesar') || badge.textContent.includes('En proceso') || badge.textContent.includes('Completado')) {
                const statusMap = {
                    'nulo': { text: 'Sin procesar', class: 'bg-secondary' },
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
            'nulo': 'Sin procesar',
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