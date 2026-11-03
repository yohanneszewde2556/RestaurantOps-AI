/**
 * Utility helpers used across the application.
 */

/** Format a number as a currency string (USD by default). */
export function formatCurrency(
  amount: number,
  currency = 'USD',
  locale = 'en-US'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(amount);
}

/** Format an ISO date string as a human-readable date. */
export function formatDate(iso: string, locale = 'en-US'): string {
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(iso));
}

/** Format an ISO date string as a relative time label ("2 hours ago"). */
export function formatRelativeTime(iso: string): string {
  const delta = (Date.now() - new Date(iso).getTime()) / 1000;
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

  if (delta < 60) return rtf.format(-Math.round(delta), 'second');
  if (delta < 3600) return rtf.format(-Math.round(delta / 60), 'minute');
  if (delta < 86400) return rtf.format(-Math.round(delta / 3600), 'hour');
  return rtf.format(-Math.round(delta / 86400), 'day');
}

/** Clamp a value between min and max. */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/** Generate a unique ID string (for local-only use, e.g., chat messages). */
export function uid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}
