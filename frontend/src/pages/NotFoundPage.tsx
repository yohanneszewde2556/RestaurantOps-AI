/**
 * 404 Not Found page.
 */

import { useNavigate } from 'react-router-dom';
import { Home, AlertCircle } from 'lucide-react';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-100 mb-6">
        <AlertCircle className="w-8 h-8 text-slate-400" />
      </div>
      <h1 className="text-3xl font-bold text-slate-800">404</h1>
      <p className="text-slate-500 mt-2 mb-6">
        This page doesn't exist yet — it may be coming in a future stage.
      </p>
      <button
        onClick={() => navigate('/')}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
      >
        <Home className="w-4 h-4" />
        Back to Dashboard
      </button>
    </div>
  );
}
