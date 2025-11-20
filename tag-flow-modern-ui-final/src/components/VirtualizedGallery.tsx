import React, { useMemo, useRef } from 'react';
import { Post } from '../types';
import VideoCard from './VideoCard';

interface VirtualizedGalleryProps {
  posts: Post[];
  loadingMore?: boolean;
  selectedPosts?: string[];
  onSelectPost?: (postId: string) => void;
  onEditPost?: (post: Post) => void;
  onRefreshData?: () => void;
  highlightedVideoId?: string;
  // Nuevas props para controlar la virtualización desde el padre
  scrollTop: number;
  containerHeight: number;
}

const VirtualizedGallery: React.FC<VirtualizedGalleryProps> = ({
  posts,
  loadingMore,
  selectedPosts = [],
  onSelectPost,
  onEditPost,
  onRefreshData,
  highlightedVideoId,
  scrollTop,
  containerHeight
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Configuración fija (siguiendo mejores prácticas)
  const ITEM_HEIGHT = 400; // Altura fija para evitar cálculos complejos
  const ITEMS_PER_ROW = 4; // Fijo para simplificar
  const OVERSCAN = 2; // Buffer de filas (overscan)

  // Cálculos de virtualización simples, ahora controlados por props
  const { visibleItems, totalHeight, offsetY } = useMemo(() => {
    const totalItems = posts.length;
    const totalRows = Math.ceil(totalItems / ITEMS_PER_ROW);
    const total = totalRows * ITEM_HEIGHT;

    const containerTop = containerRef.current?.offsetTop || 0;
    const relativeScroll = Math.max(0, scrollTop - containerTop);

    const startRow = Math.floor(relativeScroll / ITEM_HEIGHT);
    const endRow = startRow + Math.ceil(containerHeight / ITEM_HEIGHT) + OVERSCAN;

    const visibleStartRow = Math.max(0, startRow - OVERSCAN);
    const visibleEndRow = Math.min(totalRows, endRow);

    const startIndex = visibleStartRow * ITEMS_PER_ROW;
    const endIndex = Math.min(totalItems, visibleEndRow * ITEMS_PER_ROW);

    return {
      visibleItems: posts.slice(startIndex, endIndex),
      totalHeight: total,
      offsetY: visibleStartRow * ITEM_HEIGHT
    };
  }, [posts, scrollTop, containerHeight]);

  return (
    <div ref={containerRef} className="relative">
      {/* Spacer para mantener altura total */}
      <div style={{ height: totalHeight, position: 'relative' }}>
        {/* Container de items visibles */}
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0
          }}
          className="grid grid-cols-4 gap-8"
        >
          {visibleItems.map((post) => (
            <div key={post.id} style={{ height: ITEM_HEIGHT }}>
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