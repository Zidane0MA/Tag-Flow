import React from 'react';
import { FRONTEND_ICON_CATEGORIES, ICONS } from '../constants';

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
          </div>
        </div>
      </div>
    </div>
  );
};

export default IconsShowcase;