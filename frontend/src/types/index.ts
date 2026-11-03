/**
 * Shared TypeScript types for RestaurantOps AI.
 * These mirror the Pydantic schemas on the backend.
 */

// ── API Response envelope ──────────────────────────────────────────
export interface ApiSuccess<T> {
  success: true;
  data: T;
  message: string | null;
}

export interface ApiError {
  success: false;
  error: string;
  detail: string | null;
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError;

// ── Health ─────────────────────────────────────────────────────────
export interface HealthData {
  status: string;
  app: string;
  version: string;
}

// ── Navigation ─────────────────────────────────────────────────────
export interface NavItem {
  label: string;
  path: string;
  icon: string; // Lucide icon name
  badge?: number;
  disabled?: boolean;
}

// ── Ingredient / Inventory ─────────────────────────────────────────
export type IngredientUnit = 'kg' | 'g' | 'L' | 'ml' | 'pcs' | 'box' | 'bag';
export type StockStatus = 'ok' | 'low' | 'critical' | 'expired';

export interface Ingredient {
  id: number;
  name: string;
  sku: string;
  category: string;
  unit: IngredientUnit;
  quantity: number;
  min_quantity: number;
  cost_per_unit: number;
  expiry_date: string | null;
  stock_status: StockStatus;
  created_at: string;
  updated_at: string;
}

// ── Sales ──────────────────────────────────────────────────────────
export interface SaleItem {
  ingredient_id: number;
  ingredient_name: string;
  quantity_used: number;
}

export interface Sale {
  id: number;
  menu_item: string;
  quantity_sold: number;
  sale_date: string;
  items: SaleItem[];
}

// ── Procurement ────────────────────────────────────────────────────
export type ProcurementStatus = 'pending' | 'approved' | 'ordered' | 'received' | 'cancelled';

export interface ProcurementItem {
  ingredient_id: number;
  ingredient_name: string;
  quantity_requested: number;
  unit: IngredientUnit;
  estimated_cost: number;
}

export interface ProcurementOrder {
  id: number;
  status: ProcurementStatus;
  created_at: string;
  notes: string | null;
  total_cost: number;
  items: ProcurementItem[];
}

// ── AI Chat ────────────────────────────────────────────────────────
export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
}

// ── Automation ─────────────────────────────────────────────────────
export type AutomationLogLevel = 'info' | 'warning' | 'error';

export interface AutomationLog {
  id: number;
  job_name: string;
  level: AutomationLogLevel;
  message: string;
  created_at: string;
}


// ── Dashboard Summary ──────────────────────────────────────────────
export interface DashboardSummaryData {
  total_ingredients: number;
  total_active_menu_items: number;
  total_inventory_value: number;
  low_stock_count: number;
  expiring_soon_count: number;
  today_sales_revenue: number;
  today_sales_count: number;
  recent_transactions: Array<{
    id: number;
    ingredient_id: number;
    transaction_type: string;
    quantity: number;
    notes: string | null;
    created_at: string;
  }>;
  recent_sales: Array<{
    id: number;
    total_amount: number;
    sold_at: string;
    created_at: string;
  }>;
}

// ── Analytics Types ────────────────────────────────────────────────
export interface PeriodConsumptionSummary {
  today: number;
  last_7_days: number;
  last_30_days: number;
}

export interface TopConsumedIngredient {
  ingredient_id: number;
  name: string;
  sku: string;
  category: string;
  unit: string;
  total_consumed: number;
  avg_daily_consumption: number;
  total_cost: number;
}

export interface DailyIngredientConsumption {
  name: string;
  quantity: number;
  unit: string;
}

export interface DailyConsumptionTrend {
  date: string;
  total_quantity: number;
  transaction_count: number;
  top_ingredients: DailyIngredientConsumption[];
}

export interface ConsumptionAnalyticsData {
  date_range: {
    start_date: string;
    end_date: string;
    days_in_period: number;
  };
  summary: PeriodConsumptionSummary;
  top_consumed: TopConsumedIngredient[];
  daily_trends: DailyConsumptionTrend[];
}

export interface PopularMenuItem {
  menu_item_id: number;
  name: string;
  selling_price: number;
  total_quantity_sold: number;
  total_revenue: number;
  order_count: number;
  revenue_percentage: number;
}

export interface PopularItemsData {
  date_range: {
    start_date: string | null;
    end_date: string | null;
  };
  total_items_sold: number;
  total_revenue: number;
  items: PopularMenuItem[];
}

export interface RecipeCostItem {
  ingredient_id: number;
  ingredient_name: string;
  sku: string;
  unit: string;
  quantity_required: number;
  cost_per_unit: number;
  ingredient_cost: number;
}

export interface MenuItemFoodCost {
  menu_item_id: number;
  name: string;
  selling_price: number;
  is_active: boolean;
  has_recipe: boolean;
  recipe_item_count: number;
  total_cost: number;
  food_cost_percentage: number | null;
  gross_contribution: number;
  gross_margin_percentage: number | null;
  recipe_items: RecipeCostItem[];
  notes: string | null;
}

export interface FoodCostAnalyticsData {
  total_menu_items: number;
  items_with_recipes: number;
  average_food_cost_percentage: number | null;
  overall_food_cost_tier: string;
  items: MenuItemFoodCost[];
  assumptions_and_limitations: string[];
}


// ── Agent Types ────────────────────────────────────────────────────
export interface ToolExecutionMeta {
  tool_name: string;
  arguments: Record<string, unknown>;
  result_summary: Record<string, unknown>;
}

export interface AgentChatResponseData {
  conversation_id: string;
  response: string;
  tools_called: ToolExecutionMeta[];
  is_configured: boolean;
  timestamp: string;
  error?: boolean;
}

export interface AgentStatusData {
  is_configured: boolean;
  model: string;
  provider: string;
  status: string;
  message: string;
}
