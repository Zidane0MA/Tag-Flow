/**
 * Hook para manejar scroll infinito
 * Detecta cuando el usuario se acerca al final de la página y ejecuta callback
 */

import { useEffect, useRef } from 'react';

interface UseInfiniteScrollOptions {
  threshold?: number;
  enabled?: boolean;
}

export const useInfiniteScroll = (
  callback: () => void,
  options: UseInfiniteScrollOptions = {}
) => {
  const { threshold = 400, enabled = true } = options;
  const callbackRef = useRef(callback);
  const enabledRef = useRef(enabled);
  const lastTriggeredRef = useRef<number>(0);
  const isTriggering = useRef(false);

  // Always keep callback updated
  callbackRef.current = callback;
  enabledRef.current = enabled;

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const handleScroll = () => {
      if (!enabledRef.current || isTriggering.current) {
        return;
      }

      // Find the actual scrolling container
      // Priority: flex-1 container (mobile) > main element (desktop) > window
      const flexContainer = document.querySelector('.flex-1.overflow-y-auto');
      const mainElement = document.querySelector('main');
      
      let scrollTop: number;
      let scrollHeight: number;
      let clientHeight: number;
      
      if (flexContainer && flexContainer.scrollHeight > flexContainer.clientHeight) {
        // Mobile: flex container is scrollable
        scrollTop = flexContainer.scrollTop;
        scrollHeight = flexContainer.scrollHeight;
        clientHeight = flexContainer.clientHeight;
      } else if (mainElement && mainElement.scrollHeight > mainElement.clientHeight) {
        // Desktop: main element is scrollable
        scrollTop = mainElement.scrollTop;
        scrollHeight = mainElement.scrollHeight;
        clientHeight = mainElement.clientHeight;
      } else {
        // Fallback to window/document
        scrollTop = window.scrollY || document.documentElement.scrollTop;
        scrollHeight = document.documentElement.scrollHeight;
        clientHeight = window.innerHeight;
      }
      
      if (scrollHeight === 0 || clientHeight === 0) {
        return;
      }
      
      const distanceFromBottom = scrollHeight - (scrollTop + clientHeight);
      const now = Date.now();
      
      const timeSinceLastTrigger = now - lastTriggeredRef.current;
      const isNearBottom = distanceFromBottom <= threshold;
      const hasEnoughContent = scrollHeight > clientHeight * 1.3;
      const cooldownPassed = timeSinceLastTrigger > 1500;

      if (isNearBottom && hasEnoughContent && cooldownPassed) {
        isTriggering.current = true;
        lastTriggeredRef.current = now;
        
        callbackRef.current();
        
        setTimeout(() => {
          isTriggering.current = false;
        }, 1000);
      }
    };

    // Simple throttled scroll
    let ticking = false;
    const throttledScroll = () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(() => {
          handleScroll();
          ticking = false;
        });
      }
    };

    // Add event listeners to all possible scroll containers
    window.addEventListener('scroll', throttledScroll, { passive: true });
    
    // Listen to main element scroll (desktop)
    const mainElement = document.querySelector('main');
    if (mainElement) {
      mainElement.addEventListener('scroll', throttledScroll, { passive: true });
    }
    
    // Listen to flex container scroll (mobile)
    const flexContainer = document.querySelector('.flex-1.overflow-y-auto');
    if (flexContainer) {
      flexContainer.addEventListener('scroll', throttledScroll, { passive: true });
    }

    return () => {
      window.removeEventListener('scroll', throttledScroll);
      
      // Remove from main element
      const mainElement = document.querySelector('main');
      if (mainElement) {
        mainElement.removeEventListener('scroll', throttledScroll);
      }
      
      // Remove from flex container
      const flexContainer = document.querySelector('.flex-1.overflow-y-auto');
      if (flexContainer) {
        flexContainer.removeEventListener('scroll', throttledScroll);
      }
    };
  }, [enabled, threshold]); // Dependencies: enabled and threshold
};

export default useInfiniteScroll;