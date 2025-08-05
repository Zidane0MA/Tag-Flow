import React from 'react';
import { Routes, Route } from 'react-router-dom';
import AdminLayout from '../components/admin/AdminLayout';
import AdminDashboard from './admin/AdminDashboard';
import OperationsPage from './admin/OperationsPage';
import ConfigPage from './admin/ConfigPage';
import CharactersPage from './admin/CharactersPage';

const AdminPage: React.FC = () => {
  return (
    <AdminLayout>
      <Routes>
        <Route index element={<AdminDashboard />} />
        <Route path="operations" element={<OperationsPage />} />
        <Route path="config" element={<ConfigPage />} />
        <Route path="characters" element={<CharactersPage />} />
      </Routes>
    </AdminLayout>
  );
};

export default AdminPage;
