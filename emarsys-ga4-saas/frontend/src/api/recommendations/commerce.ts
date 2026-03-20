import api from './axios';

// ------------------------------------------------------------------ #
// Types
// ------------------------------------------------------------------ #

export interface Paginated<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface Customer {
  id: string;
  customer_id: string;
  customer_add_id: string | null;
  name: string;
  document: string | null;
  customer_type: string | null;
  source_created_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  product_external_id: string;
  quantity: number;
  unit_price: number;
  discount_amount: number;
  tax_amount: number;
  net_price: number;
  is_promo: boolean;
}

export interface Order {
  order_id: string;
  customer_id: string | null;
  status: string;
  ordered_at: string;
  gross_value: number;
  discount_value: number;
  tax_value: number;
  net_value: number;
  items_count: number;
  items: OrderItem[];
}

export interface OfferProduct {
  product_external_id: string;
  product_name: string;
  base_price: number;
  promo_price: number;
  role: string;
}

export interface Offer {
  offer_id: string;
  name: string;
  type: string;
  mechanic_params: Record<string, any>;
  products: OfferProduct[];
  start_at: string;
  end_at: string;
  channel_ids: string[] | null;
  store_ids: string[] | null;
  audience_type: string;
  priority: number;
}

export interface CustomerLifecycleIndicators {
  recency_days: number | null;
  number_of_invoices: number | null;
  monetary_total: number | null;
  avg_ticket: number | null;
  ticket_trend: number | null;
  purchase_velocity_trend: number | null;
  avg_days_between: number | null;
  purchase_regularity: number | null;
  distinct_articles: number | null;
  category_diversity: number | null;
  promo_ratio: number | null;
  return_rate: number | null;
  repeat_product_ratio: number | null;
  days_as_customer: number | null;
  p_alive: number | null;
  expected_transactions: number | null;
}

export interface CustomerLifecycle {
  customer_id: string;
  customer_ref: string;
  name: string;
  lifecycle: {
    segment: string;
    computed_at: string;
    indicators: CustomerLifecycleIndicators;
    preferences: {
      top_5_products: string[] | null;
      top_5_categories: string[] | null;
      preferred_channel: string | null;
    };
  } | null;
  summary: {
    total_orders: number;
    total_value: number;
    first_order_at: string | null;
    last_order_at: string | null;
    orders_90d: number;
    value_90d: number;
  } | null;
}

// ------------------------------------------------------------------ #
// Customers
// ------------------------------------------------------------------ #

export const customerService = {
  list: async (q?: string, customer_type?: string, skip = 0, limit = 50, lifecycle_segment?: string): Promise<Paginated<Customer>> => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (q) params.append('q', q);
    if (customer_type) params.append('customer_type', customer_type);
    if (lifecycle_segment) params.append('lifecycle_segment', lifecycle_segment);
    const r = await api.get(`/customers/?${params}`);
    return r.data;
  },
  getOrders: async (customer_ref: string, limit = 10): Promise<Order[]> => {
    const r = await api.get(`/orders/?customer_ref=${customer_ref}&limit=${limit}`);
    return r.data.items ?? r.data;
  },
  getLifecycle: async (customer_ref: string): Promise<CustomerLifecycle> => {
    const r = await api.get(`/lifecycle/customers/${customer_ref}`);
    return r.data;
  },
};

// ------------------------------------------------------------------ #
// Lifecycle
// ------------------------------------------------------------------ #

export interface LifecycleJob {
  id: string;
  status: 'queued' | 'running' | 'done' | 'failed';
  triggered_by: string;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  customers_processed: number | null;
  error_msg: string | null;
}

export const lifecycleService = {
  run: async (): Promise<{ started: boolean; job_id: string; status: string; message?: string }> => {
    const r = await api.post('/lifecycle/run');
    return r.data;
  },
  status: async (limit = 5): Promise<Paginated<LifecycleJob>> => {
    const r = await api.get(`/lifecycle/status?limit=${limit}`);
    return r.data;
  },
};

// ------------------------------------------------------------------ #
// Orders
// ------------------------------------------------------------------ #

export const orderService = {
  list: async (filters: {
    customer_ref?: string;
    status?: string;
    product_external_id?: string;
    skip?: number;
    limit?: number;
  }): Promise<Paginated<Order>> => {
    const params = new URLSearchParams({ skip: String(filters.skip ?? 0), limit: String(filters.limit ?? 50) });
    if (filters.customer_ref) params.append('customer_ref', filters.customer_ref);
    if (filters.status) params.append('status', filters.status);
    if (filters.product_external_id) params.append('product_external_id', filters.product_external_id);
    const r = await api.get(`/orders/?${params}`);
    return r.data;
  },
};

// ------------------------------------------------------------------ #
// Offers
// ------------------------------------------------------------------ #

export const offerService = {
  list: async (skip = 0, limit = 200): Promise<Offer[]> => {
    const r = await api.get(`/offers/?skip=${skip}&limit=${limit}`);
    return r.data;
  },
};

// ------------------------------------------------------------------ #
// Recommendations
// ------------------------------------------------------------------ #

export interface CustomerRecommendationItem {
  algorithm: string;
  rank: number;
  product_external_id: string;
  product_name: string;
  product_category: string | null;
  product_image_url: string | null;
  base_price: number;
  offer_price: number | null;
  offer_name: string | null;
  score: number;
}

export interface CustomerRecommendations {
  customer_id: string;
  customer_ref: string;
  name: string;
  recommendations: CustomerRecommendationItem[];
}

export interface RecommendationJob {
  id: string;
  status: 'queued' | 'running' | 'done' | 'failed';
  triggered_by: string;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  customers_processed: number | null;
  error_msg: string | null;
}

export const recommendationService = {
  getForCustomer: async (customer_ref: string, limit = 6): Promise<CustomerRecommendations> => {
    const r = await api.get(`/recommendations/${customer_ref}?limit=${limit}`);
    return r.data;
  },
  run: async (): Promise<{ started: boolean; job_id: string; status: string; message?: string }> => {
    const r = await api.post('/recommendations/run');
    return r.data;
  },
  status: async (limit = 5): Promise<Paginated<RecommendationJob>> => {
    const r = await api.get(`/recommendations/status?limit=${limit}`);
    return r.data;
  },
};

// ------------------------------------------------------------------ #
// Admin Cleanup
// ------------------------------------------------------------------ #

export interface PurgeResult {
  entity: string;
  total_deleted: number;
  details: Record<string, number>;
}

export const adminService = {
  purge: async (entity: string): Promise<PurgeResult> => {
    const r = await api.delete(`/admin/purge/${entity}`);
    return r.data;
  },
};

// ------------------------------------------------------------------ #
// Lifecycle Dashboard Stats
// ------------------------------------------------------------------ #

export interface SegmentCount { segment: string; count: number; }
export interface BucketCount { label: string; count: number; }
export interface SegmentTicket { segment: string; avg_ticket: number; }
export interface ProductCount { name: string; external_id: string; count: number; }
export interface CategoryCount { category: string; count: number; }
export interface ChannelCount { channel: string; count: number; }

export interface LifecycleDashboardStats {
  segment_distribution: SegmentCount[];
  recency_buckets: BucketCount[];
  p_alive_buckets: BucketCount[];
  avg_ticket_by_segment: SegmentTicket[];
  total_segmented: number;
  total_customers: number;
  frequency_buckets: BucketCount[];
  ticket_trend_buckets: BucketCount[];
  velocity_trend_buckets: BucketCount[];
  channel_distribution: ChannelCount[];
  category_diversity_buckets: BucketCount[];
  promo_ratio_buckets: BucketCount[];
  tenure_buckets: BucketCount[];
  top_recommended_products: ProductCount[];
  top_recommended_categories: CategoryCount[];
}

export const lifecycleDashboardService = {
  stats: async (): Promise<LifecycleDashboardStats> => {
    const r = await api.get('/dashboards/stats/lifecycle');
    return r.data;
  },
};
