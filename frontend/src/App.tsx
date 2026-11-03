/**
 * App.tsx — Route configuration.
 *
 * Uses React Router v6 with a single DashboardLayout wrapping all routes.
 * New pages are added here as they are built in future stages.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { DashboardPage } from './pages/DashboardPage';
import { AiAssistantPage } from './pages/AiAssistantPage';
import { NotFoundPage } from './pages/NotFoundPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="ai" element={<AiAssistantPage />} />
          {/* Future stage routes — add here as they are built: */}
          {/* <Route path="inventory" element={<InventoryPage />} /> */}
          {/* <Route path="sales" element={<SalesPage />} /> */}
          {/* <Route path="procurement" element={<ProcurementPage />} /> */}
          {/* <Route path="reports" element={<ReportsPage />} /> */}
          {/* <Route path="automation" element={<AutomationPage />} /> */}
          {/* <Route path="settings" element={<SettingsPage />} /> */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
