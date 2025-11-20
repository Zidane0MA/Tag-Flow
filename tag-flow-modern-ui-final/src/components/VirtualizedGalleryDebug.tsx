/**
 * 🚀 Virtualized Gallery Debug - Version con debug para cursor-test
 * Solo renderiza los elementos visibles en pantalla para mantener el DOM ligero
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Post } from '../types';
import VideoCard from './VideoCard';

interface VirtualizedGalleryDebugProps {
  posts: Post[];
  loading?: boolean;
  loadingMore?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
  selectedPosts?: string[];
  onSelectPost?: (postId: string) => void;
  onEditPost?: (post: Post) => void;
  onRefreshData?: () => void;
  highlightedVideoId?: string;
}

const VirtualizedGalleryDebug: React.FC<VirtualizedGalleryDebugProps> = ({
  posts,
  loading,
  loadingMore,
  onLoadMore,
  hasMore,
  selectedPosts = [],
  onSelectPost,
  onEditPost,
  onRefreshData,
  highlightedVideoId
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerHeight, setContainerHeight] = useState(0);
  const [scrollTop, setScrollTop] = useState(0);

  // Configuración de virtualización
  const itemHeight = 400; // Altura aproximada de cada VideoCard
  const itemsPerRow = 4; // Columnas en desktop
  const rowHeight = itemHeight + 32; // Altura + gap
  const overscan = 2; // Renderizar 2 filas extra arriba y abajo

  // Calcular dimensiones
  const totalRows = Math.ceil(posts.length / itemsPerRow);
  const totalHeight = totalRows * rowHeight;

  // Calcular qué elementos renderizar
  const startRow = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const endRow = Math.min(
    totalRows - 1,
    Math.floor((scrollTop + containerHeight) / rowHeight) + overscan
  );

  // Calcular índices de items visibles
  const startIndex = startRow * itemsPerRow;
  const endIndex = Math.min((endRow + 1) * itemsPerRow, posts.length);
  const visibleItems = posts.slice(startIndex, endIndex);

  // Manejo del scroll del window principal
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const scrollTop = Math.max(0, -rect.top);
    setScrollTop(scrollTop);

    // Trigger load more cuando esté cerca del final
    if (hasMore && !loadingMore && onLoadMore) {
      const windowScrollY = window.scrollY;
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;

      if (windowScrollY + windowHeight >= documentHeight - 1000) {
        onLoadMore();
      }
    }
  }, [hasMore, loadingMore, onLoadMore]);

  // Setup scroll y resize listeners
  useEffect(() => {
    const updateHeight = () => {
      setContainerHeight(window.innerHeight);
    };

    updateHeight();
    window.addEventListener('resize', updateHeight);
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('resize', updateHeight);
      window.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll]);

  // Responsive: ajustar itemsPerRow según ancho de pantalla
  const getItemsPerRow = () => {
    if (!containerRef.current) return 4;
    const width = containerRef.current.clientWidth;
    if (width < 640) return 1; // sm
    if (width < 1024) return 2; // lg
    if (width < 1280) return 3; // xl
    return 4; // 2xl+
  };

  return (
    <div className="space-y-4">
      {/* Debug Panel - Solo en cursor-test */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-800 mb-2">🚀 Virtualización Debug</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="font-medium text-blue-700">Total Posts:</span>
            <div className="text-lg font-bold text-blue-900">{posts.length}</div>
          </div>
          <div>
            <span className="font-medium text-blue-700">Renderizados:</span>
            <div className="text-lg font-bold text-green-600">{visibleItems.length}</div>
          </div>
          <div>
            <span className="font-medium text-blue-700">DOM Savings:</span>
            <div className="text-lg font-bold text-purple-600">
              {posts.length > 0 ? Math.round((1 - visibleItems.length / posts.length) * 100) : 0}%
            </div>
          </div>
          <div>
            <span className="font-medium text-blue-700">Scroll:</span>
            <div className="text-lg font-bold text-gray-600">{Math.round(scrollTop)}px</div>
          </div>
        </div>
        <div className="mt-2 text-xs text-blue-600">
          Filas: {startRow}-{endRow} de {totalRows} |
          Índices: {startIndex}-{endIndex} |
          Altura: {totalHeight}px
        </div>
      </div>

      {/* Galería virtualizada */}
      <div
        ref={containerRef}
        id="gallery-container"
        className="w-full"
      >
        {/* Contenedor principal con altura total */}
        <div style={{ height: totalHeight, position: 'relative' }}>
          {/* Grid virtualizado */}
          <div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 px-4"
            style={{
              position: 'absolute',
              top: startRow * rowHeight,
              width: '100%'
            }}
          >
            {visibleItems.map((post, index) => {
              const globalIndex = startIndex + index;
              return (
                <div
                  key={`${post.id}-${globalIndex}`}
                  data-cursor={`${post.publicationDate}|${post.id}`}
                  style={{ height: itemHeight }}
                >
                  <VideoCard
                    video={post}
                    videos={posts}
                    isSelected={selectedPosts.includes(post.id)}
                    onSelect={onSelectPost}
                    onEdit={onEditPost}
                    isHighlighted={highlightedVideoId === post.id}
                    onRefresh={onRefreshData}
                  />
                </div>
              );
            })}
          </div>

          {/* Loading indicators */}
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/80">
              <div className="flex flex-col items-center space-y-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                <p className="text-lg font-medium text-gray-700">Cargando videos...</p>
              </div>
            </div>
          )}

          {loadingMore && (
            <div className="absolute bottom-0 left-0 right-0 flex justify-center py-8">
              <div className="flex items-center space-x-3 bg-white rounded-lg shadow-lg px-6 py-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="text-gray-700 font-medium">Cargando más videos...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VirtualizedGalleryDebug;