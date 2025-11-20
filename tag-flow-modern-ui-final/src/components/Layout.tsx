import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  // Desktop-first: open by default on large screens, closed on mobile
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth >= 1024);
  const location = useLocation();

  // Handle window resize to manage sidebar state
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        // Desktop: ensure sidebar is open by default
        setIsSidebarOpen(true);
      } else {
        // Mobile: close sidebar when switching to mobile view
        setIsSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Apply transform-gpu for rendering performance, but disable it on the gallery
  // and trash pages to prevent issues with `position: fixed` elements like the BulkActionBar.
  const applyTransform = !location.pathname.startsWith('/gallery') && !location.pathname.startsWith('/trash');

  return (
    <div className="flex h-screen bg-[#0f0f0f] overflow-hidden">
      {/* Backdrop for mobile sidebar overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
          aria-hidden="true"
        ></div>
      )}

      <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />
      
      <div className={`flex-1 overflow-y-auto lg:overflow-hidden lg:flex lg:flex-col transition-all duration-300 ease-in-out ${applyTransform ? 'transform-gpu' : ''}`}>
        {/* Mobile Header - Sticky will now work within this scrolling container */}
        <header className="lg:hidden flex items-center justify-between h-16 px-4 bg-[#212121]/80 backdrop-blur-sm flex-shrink-0 sticky top-0 z-20">
          <span className="font-bold text-xl text-white">Tag-Flow</span>
          <button 
            onClick={() => setIsSidebarOpen(true)} 
            className="text-gray-400 hover:text-white p-2"
            aria-label="Open sidebar"
          >
             <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7" />
            </svg>
          </button>
        </header>

        <main className="bg-[#0f0f0f] lg:flex-1 lg:overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;