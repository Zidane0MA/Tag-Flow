/**
 * Hook para manejar scroll infinito
 * Detecta cuando el usuario se acerca al final de la página y ejecuta callback
 */

import { useEffect, useCallback, useRef } from 'react';

interface UseInfiniteScrollOptions {
  threshold?: number; // Distancia desde abajo para disparar (en px)
  enabled?: boolean;  // Si el hook está habilitado
}

export const useInfiniteScroll = (
  callback: () => void,
  options: UseInfiniteScrollOptions = {}
) => {
  const { threshold = 200, enabled = true } = options;
  const callbackRef = useRef(callback);

  // Mantener referencia actualizada del callback
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const handleScroll = useCallback(() => {
    if (!enabled) return;

    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = document.documentElement.clientHeight;
    
    const distanceFromBottom = scrollHeight - (scrollTop + clientHeight);

    // Verificar si estamos cerca del final
    if (distanceFromBottom <= threshold) {
      console.log('🎯 Infinite scroll triggered!', { distanceFromBottom, threshold });
      callbackRef.current();
    }
  }, [enabled, threshold]);

  useEffect(() => {
    if (!enabled) return;

    // Throttle scroll events para mejor rendimiento
    let ticking = false;
    
    const throttledScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          handleScroll();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', throttledScroll, { passive: true });
    window.addEventListener('resize', throttledScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', throttledScroll);
      window.removeEventListener('resize', throttledScroll);
    };
  }, [handleScroll, enabled]);
};

export default useInfiniteScroll;