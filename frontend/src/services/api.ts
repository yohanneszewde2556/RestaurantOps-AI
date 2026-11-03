/**
 * API service layer.
 *
 * All backend communication goes through this module.
 * - Uses the Vite proxy (/api → http://localhost:8000) in development.
 * - Returns typed ApiResponse<T> so callers can discriminate success/error.
 */

import type { ApiResponse, HealthData } from '../types';

const BASE_URL = '/api/v1';

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    const json = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: json.error ?? 'Request failed',
        detail: json.detail ?? `HTTP ${response.status}`,
      };
    }

    return json as ApiResponse<T>;
  } catch (error) {
    return {
      success: false,
      error: 'Network error',
      detail: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// ── Health ─────────────────────────────────────────────────────────
export const healthApi = {
  check: () => request<HealthData>('/health'),
};

import type {
  DashboardSummaryData,
  ConsumptionAnalyticsData,
  PopularItemsData,
  FoodCostAnalyticsData,
} from '../types';

// ── Dashboard ──────────────────────────────────────────────────────
export const dashboardApi = {
  getSummary: () => request<DashboardSummaryData>('/dashboard/summary'),
};

// ── Analytics ──────────────────────────────────────────────────────
export const analyticsApi = {
  getConsumption: (params?: { start_date?: string; end_date?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.start_date) q.append('start_date', params.start_date);
    if (params?.end_date) q.append('end_date', params.end_date);
    if (params?.limit) q.append('limit', params.limit.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return request<ConsumptionAnalyticsData>(`/analytics/consumption${queryStr}`);
  },

  getPopularItems: (params?: { start_date?: string; end_date?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.start_date) q.append('start_date', params.start_date);
    if (params?.end_date) q.append('end_date', params.end_date);
    if (params?.limit) q.append('limit', params.limit.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return request<PopularItemsData>(`/analytics/popular-items${queryStr}`);
  },

  getFoodCost: () => request<FoodCostAnalyticsData>('/analytics/food-cost'),
};

import type {
  AgentChatResponseData,
  AgentStatusData,
} from '../types';

// ── AI Agent ───────────────────────────────────────────────────────
export const agentApi = {
  getStatus: () => request<AgentStatusData>('/agent/status'),

  chat: (payload: {
    message: string;
    conversation_id?: string;
    history?: Array<{ role: string; content: string }>;
  }) =>
    request<AgentChatResponseData>('/agent/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
