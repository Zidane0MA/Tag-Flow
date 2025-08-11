import React, { useState } from 'react';
import { ICONS } from '../constants';
import Modal from './Modal';

interface PermanentDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  videoTitle: string;
  isMultiple?: boolean;
  count?: number;
}

const PermanentDeleteModal: React.FC<PermanentDeleteModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  videoTitle,
  isMultiple = false,
  count = 1
}) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    setIsDeleting(true);
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      console.error('Error in permanent delete:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const title = isMultiple ? 
    `Eliminar ${count} videos permanentemente` : 
    'Eliminar video permanentemente';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <div className="space-y-4">
        {/* Warning Icon */}
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
            {React.cloneElement(ICONS.delete, { className: 'h-8 w-8 text-red-600' })}
          </div>
        </div>

        {/* Main Warning Text */}
        <div className="text-center">
          <h3 className="text-lg font-semibold text-white mb-2">
            ⚠️ Esta acción no se puede deshacer
          </h3>
          <p className="text-gray-300">
            {isMultiple ? (
              <>Se eliminarán <strong>{count} videos</strong> permanentemente:</>
            ) : (
              <>Se eliminará <strong>"{videoTitle}"</strong> permanentemente:</>
            )}
          </p>
        </div>

        {/* Actions List */}
        <div className="bg-gray-800/50 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              {React.cloneElement(ICONS.check_plain, { className: 'h-3 w-3 text-white' })}
            </div>
            <div>
              <p className="text-white font-medium">Se eliminará de la base de datos</p>
              <p className="text-gray-400 text-sm">El video no aparecerá más en Tag-Flow</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              {React.cloneElement(ICONS.check_plain, { className: 'h-3 w-3 text-white' })}
            </div>
            <div>
              <p className="text-white font-medium">Se moverá a la papelera del sistema</p>
              <p className="text-gray-400 text-sm">El archivo se moverá a la Papelera/Trash del SO</p>
            </div>
          </div>
        </div>

        {/* 4K Apps Warning */}
        <div className="bg-yellow-900/30 border border-yellow-600/50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="w-5 h-5 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-black text-xs font-bold">!</span>
            </div>
            <div>
              <p className="text-yellow-300 font-medium mb-2">Información sobre apps 4K:</p>
              <ul className="text-yellow-100 text-sm space-y-1">
                <li>• Si las apps de 4K están <strong>abiertas</strong>: el video se perderá de sus bases de datos</li>
                <li>• Si las apps de 4K están <strong>cerradas</strong>: sus bases de datos no se verán afectadas</li>
                <li>• Si no estás seguro, <strong>cierra las apps de 4K</strong> antes de continuar</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-4 pt-4">
          <button 
            onClick={onClose}
            disabled={isDeleting}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Cancelar
          </button>
          <button 
            onClick={handleConfirm}
            disabled={isDeleting}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isDeleting && React.cloneElement(ICONS.spinner, { className: 'h-4 w-4 animate-spin' })}
            Eliminar Permanentemente
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default PermanentDeleteModal;