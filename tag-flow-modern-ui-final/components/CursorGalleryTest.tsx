/**
 * Tag-Flow V2 - Cursor Gallery Test Component
 * Componente de prueba para el nuevo sistema cursor antes de migración completa
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { useCursorData } from '../hooks/useCursorData';
import PostCard from './VideoCard';

interface CursorGalleryTestProps {
  className?: string;
}

export const CursorGalleryTest: React.FC<CursorGalleryTestProps> = ({ className = '' }) => {
  const {
    posts,
    loading,
    loadingMore,
    error,
    scrollState,
    loadMoreVideos,
    refreshData,
    getStats,
    setFilters,
    clearFilters
  } = useCursorData();

  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const stats = getStats();

  // Infinite scroll handler
  const handleScroll = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container || loadingMore || !scrollState.hasMore) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const scrollPercentage = scrollTop / (scrollHeight - clientHeight);

    // Load more when 80% scrolled
    if (scrollPercentage > 0.8) {
      loadMoreVideos();
    }
  }, [loadMoreVideos, loadingMore, scrollState.hasMore]);

  // Attach scroll listener
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [handleScroll]);

  // Test filters
  const testFilters = [
    { label: 'All', filters: {} },
    { label: 'YouTube', filters: { platform: 'youtube' } },
    { label: 'TikTok', filters: { platform: 'tiktok' } },
    { label: 'With Music', filters: { has_music: true } },
    { label: 'Completed', filters: { edit_status: 'completed' } },
  ];

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-medium">Error Loading Videos</h3>
        <p className="text-red-600 text-sm mt-1">{error}</p>
        <button
          onClick={refreshData}
          className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={`cursor-gallery-test ${className}`}>
      {/* Header with stats and controls */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            🚀 Cursor Pagination Test
          </h2>
          <button
            onClick={refreshData}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {/* Performance Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-blue-600 text-sm font-medium">Videos Loaded</div>
            <div className="text-blue-900 text-lg font-bold">{stats.loaded}</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-green-600 text-sm font-medium">Query Time</div>
            <div className="text-green-900 text-lg font-bold">
              {stats.performance.avgQueryTime.toFixed(1)}ms
            </div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-purple-600 text-sm font-medium">Cache Hit Rate</div>
            <div className="text-purple-900 text-lg font-bold">
              {stats.performance.cacheHitRate.toFixed(0)}%
            </div>
          </div>
          <div className="bg-orange-50 p-3 rounded">
            <div className="text-orange-600 text-sm font-medium">Has More</div>
            <div className="text-orange-900 text-lg font-bold">
              {scrollState.hasMore ? 'Yes' : 'No'}
            </div>
          </div>
        </div>

        {/* Filter buttons */}
        <div className="flex flex-wrap gap-2">
          {testFilters.map((filter, index) => (
            <button
              key={index}
              onClick={() => setFilters(filter.filters)}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
              disabled={loading}
            >
              {filter.label}
            </button>
          ))}
          <button
            onClick={clearFilters}
            className="px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200"
            disabled={loading}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Videos Grid */}
      <div
        ref={scrollContainerRef}
        className="max-h-screen overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100"
      >
        {loading && posts.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading videos with cursor pagination...</span>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {posts.map((post) => (
                <PostCard
                  key={post.id}
                  video={post}
                  videos={posts}
                  isSelected={false}
                  onSelect={() => {}}
                  onEdit={() => {}}
                  isHighlighted={false}
                />
              ))}
            </div>

            {/* Loading more indicator */}
            {loadingMore && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">Loading more videos...</span>
              </div>
            )}

            {/* No more videos */}
            {!scrollState.hasMore && posts.length > 0 && (
              <div className="text-center py-8">
                <div className="text-gray-500">
                  ✅ All videos loaded ({posts.length} total)
                </div>
              </div>
            )}

            {/* No videos */}
            {!loading && posts.length === 0 && (
              <div className="text-center py-12">
                <div className="text-gray-500">
                  No videos found with current filters
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Debug Info */}
      <div className="mt-4 p-3 bg-gray-50 rounded text-xs text-gray-600">
        <strong>Debug:</strong> Cursor: {scrollState.cursor || 'none'} |
        Queries: {stats.performance.totalQueries} |
        Loading: {loading ? 'Yes' : 'No'} |
        LoadingMore: {loadingMore ? 'Yes' : 'No'}
      </div>
    </div>
  );
};