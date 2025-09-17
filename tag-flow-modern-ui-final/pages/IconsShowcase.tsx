import React from 'react';
import { FRONTEND_ICON_CATEGORIES, ICONS, SUBSCRIPTION_ICONS, CATEGORY_ICONS, getSubscriptionIcon, getCategoryIcon } from '../constants';

const IconsShowcase: React.FC = () => {
  // Use the organized categories by frontend sections from constants.tsx
  const categories = FRONTEND_ICON_CATEGORIES;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8 text-center">
          Showcase de Iconos - Tag Flow
        </h1>

        <div className="grid gap-12">
          {Object.entries(categories).map(([categoryName, iconObjects]) => (
            <div key={categoryName} className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6 border-b-2 border-blue-200 pb-3">
                {categoryName}
              </h2>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-8">
                {Object.entries(iconObjects).map(([iconName, iconElement]) => (
                  <div
                    key={iconName}
                    className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-blue-50 hover:shadow-md transition-all duration-200 border border-gray-200"
                  >
                    <div className="text-gray-700 mb-3 p-2">
                      {iconElement}
                    </div>
                    <span className="text-xs text-gray-600 text-center font-medium break-all">
                      {iconName}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Sección adicional con todos los iconos no categorizados */}
        <div className="bg-white rounded-lg shadow-lg p-8 mt-12">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6 border-b-2 border-green-200 pb-3">
            Todos los Iconos (Vista Completa)
          </h2>

          <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 xl:grid-cols-12 gap-6">
            {Object.entries(ICONS).map(([iconName, iconElement]) => (
              <div
                key={iconName}
                className="flex flex-col items-center p-3 bg-gray-50 rounded-md hover:bg-green-50 hover:shadow-sm transition-all duration-150 border border-gray-200"
              >
                <div className="text-gray-700 mb-2">
                  {iconElement}
                </div>
                <span className="text-xs text-gray-500 text-center font-mono break-all leading-tight">
                  {iconName}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Mapeos de Database Schema */}
        <div className="grid md:grid-cols-2 gap-8 mt-12">
          {/* Subscription Types */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-purple-900 mb-4">
              📋 Mapeo Subscription Types (Database)
            </h3>
            <div className="space-y-3">
              {Object.entries(SUBSCRIPTION_ICONS).map(([dbValue, iconElement]) => (
                <div key={dbValue} className="flex items-center gap-3 p-2 bg-white rounded border">
                  <div className="text-purple-700">
                    {iconElement}
                  </div>
                  <span className="text-sm font-mono text-purple-800">
                    '{dbValue}'
                  </span>
                  <span className="text-xs text-purple-600">
                    → getSubscriptionIcon('{dbValue}')
                  </span>
                </div>
              ))}

              {/* Special cases with platform logic */}
              <div className="mt-4 p-3 bg-purple-100 rounded border-2 border-purple-300">
                <h4 className="text-sm font-semibold text-purple-900 mb-2">🎯 Casos Especiales por Plataforma:</h4>
                <div className="space-y-2 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="text-purple-700">{getSubscriptionIcon('liked', 'youtube')}</div>
                    <span className="font-mono">getSubscriptionIcon('liked', 'youtube')</span>
                    <span className="text-purple-600">→ Thumbs up (YouTube)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-purple-700">{getSubscriptionIcon('liked', 'tiktok')}</div>
                    <span className="font-mono">getSubscriptionIcon('liked', 'tiktok')</span>
                    <span className="text-purple-600">→ Heart (TikTok/Instagram)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Category Types */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-900 mb-4">
              🎞️ Mapeo Category Types (Database)
            </h3>
            <div className="space-y-3">
              {Object.entries(CATEGORY_ICONS).map(([dbValue, iconElement]) => (
                <div key={dbValue} className="flex items-center gap-3 p-2 bg-white rounded border">
                  <div className="text-green-700">
                    {iconElement}
                  </div>
                  <span className="text-sm font-mono text-green-800">
                    '{dbValue}'
                  </span>
                  <span className="text-xs text-green-600">
                    → getCategoryIcon('{dbValue}')
                  </span>
                </div>
              ))}

              {/* Special cases with platform logic */}
              <div className="mt-4 p-3 bg-green-100 rounded border-2 border-green-300">
                <h4 className="text-sm font-semibold text-green-900 mb-2">🎯 Casos Especiales por Plataforma:</h4>
                <div className="space-y-2 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="text-green-700">{getCategoryIcon('videos')}</div>
                    <span className="font-mono">getCategoryIcon('videos')</span>
                    <span className="text-green-600">→ Video icon (All platforms)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-green-700">{getCategoryIcon('videos', 'tiktok')}</div>
                    <span className="font-mono">getCategoryIcon('videos', 'tiktok')</span>
                    <span className="text-green-600">→ Rack icon (TikTok only)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Información técnica */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mt-8">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            📋 Información Técnica
          </h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <strong>Total de iconos:</strong> {Object.keys(ICONS).length}
            </div>
            <div>
              <strong>Tipo:</strong> Elementos React inline SVG
            </div>
            <div>
              <strong>Rendimiento:</strong> Carga instantánea (sin HTTP requests)
            </div>
            <div>
              <strong>Uso:</strong> {`{ICONS.iconName}`} o React.cloneElement
            </div>
            <div className="md:col-span-2 mt-2">
              <strong>Helper Functions:</strong> getSubscriptionIcon(type, platform?) y getCategoryIcon(type, platform?) para mapeos de database con lógica específica de plataforma
            </div>
            <div className="md:col-span-2 mt-2 text-xs">
              <strong>Nuevos iconos agregados:</strong> liked (👍), saved (💾), watch_later (⏰) para subscription types
            </div>
            <div className="md:col-span-2 mt-2 text-xs">
              <strong>Casos especiales:</strong> liked (YouTube vs TikTok/Instagram), videos (All vs TikTok)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IconsShowcase;