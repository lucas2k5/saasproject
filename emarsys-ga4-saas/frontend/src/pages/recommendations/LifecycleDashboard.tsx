import { useEffect, useState } from 'react';
import { Activity, RefreshCw, TrendingUp, Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import { lifecycleDashboardService, type LifecycleDashboardStats } from '../../api/recommendations/commerce';

const SEGMENT_META: Record<string, { color: string }> = {
  Prospect:      { color: '#94a3b8' },
  OneTime:       { color: '#f59e0b' },
  Leaver:        { color: '#e11d48' },
  NonEngaged:    { color: '#ef4444' },
  StuckInMiddle: { color: '#f97316' },
  LoyalRunner:   { color: '#3b82f6' },
  LoyalStar:     { color: '#10b981' },
};

const TREND_COLORS = ['#ef4444', '#f97316', '#3b82f6', '#10b981', '#059669'];
const PROMO_COLORS = ['#10b981', '#84cc16', '#f59e0b', '#f97316', '#ef4444'];
const CHANNEL_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function LifecycleDashboard() {
  const [lcStats, setLcStats] = useState<LifecycleDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchStats = async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await lifecycleDashboardService.stats();
      setLcStats(data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStats(); }, []);

  if (loading) return (
    <div className="flex h-full w-full items-center justify-center min-h-[50vh]">
      <Activity className="animate-spin h-8 w-8 text-primary" />
    </div>
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">

      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Ciclo de Vida</h1>
          <p className="text-muted-foreground">
            Distribuição e indicadores comportamentais da base de clientes
          </p>
        </div>
        <Button variant="outline" onClick={fetchStats}>
          <RefreshCw className="mr-2 h-4 w-4" /> Atualizar
        </Button>
      </div>

      {/* Sem dados */}
      {error || !lcStats || lcStats.total_segmented === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-3 text-center">
            <Users className="h-10 w-10 text-muted-foreground/50" />
            <p className="font-medium text-muted-foreground">Nenhum cliente segmentado ainda</p>
            <p className="text-sm text-muted-foreground max-w-sm">
              Acesse a tela de Clientes e execute o cálculo de segmentos para visualizar os gráficos.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* KPIs rápidos */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total segmentado</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{lcStats.total_segmented.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">de {lcStats.total_customers.toLocaleString()} clientes</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Clientes leais</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-emerald-600">
                  {(
                    (lcStats.segment_distribution.find(s => s.segment === 'LoyalStar')?.count ?? 0) +
                    (lcStats.segment_distribution.find(s => s.segment === 'LoyalRunner')?.count ?? 0)
                  ).toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground">LoyalStar + LoyalRunner</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Em risco / inativos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-500">
                  {(
                    (lcStats.segment_distribution.find(s => s.segment === 'Leaver')?.count ?? 0) +
                    (lcStats.segment_distribution.find(s => s.segment === 'NonEngaged')?.count ?? 0) +
                    (lcStats.segment_distribution.find(s => s.segment === 'OneTime')?.count ?? 0)
                  ).toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground">Leaver + NonEngaged + OneTime</p>
              </CardContent>
            </Card>
          </div>

          {/* Row 1: Donut + Ticket */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Distribuição por Segmento</CardTitle>
                <p className="text-xs text-muted-foreground">
                  {lcStats.total_segmented} clientes classificados
                </p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={lcStats.segment_distribution.filter(d => d.count > 0)}
                      cx="50%"
                      cy="50%"
                      innerRadius={65}
                      outerRadius={95}
                      paddingAngle={2}
                      dataKey="count"
                      nameKey="segment"
                    >
                      {lcStats.segment_distribution.filter(d => d.count > 0).map((entry) => (
                        <Cell key={entry.segment} fill={SEGMENT_META[entry.segment]?.color ?? '#94a3b8'} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value, name) => [
                        `${value} (${((Number(value) / lcStats.total_segmented) * 100).toFixed(1)}%)`,
                        name,
                      ]}
                    />
                    <Legend formatter={(value) => <span className="text-xs">{value}</span>} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Ticket Médio por Segmento</CardTitle>
                <p className="text-xs text-muted-foreground">Valor médio por pedido em cada grupo</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart
                    data={lcStats.avg_ticket_by_segment}
                    layout="vertical"
                    margin={{ left: 8, right: 32, top: 4, bottom: 4 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis
                      type="number"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => `R$${v.toLocaleString('pt-BR')}`}
                    />
                    <YAxis type="category" dataKey="segment" tick={{ fontSize: 11 }} width={90} />
                    <Tooltip
                      formatter={(v) => [
                        `R$ ${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
                        'Ticket médio',
                      ]}
                    />
                    <Bar dataKey="avg_ticket" radius={[0, 4, 4, 0]}>
                      {lcStats.avg_ticket_by_segment.map((entry) => (
                        <Cell key={entry.segment} fill={SEGMENT_META[entry.segment]?.color ?? '#94a3b8'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Row 2: Recência + P(Vivo) */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Recência — Dias desde a Última Compra</CardTitle>
                <p className="text-xs text-muted-foreground">Quantos clientes compraram em cada janela de tempo</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={lcStats.recency_buckets} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Clientes']} />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Distribuição de P(Vivo) — BG/NBD</CardTitle>
                <p className="text-xs text-muted-foreground">Probabilidade de cada cliente ainda estar ativo</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={lcStats.p_alive_buckets} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Clientes']} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {lcStats.p_alive_buckets.map((_, idx) => {
                        const colors = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6', '#10b981'];
                        return <Cell key={idx} fill={colors[idx] ?? '#94a3b8'} />;
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Row 3: Frequência + Tempo como Cliente */}
          {(lcStats.frequency_buckets?.length > 0 || lcStats.tenure_buckets?.length > 0) && (
          <div className="grid gap-4 md:grid-cols-2">
            {lcStats.frequency_buckets?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Frequência de Compras</CardTitle>
                <p className="text-xs text-muted-foreground">Quantas vezes cada cliente comprou</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={lcStats.frequency_buckets} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Clientes']} />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            )}
            {lcStats.tenure_buckets?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Tempo como Cliente</CardTitle>
                <p className="text-xs text-muted-foreground">Há quanto tempo os clientes compram</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={lcStats.tenure_buckets} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Clientes']} />
                    <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            )}
          </div>
          )}

          {/* Row 4: Tendência de Ticket + Velocidade de Compra */}
          {(lcStats.ticket_trend_buckets?.length > 0 || lcStats.velocity_trend_buckets?.length > 0) && (
          <div className="grid gap-4 md:grid-cols-2">
            {lcStats.ticket_trend_buckets?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Tendência de Ticket</CardTitle>
                <p className="text-xs text-muted-foreground">Ticket médio subindo ou caindo (90d vs anterior)</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={lcStats.ticket_trend_buckets} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Clientes']} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {lcStats.ticket_trend_buckets.map((_, idx) => (
                        <Cell key={idx} fill={TREND_COLORS[idx] ?? '#94a3b8'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            )}
            {lcStats.velocity_trend_buckets?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Velocidade de Compra</CardTitle>
                <p className="text-xs text-muted-foreground">Frequência de compra acelerando ou desacelerando</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={lcStats.velocity_trend_buckets} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Clientes']} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {lcStats.velocity_trend_buckets.map((_, idx) => (
                        <Cell key={idx} fill={TREND_COLORS[idx] ?? '#94a3b8'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            )}
          </div>
          )}

          {/* Row 5: Dependência de Promoção + Diversidade de Categorias */}
          {(lcStats.promo_ratio_buckets?.length > 0 || lcStats.category_diversity_buckets?.length > 0) && (
          <div className="grid gap-4 md:grid-cols-2">
            {lcStats.promo_ratio_buckets?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Dependência de Promoção</CardTitle>
                <p className="text-xs text-muted-foreground">Quanto da base compra com promoção</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={lcStats.promo_ratio_buckets} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Clientes']} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {lcStats.promo_ratio_buckets.map((_, idx) => (
                        <Cell key={idx} fill={PROMO_COLORS[idx] ?? '#94a3b8'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            )}
            {lcStats.category_diversity_buckets?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Diversidade de Categorias</CardTitle>
                <p className="text-xs text-muted-foreground">Quantas categorias diferentes cada cliente compra</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={lcStats.category_diversity_buckets} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Clientes']} />
                    <Bar dataKey="count" fill="#14b8a6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            )}
          </div>
          )}

          {/* Row 6: Canal Preferido */}
          {lcStats.channel_distribution?.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Canal Preferido</CardTitle>
                <p className="text-xs text-muted-foreground">Canal mais utilizado pelos clientes</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={lcStats.channel_distribution.filter(d => d.count > 0)}
                      cx="50%"
                      cy="50%"
                      innerRadius={65}
                      outerRadius={95}
                      paddingAngle={2}
                      dataKey="count"
                      nameKey="channel"
                    >
                      {lcStats.channel_distribution.filter(d => d.count > 0).map((_, idx) => (
                        <Cell key={idx} fill={CHANNEL_COLORS[idx % CHANNEL_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend formatter={(value) => <span className="text-xs">{value}</span>} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
          )}

          {/* Row 7: Tendências de Produto */}
          {(lcStats.top_recommended_products?.length > 0 || lcStats.top_recommended_categories?.length > 0) && (
          <>
            <div className="flex items-center gap-2 pt-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold tracking-tight">Tendências de Produto</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {lcStats.top_recommended_products?.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Top 10 Produtos Recomendados</CardTitle>
                  <p className="text-xs text-muted-foreground">Produtos que mais aparecem nas recomendações</p>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart
                      data={lcStats.top_recommended_products}
                      layout="vertical"
                      margin={{ left: 8, right: 32, top: 4, bottom: 4 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                      <YAxis
                        type="category"
                        dataKey="name"
                        tick={{ fontSize: 11 }}
                        width={160}
                        tickFormatter={(v) => v.length > 25 ? v.slice(0, 25) + '…' : v}
                      />
                      <Tooltip />
                      <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              )}
              {lcStats.top_recommended_categories?.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Top 10 Categorias Recomendadas</CardTitle>
                  <p className="text-xs text-muted-foreground">Categorias mais presentes nas recomendações</p>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart
                      data={lcStats.top_recommended_categories}
                      layout="vertical"
                      margin={{ left: 8, right: 32, top: 4, bottom: 4 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                      <YAxis
                        type="category"
                        dataKey="category"
                        tick={{ fontSize: 11 }}
                        width={160}
                      />
                      <Tooltip />
                      <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              )}
            </div>
          </>
          )}
        </>
      )}
    </div>
  );
}
