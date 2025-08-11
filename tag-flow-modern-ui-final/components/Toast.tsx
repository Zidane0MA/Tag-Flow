import React, { useEffect, useState } from 'react';
import { ICONS } from '../constants';

interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  isVisible: boolean;
  onClose: () => void;
  duration?: number;
}

const Toast: React.FC<ToastProps> = ({
  message,
  type,
  isVisible,
  onClose,
  duration = 5000
}) => {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        setIsExiting(true);
        setTimeout(onClose, 300); // Tiempo para la animación de salida
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  const getToastStyles = () => {
    switch (type) {
      case 'success':
        return 'bg-green-600 border-green-500 text-white';
      case 'error':
        return 'bg-red-600 border-red-500 text-white';
      case 'warning':
        return 'bg-yellow-600 border-yellow-500 text-white';
      case 'info':
      default:
        return 'bg-blue-600 border-blue-500 text-white';
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return React.cloneElement(ICONS.check_plain, { className: 'h-5 w-5' });
      case 'error':
        return React.cloneElement(ICONS.close, { className: 'h-5 w-5' });
      case 'warning':
        return React.cloneElement(ICONS.exclamation_simple, { className: 'h-5 w-5' });
      case 'info':
      default:
        return React.cloneElement(ICONS.status_pending, { className: 'h-5 w-5' });
    }
  };

  if (!isVisible && !isExiting) return null;

  return (
    <div
      className={`fixed top-4 right-4 z-50 max-w-sm w-full shadow-lg rounded-lg border-l-4 p-4 transition-all duration-300 ease-in-out ${
        getToastStyles()
      } ${
        isVisible && !isExiting
          ? 'translate-x-0 opacity-100'
          : 'translate-x-full opacity-0'
      }`}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getIcon()}
        </div>
        <div className="ml-3 w-0 flex-1">
          <p className="text-sm font-medium break-words">
            {message}
          </p>
        </div>
        <div className="ml-4 flex-shrink-0 flex">
          <button
            onClick={() => {
              setIsExiting(true);
              setTimeout(onClose, 300);
            }}
            className="inline-flex text-white/80 hover:text-white focus:outline-none focus:text-white transition-colors"
          >
            {React.cloneElement(ICONS.close, { className: 'h-4 w-4' })}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Toast;