/**
 * Sidebar navigation component.
 *
 * Renders the full left-hand navigation for the SaaS dashboard shell.
 * Active route is highlighted automatically via React Router's useLocation.
 */

import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  TrendingUp,
  Bot,
  ShoppingCart,
  BarChart3,
  Clock,
  Settings,
  ChefHat,
  type LucideIcon,
} from 'lucide-react';

interface NavItem {
  label: string;
  path: string;
  Icon: LucideIcon;
  disabled?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard',       path: '/',               Icon: LayoutDashboard },
  { label: 'Inventory',       path: '/inventory',      Icon: Package,        disabled: true },
  { label: 'Sales',           path: '/sales',          Icon: TrendingUp,     disabled: true },
  { label: 'AI Assistant',    path: '/ai',             Icon: Bot },
  { label: 'Procurement',     path: '/procurement',    Icon: ShoppingCart,   disabled: true },
  { label: 'Reports',         path: '/reports',        Icon: BarChart3,      disabled: true },
  { label: 'Automation Logs', path: '/automation',     Icon: Clock,          disabled: true },
  { label: 'Settings',        path: '/settings',       Icon: Settings,       disabled: true },
];

export function Sidebar() {
  const { pathname } = useLocation();

  return (
    <aside className="flex flex-col w-64 min-h-screen bg-slate-900 text-slate-100 shrink-0">
      {/* ── Brand ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 h-16 border-b border-slate-700/60">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600">
          <ChefHat className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold leading-none text-white">RestaurantOps</p>
          <p className="text-[11px] text-slate-400 leading-none mt-0.5">AI Platform</p>
        </div>
      </div>

      {/* ── Navigation ────────────────────────────────────────── */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ label, path, Icon, disabled }) => {
          const isActive = path === '/'
            ? pathname === '/'
            : pathname.startsWith(path);

          if (disabled) {
            return (
              <div
                key={path}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-500 cursor-not-allowed select-none"
                title="Coming in a future stage"
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-sm">{label}</span>
                <span className="ml-auto text-[10px] bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded font-medium">
                  Soon
                </span>
              </div>
            );
          }

          return (
            <NavLink
              key={path}
              to={path}
              className={[
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-blue-600 text-white font-medium'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white',
              ].join(' ')}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </NavLink>
          );
        })}
      </nav>

      {/* ── Footer ────────────────────────────────────────────── */}
      <div className="px-4 py-4 border-t border-slate-700/60">
        <p className="text-[11px] text-slate-500 text-center">
          Stage 1 — Architecture MVP
        </p>
      </div>
    </aside>
  );
}
