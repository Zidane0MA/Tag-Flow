
import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import GalleryPage from './pages/GalleryPage';
import AdminPage from './pages/AdminPage';
import TrashPage from './pages/TrashPage';
import { CursorDataProvider } from './hooks/useCursorData';
import { AdminProvider } from './hooks/useAdminData';
import VideoPlayerPage from './pages/VideoPlayerPage';
import CreatorPage from './pages/CreatorPage';
import SubscriptionPage from './pages/SubscriptionPage';
import IconsShowcase from './pages/IconsShowcase';
import { CursorTestPage } from './pages/CursorTestPage';


const App: React.FC = () => {
  return (
    <AdminProvider>
      <HashRouter>
        <Routes>
          {/* Player route does not use the main layout for a fullscreen experience */}
          <Route path="/post/:postId/player" element={<VideoPlayerPage />} />

          {/* All other routes use the main Layout component */}
          <Route path="/*" element={
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/gallery" replace />} />
                <Route path="/gallery" element={
                  <CursorDataProvider>
                    <GalleryPage />
                  </CursorDataProvider>
                } />
                  <Route path="/admin/*" element={<AdminPage />} />
                  <Route path="/trash" element={<TrashPage />} />
                  
                  {/* Creator & Subscription Pages */}
                  <Route path="/creator/:creatorName" element={<CreatorPage />} />
                  <Route path="/creator/:creatorName/:platform" element={<CreatorPage />} />
                  <Route path="/creator/:creatorName/:platform/:subscriptionId" element={<CreatorPage />} />
                  <Route path="/subscription/:type/:id" element={<SubscriptionPage />} />
                  <Route path="/subscription/:type/:id/:list" element={<SubscriptionPage />} />

                  {/* Icons Showcase */}
                  <Route path="/icons" element={<IconsShowcase />} />

                  {/* Cursor Test Page */}
                  <Route path="/cursor-test" element={<CursorTestPage />} />

                  {/* Fallback for any other route to redirect to gallery */}
                  <Route path="*" element={<Navigate to="/gallery" replace />} />
                </Routes>
              </Layout>
            } />
          </Routes>
        </HashRouter>
      </AdminProvider>
  );
};

export default App;
