/**
 * Tag-Flow V2 - Cursor Test Page
 * Página de prueba completa con todas las optimizaciones implementadas
 */

import React, { useState } from 'react';
import { CursorDataProvider, useCursorData } from '../hooks/useCursorData';
import { CursorGalleryTest } from '../components/CursorGalleryTest';
import VirtualizedGalleryDebug from '../components/VirtualizedGalleryDebug';

// Componente interno con todas las optimizaciones
const CursorTestContent: React.FC = () => {
  const {
    posts,
    loading,
    loadingMore,
    loadMoreVideos,
    scrollState,
    getStats
  } = useCursorData();

  const [useVirtualization, setUseVirtualization] = useState(true);
  const [showStats, setShowStats] = useState(true);

  const stats = getStats();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">🚀 Cursor Optimization Test</h1>
        <p className="text-gray-600 mt-2">
          Página completa de testing con todas las optimizaciones: cursor pagination, cache unificado,
          prefetching inteligente, WebSocket real-time y virtualización DOM.
        </p>
      </div>

      {/* Estadísticas y controles */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Stats Panel */}
        {showStats && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-800 mb-2">📊 Performance Stats</h3>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">Posts cargados:</span> {stats.loaded}
              </div>
              <div>
                <span className="font-medium">Más datos:</span> {stats.hasMore ? 'Sí' : 'No'}
              </div>
              <div>
                <span className="font-medium">Query time promedio:</span> {stats.performance.avgQueryTime.toFixed(1)}ms
              </div>
              <div>
                <span className="font-medium">Cache hit rate:</span> {stats.performance.cacheHitRate.toFixed(1)}%
              </div>
              <div>
                <span className="font-medium">Cache entries:</span> {stats.cache?.totalEntries || 0}
              </div>
              <div>
                <span className="font-medium">Cache size:</span> {((stats.cache?.totalSizeBytes || 0) / 1024).toFixed(1)}KB
              </div>
            </div>
          </div>
        )}

        {/* Controls Panel */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2">🎛️ Controls</h3>
          <div className="space-y-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={useVirtualization}
                onChange={(e) => setUseVirtualization(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm font-medium">Virtualización DOM</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showStats}
                onChange={(e) => setShowStats(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm font-medium">Mostrar estadísticas</span>
            </label>
          </div>
        </div>
      </div>

      {/* Galería con o sin virtualización */}
      {posts.length > 0 ? (
        useVirtualization ? (
          <VirtualizedGalleryDebug
            posts={posts}
            loading={loading}
            loadingMore={loadingMore}
            onLoadMore={loadMoreVideos}
            hasMore={scrollState.hasMore}
          />
        ) : (
          <CursorGalleryTest />
        )
      ) : (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg">
            {loading ? 'Cargando videos...' : 'No hay videos disponibles'}
          </div>
        </div>
      )}
    </div>
  );
};

export const CursorTestPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-6">
      <CursorDataProvider>
        <CursorTestContent />
      </CursorDataProvider>
    </div>
  );
};