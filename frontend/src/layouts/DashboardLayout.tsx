/**
 * DashboardLayout — The main shell layout.
 *
 * Composes Sidebar + TopBar + scrollable content area.
 * All authenticated pages are wrapped in this layout.
 */

import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';

const PAGE_TITLES: Record<string, string> = {
  '/':           'Dashboard',
  '/inventory':  'Inventory',
  '/sales':      'Sales',
  '/ai':         'AI Assistant',
  '/procurement':'Procurement',
  '/reports':    'Reports',
  '/automation': 'Automation Logs',
  '/settings':   'Settings',
};

export function DashboardLayout() {
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? 'RestaurantOps AI';

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar title={title} />

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
