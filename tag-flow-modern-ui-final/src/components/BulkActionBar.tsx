import React from 'react';
import { ICONS } from '../constants';

interface BulkActionBarProps {
  selectedCount: number;
  onReanalyze?: () => void;
  onEdit?: () => void;
  onRestore?: () => void;
  onDelete: () => void;
  onClear: () => void;
  isVisible: boolean;
  isLoading?: boolean;
}

const BulkActionBar: React.FC<BulkActionBarProps> = ({
  selectedCount,
  onReanalyze,
  onEdit,
  onRestore,
  onDelete,
  onClear,
  isVisible,
  isLoading = false,
}) => {
  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 w-auto max-w-[95vw] bg-[#2d2d2d]/90 backdrop-blur-sm text-white rounded-xl shadow-2xl z-40 flex items-center gap-1 sm:gap-2 px-2 py-1.5 border border-gray-600 transition-all duration-300 ease-out ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-16 opacity-0 pointer-events-none'
      }`}
    >
      <div className="flex items-center gap-2 pr-1 sm:pr-2">
        <span className="flex items-center justify-center h-7 w-7 bg-red-600 text-white rounded-full text-xs font-bold flex-shrink-0">
          {isLoading ? ICONS.spinner : selectedCount}
        </span>
        <span className="font-medium text-sm text-gray-200 hidden sm:inline whitespace-nowrap">
          {selectedCount > 1 ? 'elementos seleccionados' : 'elemento seleccionado'}
        </span>
      </div>

      <div className="h-6 w-px bg-gray-600 self-center"></div>

      {onReanalyze && (
        <button onClick={onReanalyze} disabled={isLoading} title="Reanalizar" className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/10 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-wait">
          {React.cloneElement(ICONS.analyze, { className: 'h-5 w-5' })}
          <span className="hidden md:inline">Reanalizar</span>
        </button>
      )}
      {onEdit && (
        <button onClick={onEdit} disabled={isLoading} title="Editar" className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/10 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-wait">
          {React.cloneElement(ICONS.edit, { className: 'h-5 w-5' })}
          <span className="hidden md:inline">Editar</span>
        </button>
      )}
      {onRestore && (
         <button onClick={onRestore} disabled={isLoading} title="Restaurar" className="flex items-center gap-2 p-2 rounded-lg text-green-400 hover:bg-green-500 hover:text-white transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-wait">
            {React.cloneElement(ICONS.restore, { className: 'h-5 w-5' })}
            <span className="hidden md:inline">Restaurar</span>
        </button>
      )}
      
      <button onClick={onDelete} disabled={isLoading} title="Eliminar" className="flex items-center gap-2 p-2 rounded-lg text-red-400 hover:bg-red-500 hover:text-white transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-wait">
        {React.cloneElement(ICONS.delete, { className: 'h-5 w-5' })}
        <span className="hidden md:inline">Eliminar</span>
      </button>

      <div className="h-6 w-px bg-gray-600 self-center"></div>
      
      <button onClick={onClear} disabled={isLoading} title="Limpiar selección" className="p-2 rounded-full hover:bg-white/10 transition-colors disabled:opacity-50">
        {React.cloneElement(ICONS.close, { className: 'h-5 w-5' })}
      </button>
    </div>
  );
};

export default BulkActionBar;