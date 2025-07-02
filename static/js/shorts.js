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
        
        // Mostrar header y overlay-info al usar teclado
        const header = document.querySelector('.shorts-header');
        const overlayInfo = document.querySelector('.overlay-info');
        
        if (header) {
            header.classList.remove('auto-hide');
            setTimeout(() => {
                header.classList.add('auto-hide');
            }, 2000);
        }
        
        if (overlayInfo) {
            overlayInfo.classList.remove('auto-hide');
            setTimeout(() => {
                overlayInfo.classList.add('auto-hide');
            }, 2000);
        }
        
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
    
    // Variables para throttling del scroll
    let scrollTimeout = null;
    let lastScrollTime = 0;
    const scrollThreshold = 150; // ms entre scrolls
    
    // Navegación con scroll del mouse (wheel)
    modalElement.addEventListener('wheel', function(e) {
        if (!modalElement.classList.contains('show')) return;
        
        e.preventDefault(); // Prevenir scroll de página
        
        // Throttling para evitar scroll demasiado sensible
        const currentTime = Date.now();
        if (currentTime - lastScrollTime < scrollThreshold) {
            return;
        }
        lastScrollTime = currentTime;
        
        // Mostrar header y overlay-info al usar wheel
        const header = document.querySelector('.shorts-header');
        const overlayInfo = document.querySelector('.overlay-info');
        
        if (header) {
            header.classList.remove('auto-hide');
            clearTimeout(headerHideTimeout);
            headerHideTimeout = setTimeout(() => {
                header.classList.add('auto-hide');
            }, 2000);
        }
        
        if (overlayInfo) {
            overlayInfo.classList.remove('auto-hide');
            clearTimeout(overlayInfoHideTimeout);
            overlayInfoHideTimeout = setTimeout(() => {
                overlayInfo.classList.add('auto-hide');
            }, 2000);
        }
        
        // Detectar dirección del scroll con umbral mínimo
        const deltaThreshold = 10; // Umbral mínimo para activar scroll
        
        if (e.deltaY > deltaThreshold) {
            // Scroll hacia abajo = siguiente video
            console.log('🖱️ Scroll down: siguiente video');
            nextVideo();
        } else if (e.deltaY < -deltaThreshold) {
            // Scroll hacia arriba = video anterior
            console.log('🖱️ Scroll up: video anterior');
            previousVideo();
        }
    }, { passive: false }); // passive: false para poder usar preventDefault
    
    // Gestos táctiles para dispositivos móviles
    let startY = 0;
    let startTime = 0;
    let headerHideTimeout;
    let overlayInfoHideTimeout;
    
    // Mostrar header y overlay-info al mover el mouse
    modalElement.addEventListener('mousemove', function() {
        const header = document.querySelector('.shorts-header');
        const overlayInfo = document.querySelector('.overlay-info');
        
        if (header) {
            header.classList.remove('auto-hide');
            
            // Limpiar timeout anterior y crear uno nuevo para header
            clearTimeout(headerHideTimeout);
            headerHideTimeout = setTimeout(() => {
                header.classList.add('auto-hide');
            }, 2000);
        }
        
        if (overlayInfo) {
            overlayInfo.classList.remove('auto-hide');
            
            // Limpiar timeout anterior y crear uno nuevo para overlay-info
            clearTimeout(overlayInfoHideTimeout);
            overlayInfoHideTimeout = setTimeout(() => {
                overlayInfo.classList.add('auto-hide');
            }, 2000);
        }
    });
    
    modalElement.addEventListener('touchstart', function(e) {
        startY = e.touches[0].clientY;
        startTime = Date.now();
        
        // Mostrar header y overlay-info al tocar
        const header = document.querySelector('.shorts-header');
        const overlayInfo = document.querySelector('.overlay-info');
        
        if (header) {
            header.classList.remove('auto-hide');
            clearTimeout(headerHideTimeout);
            headerHideTimeout = setTimeout(() => {
                header.classList.add('auto-hide');
            }, 2000);
        }
        
        if (overlayInfo) {
            overlayInfo.classList.remove('auto-hide');
            clearTimeout(overlayInfoHideTimeout);
            overlayInfoHideTimeout = setTimeout(() => {
                overlayInfo.classList.add('auto-hide');
            }, 2000);
        }
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
        }, 3000);
        
        // Auto-hide del header después de 2.5 segundos
        setTimeout(() => {
            const header = document.querySelector('.shorts-header');
            if (header) {
                header.classList.add('auto-hide');
            }
        }, 2500);
        
        // Auto-hide del overlay-info después de 2.5 segundos
        setTimeout(() => {
            const overlayInfo = document.querySelector('.overlay-info');
            if (overlayInfo) {
                overlayInfo.classList.add('auto-hide');
            }
        }, 2500);
        
        // Agregar event listeners específicos para overlay-info hover
        setTimeout(() => {
            const overlayInfo = document.querySelector('.overlay-info');
            if (overlayInfo) {
                overlayInfo.addEventListener('mouseenter', function() {
                    this.classList.remove('auto-hide');
                    clearTimeout(overlayInfoHideTimeout);
                });
                
                overlayInfo.addEventListener('mouseleave', function() {
                    clearTimeout(overlayInfoHideTimeout);
                    overlayInfoHideTimeout = setTimeout(() => {
                        this.classList.add('auto-hide');
                    }, 1500); // Más corto después del hover
                });
            }
        }, 100); // Pequeño delay para asegurar que el elemento existe
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
            // Asegurar posicionamiento inicial
            scrollToVideo(videoIndex);
            
            // Dar tiempo para que el DOM se actualice y forzar reflow
            setTimeout(async () => {
                // Verificar que el video esté listo antes de reproducir
                const initialVideo = document.getElementById(`shorts-video-${videoIndex}`);
                if (initialVideo) {
                    console.log(`🎬 Estado del video inicial: readyState=${initialVideo.readyState}`);
                    
                    // Forzar que el video sea visible
                    initialVideo.style.opacity = '1';
                    initialVideo.style.display = 'block';
                    
                    // Si el video no está listo, mostrar loader hasta que lo esté
                    if (initialVideo.readyState < 3) {
                        showVideoLoader(videoIndex);
                        console.log(`⏳ Video inicial no listo, esperando...`);
                    } else {
                        hideVideoLoader(videoIndex);
                        console.log(`✅ Video inicial listo para reproducir`);
                    }
                    
                    // SOLO reproducir si aún es el video actual
                    if (videoIndex === ShortsPlayer.currentIndex) {
                        // Reproducir video inicial automáticamente
                        await playVideoAtIndex(videoIndex);
                    }
                }
                
                // Precargar videos adyacentes
                preloadAdjacentVideos();
            }, 300);
        }, 600);
        
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
        
        // Placeholder inicial con preloader
        videoElement.innerHTML = `
            <div class="video-preloader">
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">Cargando video...</span>
                </div>
            </div>
            <div class="video-progress">
                <div class="video-progress-bar"></div>
            </div>
        `;
        
        ShortsPlayer.container.appendChild(videoElement);
        
        // Posicionar inicialmente
        const offset = index * 100;
        videoElement.style.transform = `translateY(${offset}vh)`;
        
        console.log(`📦 Elemento creado para video ${index}: ID=${video.id}`);
    });
    
    console.log(`✅ ${ShortsPlayer.videos.length} elementos de video creados`);
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
                onloadeddata="onVideoDataLoaded(${index})"
                oncanplay="onVideoCanPlay(${index})"
                onloadedmetadata="console.log('Video ${index} metadata loaded'); updateVideoProgress(${index})"
                ontimeupdate="updateVideoProgress(${index})"
                onended="nextVideo()"
                onclick="handleVideoClick(${index})"
                onerror="console.error('Video ${index} error:', event)"
                onloadstart="console.log('Video ${index} load started')"
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
    
    console.log(`🎯 Navegando de video ${previousIndex} a ${index}`);
    
    // Pausar video anterior
    pauseVideoAtIndex(previousIndex);
    
    // Verificar si el video ya está cargado y listo
    const videoElement = document.getElementById(`shorts-video-${index}`);
    const isVideoReady = videoElement && videoElement.readyState >= 3; // HAVE_FUTURE_DATA
    
    if (!ShortsPlayer.videos[index].loaded) {
        console.log(`📥 Video ${index} no cargado, cargando...`);
        showShortsLoading(true);
        await loadVideoAtIndex(index);
        showShortsLoading(false);
    } else if (!isVideoReady) {
        console.log(`⏳ Video ${index} cargado pero no listo, esperando...`);
        showVideoLoader(index);
    } else {
        console.log(`✅ Video ${index} ya está listo para reproducir`);
        hideVideoLoader(index);
    }
    
    // Actualizar UI primero (scroll)
    scrollToVideo(index);
    updateShortsUI();
    
    // Esperar un momento antes de reproducir para evitar conflictos
    setTimeout(async () => {
        // Reproducir video actual solo si sigue siendo el video actual
        if (index === ShortsPlayer.currentIndex) {
            await playVideoAtIndex(index);
        }
        
        // Precargar videos adyacentes
        preloadAdjacentVideos();
        
        // Permitir nuevas transiciones después de un breve delay
        setTimeout(() => {
            ShortsPlayer.isTransitioning = false;
        }, 300);
    }, 200);
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
    
    // Evitar múltiples llamadas simultáneas al mismo video
    if (videoElement.dataset.isPlaying === 'true') {
        console.log(`⚠️ Video ${index} ya está en proceso de reproducción`);
        return;
    }
    
    console.log(`▶️ Intentando reproducir video ${index}`);
    videoElement.dataset.isPlaying = 'true';
    
    // Esperar hasta que el video esté listo si no lo está
    if (videoElement.readyState < 3) { // HAVE_FUTURE_DATA
        console.log(`⏳ Video ${index} no está listo, esperando...`);
        showVideoLoader(index);
        
        return new Promise((resolve) => {
            const onCanPlay = () => {
                console.log(`✅ Video ${index} ahora está listo`);
                videoElement.removeEventListener('canplay', onCanPlay);
                hideVideoLoader(index);
                // Usar setTimeout para evitar llamadas recursivas inmediatas
                setTimeout(() => {
                    playVideoAtIndex(index).then(resolve);
                }, 100);
            };
            
            videoElement.addEventListener('canplay', onCanPlay);
            
            // Timeout de seguridad
            setTimeout(() => {
                videoElement.removeEventListener('canplay', onCanPlay);
                hideVideoLoader(index);
                console.warn(`⚠️ Timeout esperando video ${index}, intentando reproducir anyway`);
                setTimeout(() => {
                    playVideoAtIndex(index).then(resolve);
                }, 100);
            }, 3000);
        });
    }
    
    try {
        // Pausar video anterior si existe
        if (ShortsPlayer.currentVideo && ShortsPlayer.currentVideo !== videoElement) {
            ShortsPlayer.currentVideo.pause();
            ShortsPlayer.currentVideo.dataset.isPlaying = 'false';
            console.log(`⏸️ Video anterior pausado`);
        }
        
        // Asegurar que el loader esté oculto
        hideVideoLoader(index);
        
        // SOLO reiniciar si el video no está cerca del inicio
        // Esto evita el reinicio constante que causa el problema
        if (videoElement.currentTime > 2) {
            videoElement.currentTime = 0;
        }
        
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
                
                // Solo mostrar notificación la primera vez
                if (index === ShortsPlayer.currentIndex) {
                    TagFlow.utils.showNotification('Haz clic en el video para activar el audio', 'info');
                }
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
        hideVideoLoader(index);
        TagFlow.utils.showNotification(`Error reproduciendo video ${index}`, 'error');
    } finally {
        // Limpiar flag después de un breve delay
        setTimeout(() => {
            videoElement.dataset.isPlaying = 'false';
        }, 1000);
    }
}

/**
 * Pausar video en el índice especificado
 */
function pauseVideoAtIndex(index) {
    const videoElement = document.getElementById(`shorts-video-${index}`);
    if (videoElement) {
        videoElement.pause();
        videoElement.dataset.isPlaying = 'false';
    }
}

/**
 * Callback cuando el video tiene datos cargados
 */
function onVideoDataLoaded(index) {
    console.log(`📊 Video ${index} data loaded`);
    hideVideoLoader(index);
}

/**
 * Callback cuando el video puede reproducirse
 */
function onVideoCanPlay(index) {
    console.log(`▶️ Video ${index} can play - ready for playback`);
    hideVideoLoader(index);
    
    // Solo auto-iniciar si es el video actual Y aún no se está reproduciendo
    if (index === ShortsPlayer.currentIndex) {
        const videoElement = document.getElementById(`shorts-video-${index}`);
        if (videoElement && videoElement.paused && videoElement.dataset.isPlaying !== 'true') {
            console.log(`🎬 Auto-starting video ${index} since it's current and not playing`);
            // Pequeño delay para evitar conflictos
            setTimeout(() => {
                playVideoAtIndex(index);
            }, 150);
        }
    }
}

/**
 * Ocultar loader específico de un video
 */
function hideVideoLoader(index) {
    const videoElement = ShortsPlayer.container.querySelector(`[data-index="${index}"]`);
    if (videoElement) {
        const loader = videoElement.querySelector('.video-preloader');
        if (loader) {
            loader.style.display = 'none';
            console.log(`🎯 Loader oculto para video ${index}`);
        }
    }
}

/**
 * Mostrar loader específico de un video
 */
function showVideoLoader(index) {
    const videoElement = ShortsPlayer.container.querySelector(`[data-index="${index}"]`);
    if (videoElement) {
        const loader = videoElement.querySelector('.video-preloader');
        if (loader) {
            loader.style.display = 'flex';
            console.log(`⏳ Loader mostrado para video ${index}`);
        }
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
            // Asegurar que el video esté visible
            const video = el.querySelector('video');
            if (video) {
                video.style.opacity = '1';
            }
            console.log(`✅ Video ${i} marcado como activo`);
        } else if (i < index) {
            el.classList.add('prev');
        } else {
            el.classList.add('next');
        }
        
        // Logging para debug
        console.log(`📍 Video ${i}: transform=${el.style.transform}, classes=${el.className}`);
    });
    
    // Forzar reflow para asegurar que las transformaciones se apliquen
    ShortsPlayer.container.offsetHeight;
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
            <div class="video-title">${video.display_title || video.file_name || 'Video sin título'}</div>
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
    
    // Ocultar todos los loaders
    showShortsLoading(false);
    ShortsPlayer.videos.forEach((video, index) => {
        hideVideoLoader(index);
    });
    
    // Limpiar variables
    ShortsPlayer.currentIndex = 0;
    ShortsPlayer.videos = [];
    ShortsPlayer.currentVideo = null;
    ShortsPlayer.loadedVideos.clear();
    ShortsPlayer.isTransitioning = false;
    
    // Limpiar contenedor
    if (ShortsPlayer.container) {
        ShortsPlayer.container.innerHTML = '';
    }
    
    // Limpiar clases auto-hide para reset
    const headerElements = document.querySelectorAll('.shorts-header');
    const overlayInfoElements = document.querySelectorAll('.overlay-info');
    
    headerElements.forEach(header => header.classList.remove('auto-hide'));
    overlayInfoElements.forEach(overlay => overlay.classList.remove('auto-hide'));
    
    console.log('🧹 Reproductor de shorts limpiado completamente');
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
