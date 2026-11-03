/**
 * Dashboard Page — Operational Overview & Consumption Analytics
 *
 * Stage 4: Integrates real-time backend analytics:
 * - Ingredient consumption volume and daily trends
 * - Popular menu item sales and revenue contributions
 * - Recipe food cost calculations and profitability margins
 * - High-level operational inventory KPIs
 */

import { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  DollarSign,
  UtensilsCrossed,
  Layers,
  ArrowUpRight,
  RefreshCw,
  Calendar,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

import { dashboardApi, analyticsApi } from '../services/api';
import type {
  DashboardSummaryData,
  ConsumptionAnalyticsData,
  PopularItemsData,
  FoodCostAnalyticsData,
} from '../types';
import { formatCurrency } from '../utils/format';

// Color Palette for SaaS Analytics
const COLORS = ['#2563EB', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#64748B'];

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  Icon: React.ElementType;
  iconBg: string;
  badge?: { text: string; color: string };
}

function StatCard({ label, value, sub, Icon, iconBg, badge }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-start gap-4 shadow-sm hover:shadow-md transition-shadow">
      <div className={`p-3 rounded-xl ${iconBg} shrink-0`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
          {badge && (
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${badge.color}`}>
              {badge.text}
            </span>
          )}
        </div>
        <p className="text-2xl font-bold text-slate-800 mt-1 truncate">{value}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  );
}

export function DashboardPage() {
  const [periodDays, setPeriodDays] = useState<number>(30);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<DashboardSummaryData | null>(null);
  const [consumption, setConsumption] = useState<ConsumptionAnalyticsData | null>(null);
  const [popular, setPopular] = useState<PopularItemsData | null>(null);
  const [foodCost, setFoodCost] = useState<FoodCostAnalyticsData | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const endDate = new Date().toISOString();
    const startDate = new Date(Date.now() - periodDays * 24 * 60 * 60 * 1000).toISOString();

    try {
      const [summaryRes, consumptionRes, popularRes, foodCostRes] = await Promise.all([
        dashboardApi.getSummary(),
        analyticsApi.getConsumption({ start_date: startDate, end_date: endDate, limit: 8 }),
        analyticsApi.getPopularItems({ start_date: startDate, end_date: endDate, limit: 6 }),
        analyticsApi.getFoodCost(),
      ]);

      if (!summaryRes.success) throw new Error(summaryRes.error || 'Failed to load summary');
      if (!consumptionRes.success) throw new Error(consumptionRes.error || 'Failed to load consumption analytics');
      if (!popularRes.success) throw new Error(popularRes.error || 'Failed to load popular items');
      if (!foodCostRes.success) throw new Error(foodCostRes.error || 'Failed to load food cost metrics');

      setSummary(summaryRes.data);
      setConsumption(consumptionRes.data);
      setPopular(popularRes.data);
      setFoodCost(foodCostRes.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching analytics data');
    } finally {
      setLoading(false);
    }
  }, [periodDays]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Transform daily trend data for Recharts
  const trendChartData = consumption?.daily_trends.map((item) => ({
    date: item.date.slice(5), // MM-DD
    fullDate: item.date,
    quantity: item.total_quantity,
    transactions: item.transaction_count,
  })) ?? [];

  // Transform top consumed ingredients for Recharts
  const topIngredientsData = consumption?.top_consumed.map((item) => ({
    name: item.name.length > 15 ? `${item.name.slice(0, 15)}…` : item.name,
    fullName: item.name,
    quantity: item.total_consumed,
    cost: item.total_cost,
    unit: item.unit,
  })) ?? [];

  // Transform popular items for Bar & Pie charts
  const popularChartData = popular?.items.map((item) => ({
    name: item.name.length > 16 ? `${item.name.slice(0, 16)}…` : item.name,
    fullName: item.name,
    quantity: item.total_quantity_sold,
    revenue: item.total_revenue,
    revenuePercentage: item.revenue_percentage,
  })) ?? [];

  // Transform food cost comparison
  const foodCostChartData = foodCost?.items.map((item) => ({
    name: item.name.length > 14 ? `${item.name.slice(0, 14)}…` : item.name,
    fullName: item.name,
    price: item.selling_price,
    cost: item.total_cost,
    foodCostPct: item.food_cost_percentage ?? 0,
    grossMargin: item.gross_contribution,
  })) ?? [];

  return (
    <div className="space-y-6">

      {/* ── Page Header & Controls ────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Operations & Analytics</h2>
          <p className="text-sm text-slate-500 mt-1">
            Real-time kitchen consumption velocity, item profitability, and sales performance.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {/* Time range selector */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-medium">
            <button
              onClick={() => setPeriodDays(7)}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                periodDays === 7 ? 'bg-white text-blue-600 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => setPeriodDays(30)}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                periodDays === 30 ? 'bg-white text-blue-600 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              30 Days
            </button>
            <button
              onClick={() => setPeriodDays(90)}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                periodDays === 90 ? 'bg-white text-blue-600 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              90 Days
            </button>
          </div>

          {/* Refresh button */}
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 shadow-sm disabled:opacity-50 transition-colors"
            title="Refresh analytics data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : 'text-slate-500'}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* ── Error Banner ─────────────────────────────────────────── */}
      {error && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4 text-red-800">
          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold">Failed to load analytics</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
          <button
            onClick={fetchData}
            className="text-xs font-semibold text-red-700 underline hover:text-red-900"
          >
            Try Again
          </button>
        </div>
      )}

      {/* ── KPI Stat Cards ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Inventory Value"
          value={summary ? formatCurrency(summary.total_inventory_value) : '—'}
          sub={summary ? `${summary.total_ingredients} ingredients in catalog` : 'Loading…'}
          Icon={DollarSign}
          iconBg="bg-blue-600"
        />

        <StatCard
          label="Total Revenue (Period)"
          value={popular ? formatCurrency(popular.total_revenue) : '—'}
          sub={popular ? `${popular.total_items_sold} dishes sold` : 'Loading…'}
          Icon={TrendingUp}
          iconBg="bg-emerald-600"
          badge={{ text: `${periodDays}d`, color: 'bg-emerald-100 text-emerald-800' }}
        />

        <StatCard
          label="Low Stock Alerts"
          value={summary?.low_stock_count ?? 0}
          sub={
            summary?.low_stock_count && summary.low_stock_count > 0
              ? 'Items at or below minimum threshold'
              : 'All pantry stocks healthy'
          }
          Icon={AlertTriangle}
          iconBg={summary?.low_stock_count && summary.low_stock_count > 0 ? 'bg-amber-500' : 'bg-slate-500'}
          badge={
            summary?.low_stock_count && summary.low_stock_count > 0
              ? { text: 'Action Needed', color: 'bg-amber-100 text-amber-800' }
              : undefined
          }
        />

        <StatCard
          label="Average Food Cost"
          value={
            foodCost?.average_food_cost_percentage
              ? `${foodCost.average_food_cost_percentage.toFixed(1)}%`
              : '—'
          }
          sub={foodCost?.overall_food_cost_tier ?? 'Calculating margins…'}
          Icon={UtensilsCrossed}
          iconBg="bg-violet-600"
          badge={{ text: 'Target <30%', color: 'bg-violet-100 text-violet-800' }}
        />
      </div>

      {/* ── Consumption & Velocity Section ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Daily Consumption Timeline */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-800">Ingredient Consumption Timeline</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Aggregated daily ingredient depletion volume across all menu sales.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
              <Calendar className="w-3.5 h-3.5 text-blue-500" />
              <span>{periodDays} Day Trend</span>
            </div>
          </div>

          <div className="h-64 w-full">
            {loading ? (
              <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg animate-pulse">
                <p className="text-xs text-slate-400">Loading consumption trends…</p>
              </div>
            ) : trendChartData.length === 0 ? (
              <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg border border-dashed border-slate-200">
                <p className="text-xs text-slate-400">No ingredient consumption recorded in this date range.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorConsumption" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563EB" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748B' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
                  <Tooltip
                    formatter={(val) => [`${Number(val).toFixed(2)} units`, 'Consumed Volume']}
                    labelFormatter={(label) => `Date: ${label}`}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '12px' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="quantity"
                    stroke="#2563EB"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorConsumption)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Quick period summary metrics */}
          <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-slate-100 text-center">
            <div className="bg-slate-50 rounded-lg p-2.5">
              <p className="text-[11px] text-slate-500 font-medium">Today's Consumption</p>
              <p className="text-sm font-bold text-slate-800 mt-0.5">
                {consumption?.summary.today ? `${Number(consumption.summary.today).toFixed(2)} units` : '0.00'}
              </p>
            </div>
            <div className="bg-slate-50 rounded-lg p-2.5">
              <p className="text-[11px] text-slate-500 font-medium">Last 7 Days</p>
              <p className="text-sm font-bold text-slate-800 mt-0.5">
                {consumption?.summary.last_7_days ? `${Number(consumption.summary.last_7_days).toFixed(2)} units` : '0.00'}
              </p>
            </div>
            <div className="bg-slate-50 rounded-lg p-2.5">
              <p className="text-[11px] text-slate-500 font-medium">Last 30 Days</p>
              <p className="text-sm font-bold text-slate-800 mt-0.5">
                {consumption?.summary.last_30_days ? `${Number(consumption.summary.last_30_days).toFixed(2)} units` : '0.00'}
              </p>
            </div>
          </div>
        </div>

        {/* Top Consumed Ingredients Bar Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-800">Top Consumed Ingredients</h3>
              <p className="text-xs text-slate-500 mt-0.5">Ranked by volume depleted.</p>
            </div>
            <Layers className="w-4 h-4 text-slate-400" />
          </div>

          <div className="h-64 w-full flex-1">
            {loading ? (
              <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg animate-pulse">
                <p className="text-xs text-slate-400">Loading top ingredients…</p>
              </div>
            ) : topIngredientsData.length === 0 ? (
              <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg border border-dashed border-slate-200">
                <p className="text-xs text-slate-400">No ingredient depletion recorded.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topIngredientsData} layout="vertical" margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
                  <XAxis type="number" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#334155' }} width={85} />
                  <Tooltip
                    formatter={(val, _name, item) => [
                      `${Number(val).toFixed(2)} ${item.payload.unit} (Est. ${formatCurrency(item.payload.cost)})`,
                      'Consumed',
                    ]}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '12px' }}
                  />
                  <Bar dataKey="quantity" fill="#3B82F6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* ── Sales & Menu Performance ──────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Best-Selling Menu Items */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-800">Best-Selling Menu Items</h3>
              <p className="text-xs text-slate-500 mt-0.5">Dishes ordered and total revenue contribution.</p>
            </div>
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-md">
              Top Performers
            </span>
          </div>

          <div className="h-64 w-full">
            {loading ? (
              <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg animate-pulse">
                <p className="text-xs text-slate-400">Loading popular dishes…</p>
              </div>
            ) : popularChartData.length === 0 ? (
              <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg border border-dashed border-slate-200">
                <p className="text-xs text-slate-400">No menu sales recorded in this period.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={popularChartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis yAxisId="left" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: '#10B981' }} />
                  <Tooltip
                    formatter={(val, name) => [
                      name === 'quantity' ? `${val} orders` : formatCurrency(Number(val)),
                      name === 'quantity' ? 'Quantity Sold' : 'Total Revenue',
                    ]}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Bar yAxisId="left" dataKey="quantity" name="Quantity Sold" fill="#2563EB" radius={[4, 4, 0, 0]} />
                  <Bar yAxisId="right" dataKey="revenue" name="Revenue ($)" fill="#10B981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Revenue Contribution Share (Donut / Pie) */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-800">Revenue Contribution</h3>
              <p className="text-xs text-slate-500 mt-0.5">Share of sales by menu item.</p>
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-400" />
          </div>

          <div className="h-64 w-full flex-1">
            {loading ? (
              <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg animate-pulse">
                <p className="text-xs text-slate-400">Loading revenue share…</p>
              </div>
            ) : popularChartData.length === 0 ? (
              <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg border border-dashed border-slate-200">
                <p className="text-xs text-slate-400">No revenue data available.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={popularChartData}
                    dataKey="revenue"
                    nameKey="fullName"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                  >
                    {popularChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val) => [formatCurrency(Number(val)), 'Revenue Contribution']}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* ── Recipe Food Cost & Profitability ──────────────────────── */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-slate-800">Recipe Food Cost & Profitability Analysis</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Calculated bill-of-materials ingredient costs vs selling prices and gross margins.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-600 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-lg">
            <Info className="w-3.5 h-3.5 text-blue-600 shrink-0" />
            <span>Target: Food Cost &lt; 30% of Menu Price</span>
          </div>
        </div>

        {/* Cost vs Selling Price Bar Chart */}
        <div className="h-64 w-full">
          {loading ? (
            <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg animate-pulse">
              <p className="text-xs text-slate-400">Loading recipe cost comparison…</p>
            </div>
          ) : foodCostChartData.length === 0 ? (
            <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg border border-dashed border-slate-200">
              <p className="text-xs text-slate-400">No menu items configured.</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={foodCostChartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
                <Tooltip
                  formatter={(val, name) => [formatCurrency(Number(val)), name === 'cost' ? 'Recipe Cost' : 'Selling Price']}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="cost" name="Recipe Ingredient Cost" fill="#EF4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="price" name="Menu Selling Price" fill="#2563EB" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Profitability Detail Table */}
        <div className="overflow-x-auto pt-2">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50">
                <th className="py-2.5 px-3">Menu Item</th>
                <th className="py-2.5 px-3">Selling Price</th>
                <th className="py-2.5 px-3">Recipe Cost</th>
                <th className="py-2.5 px-3">Food Cost %</th>
                <th className="py-2.5 px-3">Gross Contribution</th>
                <th className="py-2.5 px-3">Margin Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {foodCost?.items.map((item) => {
                const fcPct = item.food_cost_percentage;
                let statusBadge = (
                  <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-medium text-[10px]">
                    No Recipe
                  </span>
                );
                if (fcPct !== null) {
                  if (fcPct <= 25) {
                    statusBadge = (
                      <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-bold text-[10px]">
                        High Profit (&le;25%)
                      </span>
                    );
                  } else if (fcPct <= 35) {
                    statusBadge = (
                      <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold text-[10px]">
                        Target (25-35%)
                      </span>
                    );
                  } else {
                    statusBadge = (
                      <span className="bg-red-100 text-red-800 px-2 py-0.5 rounded-full font-bold text-[10px]">
                        High Cost (&gt;35%)
                      </span>
                    );
                  }
                }

                return (
                  <tr key={item.menu_item_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-slate-900">{item.name}</td>
                    <td className="py-2.5 px-3">{formatCurrency(item.selling_price)}</td>
                    <td className="py-2.5 px-3">{formatCurrency(item.total_cost)}</td>
                    <td className="py-2.5 px-3 font-mono">
                      {fcPct !== null ? `${fcPct.toFixed(1)}%` : '—'}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-emerald-700">
                      {formatCurrency(item.gross_contribution)}
                      {item.gross_margin_percentage !== null && (
                        <span className="text-[10px] text-slate-400 font-normal ml-1">
                          ({item.gross_margin_percentage.toFixed(0)}%)
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3">{statusBadge}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Assumptions callout */}
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-[11px] text-slate-500 space-y-1">
          <p className="font-semibold text-slate-700">Methodology & Assumptions:</p>
          <ul className="list-disc list-inside space-y-0.5 text-slate-600">
            {foodCost?.assumptions_and_limitations.map((note, idx) => (
              <li key={idx}>{note}</li>
            ))}
          </ul>
        </div>
      </div>

    </div>
  );
}
