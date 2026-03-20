import { useEffect, useState } from 'react';
import {
  Activity,
  Database,
  Layers,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Barcode,
  Store,
  Radio,
  Users,
  Tag,
  Package,
  Percent,
  ShoppingCart,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

import { productService, type DashboardStats, type RevenueStats } from '../../api/recommendations/products';
import { TEXTS } from '@/constants/pt-br';

function formatBRL(value: number): string {
  return `R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

function formatMonth(month: string): string {
  const [y, m] = month.split('-');
  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  return `${months[parseInt(m, 10) - 1]}/${y.slice(2)}`;
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [revenue, setRevenue] = useState<RevenueStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const [dashData, revData] = await Promise.all([
        productService.getDashboardStats(),
        productService.getRevenueStats(12).catch(() => null),
      ]);
      setStats(dashData);
      setRevenue(revData);
    } catch (error) {
      console.error("Falha ao carregar dashboard", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStats(); }, []);

  // Monta dados do gráfico combinando actual + forecast
  const chartData = (() => {
    if (!revenue) return [];
    const data: { month: string; label: string; actual?: number; forecast?: number }[] = [];
    for (const a of revenue.actual) {
      data.push({ month: a.month, label: formatMonth(a.month), actual: a.revenue });
    }
    // Ponto de conexão: último mês real também tem forecast
    if (revenue.actual.length > 0 && revenue.forecast.length > 0) {
      const lastActual = data[data.length - 1];
      lastActual.forecast = lastActual.actual;
    }
    for (const f of revenue.forecast) {
      data.push({ month: f.month, label: formatMonth(f.month), forecast: f.revenue });
    }
    return data;
  })();

  // Variação mês atual vs anterior
  const monthVariation = (() => {
    if (!revenue?.summary) return null;
    const prev = revenue.summary.prev_month_revenue;
    if (prev <= 0) return null;
    return ((revenue.summary.current_month_revenue - prev) / prev) * 100;
  })();

  if (loading && !stats) return (
    <div className="flex h-full w-full items-center justify-center min-h-[50vh]">
      <Activity className="animate-spin h-8 w-8 text-primary" />
    </div>
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">

      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            {TEXTS.DASHBOARD.TITLE}
          </h1>
          <p className="text-muted-foreground">
            {TEXTS.DASHBOARD.SUBTITLE}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchStats}>
            <RefreshCw className="mr-2 h-4 w-4" />
            {TEXTS.COMMON.BTN_UPDATE}
          </Button>
        </div>
      </div>

      {/* SEÇÃO: RECEITA */}
      {revenue && revenue.actual.length > 0 && (
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Receita
        </h2>

        {/* KPIs de receita */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Mês Atual</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatBRL(revenue.summary.current_month_revenue)}</div>
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                {monthVariation !== null ? (
                  <>
                    {monthVariation >= 0 ? (
                      <TrendingUp className="h-3 w-3 text-emerald-500" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-red-500" />
                    )}
                    <span className={monthVariation >= 0 ? 'text-emerald-600' : 'text-red-600'}>
                      {monthVariation >= 0 ? '+' : ''}{monthVariation.toFixed(1)}%
                    </span>
                    {' '}vs mês anterior
                  </>
                ) : (
                  <>{revenue.summary.current_month_orders} pedidos</>
                )}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Mês Anterior</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatBRL(revenue.summary.prev_month_revenue)}</div>
              <p className="text-xs text-muted-foreground">Receita completa</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Média Mensal (6m)</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatBRL(revenue.summary.avg_monthly_revenue_6m)}</div>
              <p className="text-xs text-muted-foreground">Últimos 6 meses</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Previsão 90 dias</CardTitle>
              <TrendingUp className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-600">{formatBRL(revenue.summary.forecast_next_90d)}</div>
              <p className="text-xs text-muted-foreground">
                {revenue.summary.customers_with_forecast.toLocaleString()} clientes ativos (BG/NBD)
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Gráfico de receita */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Receita Realizada vs Previsão</CardTitle>
            <p className="text-xs text-muted-foreground">
              Linha sólida = realizado &bull; Linha tracejada = previsão BG/NBD (expected_transactions × ticket médio)
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={chartData} margin={{ left: 8, right: 8, top: 8, bottom: 4 }}>
                <defs>
                  <linearGradient id="gradActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(value: any, name: any) => [
                    formatBRL(Number(value)),
                    name === 'actual' ? 'Realizado' : 'Previsão',
                  ]}
                  labelFormatter={(label) => `Mês: ${label}`}
                />
                {/* Linha vertical separando realizado de previsão */}
                {revenue.actual.length > 0 && (
                  <ReferenceLine
                    x={formatMonth(revenue.actual[revenue.actual.length - 1].month)}
                    stroke="#94a3b8"
                    strokeDasharray="4 4"
                    label={{ value: 'Hoje', position: 'top', fontSize: 10, fill: '#94a3b8' }}
                  />
                )}
                <Area
                  type="monotone"
                  dataKey="actual"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  fill="url(#gradActual)"
                  connectNulls={false}
                  name="actual"
                  dot={{ r: 3, fill: '#3b82f6' }}
                />
                <Area
                  type="monotone"
                  dataKey="forecast"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  strokeDasharray="6 4"
                  fill="url(#gradForecast)"
                  connectNulls={false}
                  name="forecast"
                  dot={{ r: 3, fill: '#10b981' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
      )}

      {/* SEÇÃO: CATÁLOGO */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {TEXTS.DASHBOARD.SECTION_CATALOG}
        </h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_PRODUCTS}</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.products.total.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">{TEXTS.DASHBOARD.CARD_PRODUCTS_SUB}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_CATEGORIES}</CardTitle>
              <Layers className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.categories ?? 0}</div>
              <p className="text-xs text-muted-foreground">{TEXTS.DASHBOARD.CARD_CATEGORIES_SUB}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_CUSTOMERS}</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.customers?.toLocaleString() ?? 0}</div>
              <p className="text-xs text-muted-foreground">{TEXTS.DASHBOARD.CARD_CUSTOMERS_SUB}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_TENANT}</CardTitle>
              <Barcode className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold truncate text-sm font-mono">#{stats?.tenant.id}</div>
              <p className="text-xs text-muted-foreground">{TEXTS.DASHBOARD.CARD_TENANT_SUB}</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* SEÇÃO: OPERAÇÕES */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {TEXTS.DASHBOARD.SECTION_OPERATIONS}
        </h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_CHANNELS}</CardTitle>
              <Radio className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.channels ?? 0}</div>
              <p className="text-xs text-muted-foreground">{TEXTS.DASHBOARD.CARD_CHANNELS_SUB}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_STORES}</CardTitle>
              <Store className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.stores ?? 0}</div>
              <p className="text-xs text-muted-foreground">{TEXTS.DASHBOARD.CARD_STORES_SUB}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_PRICES}</CardTitle>
              <Tag className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.prices?.toLocaleString() ?? 0}</div>
              <p className="text-xs text-muted-foreground">{TEXTS.DASHBOARD.CARD_PRICES_SUB}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_STOCK}</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.stock_items?.toLocaleString() ?? 0}</div>
              <p className="text-xs text-muted-foreground">{TEXTS.DASHBOARD.CARD_STOCK_SUB}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_ORDERS}</CardTitle>
              <ShoppingCart className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.orders?.toLocaleString() ?? 0}</div>
              <p className="text-xs text-muted-foreground">
                {TEXTS.DASHBOARD.CARD_ORDERS_SUB_FN(stats?.order_items ?? 0)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_OFFERS}</CardTitle>
              <Percent className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.offers?.toLocaleString() ?? 0}</div>
              <p className="text-xs text-muted-foreground">
                {TEXTS.DASHBOARD.CARD_OFFERS_SUB_FN(stats?.active_offers ?? 0)}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* SEÇÃO: IA */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {TEXTS.DASHBOARD.SECTION_AI}
        </h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{TEXTS.DASHBOARD.CARD_VECTORS}</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.ai_index.total_vectors.toLocaleString()}</div>
              <div className="flex items-center gap-2 mt-2">
                <Progress value={stats?.ai_index.percentage} className="h-2 w-full" />
                <span className="text-xs font-medium">{stats?.ai_index.percentage}%</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                {stats?.ai_index.status === 'active' || stats?.ai_index.status === 'synced' || stats?.ai_index.status === 'green'
                  ? <><CheckCircle className="h-3 w-3 text-green-500" /> {TEXTS.DASHBOARD.STATUS_SYNCED}</>
                  : <><AlertCircle className="h-3 w-3 text-yellow-500" /> {TEXTS.DASHBOARD.STATUS_INDEXING}</>}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
