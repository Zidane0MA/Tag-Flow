/**
 * 🚀 Virtualized Gallery - Versión optimizada para GalleryPage
 * Virtualización que respeta el scroll principal y layout original
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Post } from '../types';
import VideoCard from './VideoCard';

interface VirtualizedGalleryProps {
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

const VirtualizedGallery: React.FC<VirtualizedGalleryProps> = ({
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
  const [scrollTop, setScrollTop] = useState(0);
  const [cardsPerRow, setCardsPerRow] = useState(4);
  const containerRef = useRef<HTMLDivElement>(null);

  // Configuración adaptativa
  const CARD_HEIGHT = 360; // Altura aproximada de VideoCard
  const GAP = 32; // gap-8
  const ROW_HEIGHT = CARD_HEIGHT + GAP;
  const BUFFER_ROWS = 2; // Filas extra para renderizar

  // Detectar cards per row basado en breakpoints de Tailwind
  useEffect(() => {
    const updateCardsPerRow = () => {
      const width = window.innerWidth;
      if (width < 640) setCardsPerRow(1);        // sm
      else if (width < 1024) setCardsPerRow(2);  // lg
      else if (width < 1280) setCardsPerRow(3);  // xl
      else setCardsPerRow(4);                    // 2xl+
    };

    updateCardsPerRow();
    window.addEventListener('resize', updateCardsPerRow);
    return () => window.removeEventListener('resize', updateCardsPerRow);
  }, []);

  // Monitorear scroll del contenedor principal
  useEffect(() => {
    const mainElement = document.querySelector('main');
    if (!mainElement) return;

    const handleScroll = () => {
      setScrollTop(mainElement.scrollTop);
    };

    mainElement.addEventListener('scroll', handleScroll, { passive: true });
    return () => mainElement.removeEventListener('scroll', handleScroll);
  }, []);

  // Calcular qué items son visibles
  const { visiblePosts, spacerHeight, offsetY } = useMemo(() => {
    const totalRows = Math.ceil(posts.length / cardsPerRow);
    const containerTop = containerRef.current?.offsetTop || 0;

    // Calcular posición del scroll relativa al container
    const relativeScrollTop = Math.max(0, scrollTop - containerTop);

    // Determinar filas visibles
    const viewportHeight = window.innerHeight;
    const startRow = Math.max(0, Math.floor(relativeScrollTop / ROW_HEIGHT) - BUFFER_ROWS);
    const visibleRowCount = Math.ceil(viewportHeight / ROW_HEIGHT) + BUFFER_ROWS * 2;
    const endRow = Math.min(totalRows, startRow + visibleRowCount);

    // Calcular indices de posts
    const startIndex = startRow * cardsPerRow;
    const endIndex = Math.min(posts.length, endRow * cardsPerRow);

    return {
      visiblePosts: posts.slice(startIndex, endIndex),
      spacerHeight: totalRows * ROW_HEIGHT,
      offsetY: startRow * ROW_HEIGHT
    };
  }, [posts, scrollTop, cardsPerRow]);

  return (
    <div ref={containerRef} id="gallery-container">
      {/* Container con altura total para mantener el scroll */}
      <div style={{ height: spacerHeight, position: 'relative' }}>
        {/* Grid renderizado con offset */}
        <div
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0
          }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8"
        >
          {visiblePosts.map((post) => (
            <VideoCard
              key={post.id}
              video={post}
              videos={posts}
              isSelected={selectedPosts.includes(post.id)}
              onSelect={onSelectPost}
              onEdit={onEditPost}
              isHighlighted={highlightedVideoId === post.id}
              onRefresh={onRefreshData}
            />
          ))}
        </div>
      </div>

      {/* Loading indicator */}
      {loadingMore && (
        <div className="flex justify-center items-center py-8">
          <div className="flex items-center space-x-2 text-gray-400">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-500"></div>
            <span>Cargando más videos...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default VirtualizedGallery;