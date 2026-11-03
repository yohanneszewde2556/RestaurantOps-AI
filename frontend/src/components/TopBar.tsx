/**
 * TopBar — Application top navigation bar.
 *
 * Displays the current page title and system status indicators.
 */

import { Bell, Activity } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { healthApi } from '../services/api';

interface TopBarProps {
  title: string;
}

export function TopBar({ title }: TopBarProps) {
  const { data, loading, error } = useApi(() => healthApi.check());

  const statusColor = loading
    ? 'bg-yellow-400'
    : error
      ? 'bg-red-500'
      : 'bg-emerald-500';

  const statusLabel = loading
    ? 'Connecting…'
    : error
      ? 'Backend offline'
      : `v${data?.version ?? '—'} · Connected`;

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-white border-b border-slate-200 shrink-0">
      {/* ── Page title ────────────────────────────────────────── */}
      <h1 className="text-lg font-semibold text-slate-800 tracking-tight">
        {title}
      </h1>

      {/* ── Right controls ────────────────────────────────────── */}
      <div className="flex items-center gap-4">
        {/* API status badge */}
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Activity className="w-3.5 h-3.5" />
          <span
            className={[
              'inline-block w-2 h-2 rounded-full',
              statusColor,
            ].join(' ')}
          />
          <span>{statusLabel}</span>
        </div>

        {/* Notification bell (placeholder) */}
        <button
          className="relative p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-5 h-5" />
        </button>

        {/* User avatar (placeholder) */}
        <div
          className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-semibold cursor-pointer select-none"
          title="Manager"
        >
          M
        </div>
      </div>
    </header>
  );
}
