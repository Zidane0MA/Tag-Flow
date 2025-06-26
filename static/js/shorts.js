/**
 * Tag-Flow V2 - JavaScript para Modal TikTok/Shorts
 * Funcionalidad de navegación tipo TikTok con scroll vertical
 */

// Variables globales para shorts
window.ShortsPlayer = {
    modal: null,
    container: null,
    currentIndex: 0,
    videos: [],
    isInitialized: false,
    isLoading: false,
    currentVideo: null,
    loadedVideos: new Set(),
    preloadDistance: 2, // Número de videos a precargar antes/después
    touchStartY: 0,
    touchStartTime: 0,
    isTransitioning: false
};

/**
 * Inicializar reproductor de shorts al cargar el DOM
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeShortsPlayer();
});

/**
 * Inicializar el reproductor de shorts
 */
function initializeShortsPlayer() {
    console.log('🎬 Inicializando reproductor de shorts...');
    
    const modalElement = document.getElementById('videoShortsModal');
    const container = document.getElementById('shorts-container');
    
    if (!modalElement || !container) {
        console.warn('❌ Elementos del reproductor de shorts no encontrados');
        return;
    }
    
    ShortsPlayer.modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static',
        keyboard: true
    });
    ShortsPlayer.container = container;
    
    // Event listeners
    setupShortsEventListeners();
    
    ShortsPlayer.isInitialized = true;
    console.log('✅ Reproductor de shorts inicializado');
}

/**
 * Configurar event listeners para shortcuts
 */
function setupShortsEventListeners() {
    const modalElement = document.getElementById('videoShortsModal');
    
    // Navegación por teclado
    document.addEventListener('keydown', function(e) {
        if (!modalElement.classList.contains('show')) return;
        
        switch(e.key) {
            case 'ArrowUp':
                e.preventDefault();
                previousVideo();
                break;
            case 'ArrowDown':
                e.preventDefault();
                nextVideo();
                break;
            case ' ':
            case 'Spacebar':
                e.preventDefault();
                toggleCurrentVideo();
                break;
            case 'Escape':
                e.preventDefault();
                closeShortsPlayer();
                break;
        }
    });
    
    // Gestos táctiles para dispositivos móviles
    let startY = 0;
    let startTime = 0;
    
    modalElement.addEventListener('touchstart', function(e) {
        startY = e.touches[0].clientY;
        startTime = Date.now();
    });
    
    modalElement.addEventListener('touchend', function(e) {
        const endY = e.changedTouches[0].clientY;
        const endTime = Date.now();
        const deltaY = startY - endY;
        const deltaTime = endTime - startTime;
        
        // Detectar swipe vertical rápido
        if (Math.abs(deltaY) > 50 && deltaTime < 300) {
            e.preventDefault();
            if (deltaY > 0) {
                nextVideo(); // Swipe up = siguiente video
            } else {
                previousVideo(); // Swipe down = video anterior
            }
        }
    });
    
    // Ocultar instrucciones después de un tiempo
    modalElement.addEventListener('shown.bs.modal', function() {
        setTimeout(() => {
            const instructions = document.getElementById('shorts-instructions');
            if (instructions) {
                instructions.style.display = 'none';
            }
        }, 4000);
    });
    
    // Cleanup al cerrar modal
    modalElement.addEventListener('hidden.bs.modal', function() {
        cleanupShortsPlayer();
    });
}

/**
 * Abrir video en modo shorts
 * @param {number} videoId - ID del video a reproducir
 */
async function playVideoShorts(videoId) {
    if (!ShortsPlayer.isInitialized) {
        TagFlow.utils.showNotification('Reproductor de shorts no disponible', 'error');
        return;
    }
    
    try {
        ShortsPlayer.isLoading = true;
        TagFlow.utils.showLoading();
        
        // Obtener lista de videos filtrados de la página actual
        await loadCurrentVideosList();
        
        // Debug para verificar orden
        debugVideoOrder();
        
        // Encontrar índice del video seleccionado
        const videoIndex = ShortsPlayer.videos.findIndex(v => v.id == videoId);
        if (videoIndex === -1) {
            console.error(`❌ Video ${videoId} no encontrado en lista. Videos disponibles:`, 
                         ShortsPlayer.videos.map(v => v.id));
            throw new Error('Video no encontrado en la lista actual');
        }
        
        console.log(`🎯 Video encontrado en índice ${videoIndex} de ${ShortsPlayer.videos.length}`);
        ShortsPlayer.currentIndex = videoIndex;
        
        // Crear elementos de video en el contenedor
        await createVideoElements();
        
        // Cargar video inicial
        await loadVideoAtIndex(videoIndex);
        
        // Actualizar UI
        updateShortsUI();
        
        // Mostrar modal
        ShortsPlayer.modal.show();
        
        // Esperar un momento para que el modal se muestre completamente
        setTimeout(async () => {
            // Reproducir video inicial automáticamente
            await playVideoAtIndex(videoIndex);
            
            // Precargar videos adyacentes
            preloadAdjacentVideos();
        }, 300);
        
    } catch (error) {
        console.error('Error abriendo shorts:', error);
        TagFlow.utils.showNotification('Error al cargar el reproductor', 'error');
    } finally {
        ShortsPlayer.isLoading = false;
        TagFlow.utils.hideLoading();
    }
}

/**
 * Cargar lista de videos de la página actual
 */
async function loadCurrentVideosList() {
    try {
        // Obtener todos los videos visibles en la página en el orden correcto
        const videoCards = document.querySelectorAll('.video-card-wrapper[data-video-id]');
        ShortsPlayer.videos = [];
        
        console.log(`🔍 Encontradas ${videoCards.length} cards de video`);
        
        videoCards.forEach((card, index) => {
            const videoId = card.dataset.videoId;
            const creatorName = card.dataset.creator;
            const platform = card.dataset.platform;
            
            // Verificar que la card es visible (no filtrada)
            const isVisible = !card.classList.contains('filtered-out') && 
                            card.style.display !== 'none' && 
                            !card.hidden;
            
            if (!isVisible) {
                console.log(`⏭️ Saltando video ${videoId} - no visible`);
                return;
            }
            
            // Extraer información de la card
            const titleElement = card.querySelector('.card-title');
            const musicElement = card.querySelector('.fa-music')?.parentElement;
            const charactersElement = card.querySelector('.fa-user-friends')?.parentElement;
            const thumbnailElement = card.querySelector('.thumbnail-image');
            
            const videoData = {
                id: parseInt(videoId),
                creator_name: creatorName,
                platform: platform,
                title: titleElement?.textContent?.trim() || 'Sin título',
                music: extractMusicInfo(musicElement),
                characters: extractCharactersInfo(charactersElement),
                thumbnail_url: thumbnailElement?.src,
                order_in_gallery: index, // Guardar orden original
                // Datos adicionales se cargarán dinámicamente
                file_path: null,
                duration: null,
                loaded: false
            };
            
            ShortsPlayer.videos.push(videoData);
            console.log(`📹 Video ${ShortsPlayer.videos.length}: ID=${videoId}, Creator=${creatorName}`);
        });
        
        console.log(`📼 Cargados ${ShortsPlayer.videos.length} videos visibles para shorts`);
        
        if (ShortsPlayer.videos.length === 0) {
            throw new Error('No hay videos visibles para reproducir');
        }
        
    } catch (error) {
        console.error('Error cargando lista de videos:', error);
        throw error;
    }
}

/**
 * Extraer información de música del elemento
 */
function extractMusicInfo(musicElement) {
    if (!musicElement) return { title: 'Música original', artist: '' };
    
    const text = musicElement.textContent.trim();
    const strongElement = musicElement.querySelector('strong');
    
    if (strongElement) {
        const title = strongElement.textContent.trim();
        const fullText = text.replace(title, '').replace('-', '').trim();
        const isAuto = text.includes('(auto)');
        
        return {
            title: title || 'Música original',
            artist: fullText.replace('(auto)', '').trim() || '',
            is_auto: isAuto
        };
    }
    
    return { title: text || 'Música original', artist: '' };
}

/**
 * Extraer información de personajes del elemento
 */
function extractCharactersInfo(charactersElement) {
    if (!charactersElement) return [];
    
    const text = charactersElement.textContent.trim();
    if (text.includes('Sin personajes')) return [];
    
    // Extraer personajes del texto
    const charactersText = text.replace(/\+\d+\s+más/g, '').trim();
    return charactersText.split(',').map(c => c.trim()).filter(c => c);
}

/**
 * Crear elementos de video en el contenedor
 */
async function createVideoElements() {
    ShortsPlayer.container.innerHTML = '';
    
    ShortsPlayer.videos.forEach((video, index) => {
        const videoElement = document.createElement('div');
        videoElement.className = 'shorts-video-item';
        videoElement.dataset.videoId = video.id;
        videoElement.dataset.index = index;
        
        // Placeholder inicial
        videoElement.innerHTML = `
            <div class="video-preloader">
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
            </div>
            <div class="video-progress">
                <div class="video-progress-bar"></div>
            </div>
        `;
        
        ShortsPlayer.container.appendChild(videoElement);
    });
}

/**
 * Cargar video en el índice especificado
 */
async function loadVideoAtIndex(index) {
    if (index < 0 || index >= ShortsPlayer.videos.length) return;
    
    const video = ShortsPlayer.videos[index];
    if (video.loaded) return;
    
    console.log(`🎬 Cargando video ${index}: ID=${video.id}, Creator=${video.creator_name}`);
    
    try {
        // Obtener datos completos del video
        const response = await TagFlow.utils.apiRequest(`${TagFlow.apiBase}/video/${video.id}`);
        
        if (!response.success) {
            throw new Error('Error cargando datos del video');
        }
        
        // Actualizar datos del video
        Object.assign(video, response.video);
        console.log(`✅ Datos del video ${index} cargados:`, video.file_name);
        
        // Crear elemento de video
        const videoElement = ShortsPlayer.container.querySelector(`[data-index="${index}"]`);
        if (!videoElement) {
            console.error(`❌ No se encontró elemento de video para índice ${index}`);
            return;
        }
        
        const videoHtml = `
            <video 
                id="shorts-video-${index}"
                preload="metadata"
                loop
                playsinline
                onloadeddata="console.log('Video ${index} loaded successfully')"
                onloadedmetadata="console.log('Video ${index} metadata loaded'); updateVideoProgress(${index})"
                ontimeupdate="updateVideoProgress(${index})"
                onended="nextVideo()"
                onclick="handleVideoClick(${index})"
                onerror="console.error('Video ${index} error:', event)"
                oncanplay="console.log('Video ${index} can play')"
            >
                <source src="/video-stream/${video.id}" type="video/mp4">
                Tu navegador no soporta este formato de video.
            </video>
            <div class="video-progress">
                <div class="video-progress-bar" id="progress-bar-${index}"></div>
            </div>
        `;
        
        videoElement.innerHTML = videoHtml;
        
        const videoTag = videoElement.querySelector('video');
        if (videoTag) {
            // Eventos adicionales para debugging
            videoTag.addEventListener('loadstart', () => console.log(`📡 Video ${index} empezó a cargar`));
            videoTag.addEventListener('canplay', () => console.log(`▶️ Video ${index} listo para reproducir`));
            videoTag.addEventListener('error', (e) => console.error(`❌ Error en video ${index}:`, e));
            
            videoTag.load();
            ShortsPlayer.loadedVideos.add(index);
            console.log(`🎯 Video ${index} configurado correctamente`);
        }
        
        video.loaded = true;
        
    } catch (error) {
        console.error(`❌ Error cargando video ${index}:`, error);
        
        // Mostrar error en el elemento
        const videoElement = ShortsPlayer.container.querySelector(`[data-index="${index}"]`);
        if (videoElement) {
            videoElement.innerHTML = `
                <div class="text-center text-white p-4">
                    <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                    <p>Error cargando el video</p>
                    <p class="small">ID: ${video.id} - ${video.creator_name}</p>
                    <button class="btn btn-outline-light btn-sm" onclick="retryLoadVideo(${index})">
                        Reintentar
                    </button>
                </div>
            `;
        }
    }
}

/**
 * Precargar videos adyacentes
 */
function preloadAdjacentVideos() {
    const currentIndex = ShortsPlayer.currentIndex;
    const start = Math.max(0, currentIndex - ShortsPlayer.preloadDistance);
    const end = Math.min(ShortsPlayer.videos.length, currentIndex + ShortsPlayer.preloadDistance + 1);
    
    for (let i = start; i < end; i++) {
        if (i !== currentIndex && !ShortsPlayer.videos[i].loaded) {
            setTimeout(() => loadVideoAtIndex(i), (Math.abs(i - currentIndex) * 100));
        }
    }
}

/**
 * Navegar al video anterior
 */
function previousVideo() {
    if (ShortsPlayer.currentIndex > 0) {
        navigateToVideo(ShortsPlayer.currentIndex - 1);
    }
}

/**
 * Navegar al siguiente video
 */
function nextVideo() {
    if (ShortsPlayer.currentIndex < ShortsPlayer.videos.length - 1) {
        navigateToVideo(ShortsPlayer.currentIndex + 1);
    }
}

/**
 * Navegar a un video específico
 */
async function navigateToVideo(index) {
    if (index < 0 || index >= ShortsPlayer.videos.length || ShortsPlayer.isLoading || ShortsPlayer.isTransitioning) return;
    
    ShortsPlayer.isTransitioning = true;
    
    const previousIndex = ShortsPlayer.currentIndex;
    ShortsPlayer.currentIndex = index;
    
    // Pausar video anterior
    pauseVideoAtIndex(previousIndex);
    
    // Cargar video actual si no está cargado
    if (!ShortsPlayer.videos[index].loaded) {
        showShortsLoading(true);
        await loadVideoAtIndex(index);
        showShortsLoading(false);
    }
    
    // Reproducir video actual
    await playVideoAtIndex(index);
    
    // Actualizar UI
    updateShortsUI();
    
    // Precargar videos adyacentes
    preloadAdjacentVideos();
    
    // Scroll suave al video
    scrollToVideo(index);
    
    // Permitir nuevas transiciones después de un breve delay
    setTimeout(() => {
        ShortsPlayer.isTransitioning = false;
    }, 300);
}

/**
 * Reproducir video en el índice especificado
 */
async function playVideoAtIndex(index) {
    const videoElement = document.getElementById(`shorts-video-${index}`);
    if (!videoElement) {
        console.warn(`❌ No se encontró video element para índice ${index}`);
        return;
    }
    
    console.log(`▶️ Intentando reproducir video ${index}`);
    
    try {
        // Pausar video anterior si existe
        if (ShortsPlayer.currentVideo && ShortsPlayer.currentVideo !== videoElement) {
            ShortsPlayer.currentVideo.pause();
            console.log(`⏸️ Video anterior pausado`);
        }
        
        videoElement.currentTime = 0;
        
        // Intentar reproducir con audio primero
        videoElement.muted = false;
        
        try {
            await videoElement.play();
            console.log(`✅ Video ${index} reproduciéndose con audio`);
        } catch (audioError) {
            // Si falla por políticas de autoplay, intentar sin audio
            console.warn(`⚠️ Autoplay con audio falló, intentando sin audio:`, audioError.message);
            videoElement.muted = true;
            
            try {
                await videoElement.play();
                console.log(`✅ Video ${index} reproduciéndose sin audio`);
                TagFlow.utils.showNotification('Haz clic en el video para activar el audio', 'info');
            } catch (mutedError) {
                console.error(`❌ Error reproduciendo video ${index} incluso sin audio:`, mutedError);
                throw mutedError;
            }
        }
        
        ShortsPlayer.currentVideo = videoElement;
        
        // Agregar event listener para habilitar audio en primer clic
        if (videoElement.muted) {
            const enableAudio = function() {
                if (videoElement.muted) {
                    videoElement.muted = false;
                    console.log(`🔊 Audio activado para video ${index}`);
                    TagFlow.utils.showNotification('Audio activado', 'success');
                }
                videoElement.removeEventListener('click', enableAudio);
            };
            
            videoElement.addEventListener('click', enableAudio, { once: true });
        }
        
    } catch (error) {
        console.error(`❌ Error crítico reproduciendo video ${index}:`, error);
        TagFlow.utils.showNotification(`Error reproduciendo video ${index}`, 'error');
    }
}

/**
 * Pausar video en el índice especificado
 */
function pauseVideoAtIndex(index) {
    const videoElement = document.getElementById(`shorts-video-${index}`);
    if (videoElement) {
        videoElement.pause();
    }
}

/**
 * Manejar clic en video
 */
function handleVideoClick(index) {
    const videoElement = document.getElementById(`shorts-video-${index}`);
    if (videoElement && index === ShortsPlayer.currentIndex) {
        // Solo pausar/reproducir si es el video actual
        if (videoElement.paused) {
            videoElement.play().catch(err => console.warn('Error playing video:', err));
        } else {
            videoElement.pause();
        }
        
        // Activar audio si está muted
        if (videoElement.muted) {
            videoElement.muted = false;
            TagFlow.utils.showNotification('Audio activado', 'success');
        }
    }
}

/**
 * Alternar reproducción del video actual
 */
function toggleCurrentVideo() {
    if (ShortsPlayer.currentVideo) {
        if (ShortsPlayer.currentVideo.paused) {
            ShortsPlayer.currentVideo.play();
        } else {
            ShortsPlayer.currentVideo.pause();
        }
    }
}

/**
 * Hacer scroll suave al video
 */
function scrollToVideo(index) {
    console.log(`🎯 Scrolling a video ${index}`);
    
    const videoElements = ShortsPlayer.container.querySelectorAll('.shorts-video-item');
    
    videoElements.forEach((el, i) => {
        const offset = (i - index) * 100;
        el.style.transform = `translateY(${offset}vh)`;
        
        // Gestión de clases para estados
        el.classList.remove('active', 'prev', 'next');
        
        if (i === index) {
            el.classList.add('active');
            console.log(`✅ Video ${i} marcado como activo`);
        } else if (i < index) {
            el.classList.add('prev');
        } else {
            el.classList.add('next');
        }
        
        // Logging para debug
        console.log(`📍 Video ${i}: transform=${el.style.transform}, classes=${el.className}`);
    });
}

/**
 * Actualizar UI del reproductor
 */
function updateShortsUI() {
    const currentVideo = ShortsPlayer.videos[ShortsPlayer.currentIndex];
    if (!currentVideo) return;
    
    // Actualizar contador
    document.getElementById('current-video-position').textContent = ShortsPlayer.currentIndex + 1;
    document.getElementById('total-videos-count').textContent = ShortsPlayer.videos.length;
    
    // Actualizar información del overlay
    updateOverlayInfo(currentVideo);
    
    // Actualizar botones de navegación
    updateNavigationButtons();
}

/**
 * Actualizar información del overlay
 */
function updateOverlayInfo(video) {
    // Información del creador
    const creatorInfo = document.getElementById('current-creator-info');
    if (creatorInfo) {
        creatorInfo.innerHTML = `
            <div class="creator-name">@${video.creator_name}</div>
            <div class="video-title">${video.file_name || 'Video sin título'}</div>
        `;
    }
    
    // Información de música
    const musicInfo = document.getElementById('current-music-info');
    if (musicInfo && video.music) {
        const musicText = video.music.artist ? 
            `${video.music.title} - ${video.music.artist}` : 
            video.music.title;
        
        musicInfo.innerHTML = `
            <i class="fas fa-music"></i>
            <span class="music-text">${musicText}</span>
        `;
    }
    
    // Tags/personajes
    const tagsContainer = document.getElementById('current-video-tags');
    if (tagsContainer) {
        if (video.characters && video.characters.length > 0) {
            tagsContainer.innerHTML = video.characters.map(char => 
                `<span class="video-tag">${char}</span>`
            ).join('');
        } else {
            tagsContainer.innerHTML = '';
        }
    }
    
    // Metadatos
    const metadataContainer = document.getElementById('current-video-metadata');
    if (metadataContainer) {
        const duration = video.duration_seconds ? 
            TagFlow.utils.formatDuration(video.duration_seconds) : '0:00';
        const platform = video.platform ? video.platform.toUpperCase() : 'UNKNOWN';
        const date = video.created_at ? video.created_at.split('T')[0] : 'Sin fecha';
        
        metadataContainer.innerHTML = `
            <span class="metadata-item">
                <i class="fas fa-clock"></i> 
                <span id="video-duration">${duration}</span>
            </span>
            <span class="metadata-item">
                <i class="fas fa-eye"></i> 
                <span id="video-platform">${platform}</span>
            </span>
            <span class="metadata-item">
                <i class="fas fa-calendar"></i> 
                <span id="video-date">${date}</span>
            </span>
        `;
    }
}

/**
 * Actualizar botones de navegación
 */
function updateNavigationButtons() {
    const prevBtn = document.querySelector('.nav-prev');
    const nextBtn = document.querySelector('.nav-next');
    
    if (prevBtn) {
        prevBtn.disabled = ShortsPlayer.currentIndex === 0;
    }
    
    if (nextBtn) {
        nextBtn.disabled = ShortsPlayer.currentIndex === ShortsPlayer.videos.length - 1;
    }
}

/**
 * Actualizar progreso del video
 */
function updateVideoProgress(index) {
    const videoElement = document.getElementById(`shorts-video-${index}`);
    const progressBar = document.getElementById(`progress-bar-${index}`);
    
    if (videoElement && progressBar) {
        const progress = (videoElement.currentTime / videoElement.duration) * 100;
        progressBar.style.width = `${progress}%`;
    }
}

/**
 * Función de debugging para verificar orden de videos
 */
function debugVideoOrder() {
    console.log('🔍 === DEBUG: ORDEN DE VIDEOS ===');
    console.log(`Total videos en ShortsPlayer: ${ShortsPlayer.videos.length}`);
    console.log(`Índice actual: ${ShortsPlayer.currentIndex}`);
    
    ShortsPlayer.videos.forEach((video, index) => {
        console.log(`${index}: ID=${video.id}, Creator=${video.creator_name}, Order=${video.order_in_gallery}`);
    });
    
    // Verificar elementos DOM
    const videoElements = ShortsPlayer.container.querySelectorAll('.shorts-video-item');
    console.log(`Elementos DOM creados: ${videoElements.length}`);
    
    videoElements.forEach((el, index) => {
        const videoId = el.dataset.videoId;
        const dataIndex = el.dataset.index;
        console.log(`DOM ${index}: videoId=${videoId}, dataIndex=${dataIndex}`);
    });
    
    console.log('🔍 === FIN DEBUG ===');
}

/**
 * Mostrar/ocultar loading específico de shorts
 */
function showShortsLoading(show) {
    const loadingElement = document.getElementById('shorts-loading');
    if (loadingElement) {
        loadingElement.style.display = show ? 'flex' : 'none';
    }
}

/**
 * Cerrar reproductor de shorts
 */
function closeShortsPlayer() {
    if (ShortsPlayer.modal) {
        ShortsPlayer.modal.hide();
    }
}

/**
 * Limpiar reproductor al cerrar
 */
function cleanupShortsPlayer() {
    // Pausar todos los videos
    ShortsPlayer.videos.forEach((video, index) => {
        pauseVideoAtIndex(index);
    });
    
    // Limpiar variables
    ShortsPlayer.currentIndex = 0;
    ShortsPlayer.videos = [];
    ShortsPlayer.currentVideo = null;
    ShortsPlayer.loadedVideos.clear();
    
    // Limpiar contenedor
    if (ShortsPlayer.container) {
        ShortsPlayer.container.innerHTML = '';
    }
    
    console.log('🧹 Reproductor de shorts limpiado');
}

/**
 * Reintentar cargar video
 */
async function retryLoadVideo(index) {
    ShortsPlayer.videos[index].loaded = false;
    await loadVideoAtIndex(index);
}

// Funciones para las acciones del overlay
function toggleVideoLike() {
    const likeBtn = document.querySelector('.action-btn[onclick="toggleVideoLike()"]');
    if (likeBtn) {
        likeBtn.classList.toggle('liked');
        const icon = likeBtn.querySelector('i');
        if (likeBtn.classList.contains('liked')) {
            icon.className = 'fas fa-heart';
            TagFlow.utils.showNotification('¡Te gusta este video!', 'success');
        } else {
            icon.className = 'far fa-heart';
        }
    }
}

function editCurrentVideo() {
    const currentVideo = ShortsPlayer.videos[ShortsPlayer.currentIndex];
    if (currentVideo) {
        closeShortsPlayer();
        setTimeout(() => editVideo(currentVideo.id), 300);
    }
}

function shareCurrentVideo() {
    const currentVideo = ShortsPlayer.videos[ShortsPlayer.currentIndex];
    if (currentVideo) {
        const shareText = `¡Mira este video de ${currentVideo.creator_name}!`;
        
        if (navigator.share) {
            navigator.share({
                title: shareText,
                text: shareText,
                url: window.location.href
            }).catch(err => console.log('Error sharing:', err));
        } else {
            // Fallback: copiar al portapapeles
            navigator.clipboard.writeText(shareText).then(() => {
                TagFlow.utils.showNotification('Enlace copiado al portapapeles', 'success');
            });
        }
    }
}

function openCurrentVideoFolder() {
    const currentVideo = ShortsPlayer.videos[ShortsPlayer.currentIndex];
    if (currentVideo) {
        openVideoFolder(currentVideo.id);
    }
}

function openCurrentVideoInSystem() {
    const currentVideo = ShortsPlayer.videos[ShortsPlayer.currentIndex];
    if (currentVideo) {
        openVideoFolder(currentVideo.id);
    }
}

console.log('🎬 Shorts Player JavaScript cargado');
