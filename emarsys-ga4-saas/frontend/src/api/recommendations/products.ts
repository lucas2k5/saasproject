import api from './axios';

// Função auxiliar para garantir o formato correto
const normalizeRecs = (items: any[]): RecommendationItem[] => {
  if (!Array.isArray(items)) return [];

  return items.map(item => {
    // Se o item já tiver a estrutura { product: ..., score: ... }, retorna ele mesmo
    if (item.product) {
      return item as RecommendationItem;
    }
    // Se o item for o produto direto (formato plano), embrulhamos ele
    // e assumimos um score fictício se não vier
    return {
      product: item,
      score: item.score || 0.95 // Score padrão se a API não mandar
    };
  });
};

// 1. Interface Leve (Lista)
export interface Product {
  id: string;
  external_id: string;
  name: string;
  price: number;
  description: string;
  image_url: string;
  category: string[] | string; // Pode vir como string no upload ou array do banco
  attributes: Record<string, any>;
}

// Interface para a nossa árvore de categorias
export interface CategoryNode {
  label: string;
  value: string;
  children: CategoryNode[];
}

// 2. Interface Pesada (Detalhe - inclui o JSON de atributos)
export interface ProductDetail extends Product {
  attributes: Record<string, any>;
  enriched_text?: string | null;
  purchase_cycle_type?: string | null;
  purchase_cycle_days?: number | null;
}

export interface RecommendationItem {
  product: Product;
  score: number;
}

export interface RecommendationResponse {
  cheaper: RecommendationItem[];
  equivalent: RecommendationItem[];
  expensive: RecommendationItem[];
}

export interface DashboardStats {
  products: { total: number; active: number };
  categories: number;
  channels: number;
  stores: number;
  customers: number;
  prices: number;
  stock_items: number;
  orders: number;
  order_items: number;
  offers: number;
  active_offers: number;
  ai_index: { total_vectors: number; status: string; percentage: number };
  tenant: { id: number; name: string };
}

export interface ProductPriceItem {
  channel_id: string;
  channel_name: string;
  store_id: string;
  store_name: string;
  price: number;
}

export interface ProductStockItem {
  channel_id: string;
  channel_name: string;
  store_id: string;
  store_name: string;
  quantity: number;
  available: boolean;
}

export interface ProductPricesStock {
  prices: ProductPriceItem[];
  stock: ProductStockItem[];
}

export interface RevenueActual {
  month: string;
  revenue: number;
  orders: number;
  customers: number;
}

export interface RevenueForecast {
  month: string;
  revenue: number;
}

export interface RevenueStats {
  actual: RevenueActual[];
  forecast: RevenueForecast[];
  summary: {
    current_month: string;
    current_month_revenue: number;
    current_month_orders: number;
    prev_month_revenue: number;
    avg_monthly_revenue_6m: number;
    forecast_next_90d: number;
    forecast_monthly_avg: number;
    customers_with_forecast: number;
  };
}

export const productService = {
  getCategoryTree: async (): Promise<CategoryNode[]> => {
    const response = await api.get('/products/categories/tree');
    return response.data;
  },

  // Busca lista simples (Grid)
  getProducts: async (
    skip: number = 0,
    limit: number = 100,
    search?: string,
    category?: string // <--- Novo filtro
  ): Promise<Product[]> => {

    // Monta a URL com os parâmetros
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());

    if (search) params.append('q', search);
    if (category) params.append('category', category); // Passa a categoria selecionada

    const response = await api.get(`/products/?${params.toString()}`);
    return response.data;
  },

  // busca de produtos
  searchProducts: async (query: string, limit: number = 20): Promise<Product[]> => {

    console.group("🔍 [DEBUG] Iniciando Busca");
    console.log("Query enviada:", query);

    try {
      const response = await api.post('/search/', {
        query: query,
        limit: limit
      });

      const data = response.data;
      console.log("Query enviada:", data.results);
      // CENÁRIO A: A API retorna { results: [ { product: {...}, score: ... } ] }
      // Precisamos extrair o objeto 'product' de dentro e mapear os campos
      if (data && Array.isArray(data.results)) {
        return data.results.map((item: any) => ({
          id: item.product.product_id, // Mapeia product_id -> id
          name: item.product.name,
          price: item.product.price,
          description: item.product.description || "", // Garante string
          category: Array.isArray(item.product.category)
            ? item.product.category[0] // Pega a primeira categoria se for lista
            : item.product.category,
          image_url: item.product.image_url,
          external_id: item.product.external_id
        }));
      }

      console.warn("Formato inesperado na busca:", data);
      return [];

    } catch (error) {
      console.error("Erro ao buscar produtos:", error);
      return [];
    }
  },

  // NOVO: Busca detalhe completo (Gaveta)
  getProductDetail: async (id: string): Promise<ProductDetail> => {
    const response = await api.get(`/products/${id}`);
    console.log('product detail', response.data)
    return response.data;
  },

  // Busca recomendações da IA
  getRecommendations: async (productId: string): Promise<RecommendationResponse> => {

    try {
      console.log(`🔍 [DEBUG] Buscando recomendações para: ${productId}`);
      const response = await api.get(`/recommend/${productId}`);

      // Validação de Segurança: Se não vier o formato esperado, retorna vazio para não quebrar o .map
      console.log('response:', response.data)
      const recs = response.data.recommendations || {};
      return {
        cheaper: normalizeRecs(recs.cheaper),
        equivalent: normalizeRecs(recs.similar),
        expensive: normalizeRecs(recs.expensive)
      };

    } catch (error) {
      console.error("❌ Erro ao buscar recomendações:", error);
      // Retorna objeto vazio seguro para evitar o erro "map of undefined"
      return { cheaper: [], equivalent: [], expensive: [] };
    }

  },

  getProductPricesStock: async (productId: string): Promise<ProductPricesStock> => {
    const response = await api.get(`/products/${productId}/prices-stock`);
    return response.data;
  },

  // Busca dados de receita (realizado + previsão)
  getRevenueStats: async (monthsBack = 12): Promise<RevenueStats> => {
    const response = await api.get(`/dashboards/stats/revenue?months_back=${monthsBack}`);
    return response.data;
  },

  // Busca dados para dashboard
  getDashboardStats: async (): Promise<DashboardStats> => {
    try {
      const response = await api.get('/dashboards/stats');
      console.log('stats:', response.data);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar estatísticas do dashboard:", error);
      throw error; // Repassa o erro para o componente tratar (loading/erro visual)
    }
  }
};
