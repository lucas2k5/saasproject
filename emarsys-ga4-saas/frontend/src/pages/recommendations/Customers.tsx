import { useEffect, useState, useCallback, useRef } from 'react';
import { Search, Users, ChevronRight, ShoppingCart, User, Hash, Phone, Tag, ChevronLeft, Play, Loader2, CheckCircle2, XCircle, Clock, Trash2, ChevronDown, Mail, MessageSquare, Bell } from 'lucide-react';
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { customerService, lifecycleService, recommendationService, adminService, type Customer, type Order, type CustomerLifecycle, type LifecycleJob, type RecommendationJob, type CustomerRecommendationItem } from '../../api/recommendations/commerce';
import api from '../../api/recommendations/axios';

const PAGE_SIZE = 50;

const STATUS_COLORS: Record<string, string> = {
  delivered: 'bg-green-500/10 text-green-600 border-green-500/20',
  confirmed: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  cancelled: 'bg-red-500/10 text-red-600 border-red-500/20',
  returned:  'bg-orange-500/10 text-orange-600 border-orange-500/20',
};

const SEGMENT_COLORS: Record<string, string> = {
  Prospect:       'bg-slate-100 text-slate-700',
  OneTime:        'bg-amber-100 text-amber-700',
  Leaver:         'bg-rose-100 text-rose-700',
  NonEngaged:     'bg-red-100 text-red-700',
  StuckInMiddle:  'bg-orange-100 text-orange-700',
  LoyalRunner:    'bg-blue-100 text-blue-700',
  LoyalStar:      'bg-emerald-100 text-emerald-700',
};

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function fmtMoney(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function Customers() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [segmentFilter, setSegmentFilter] = useState('');
  const [selected, setSelected] = useState<Customer | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [lifecycle, setLifecycle] = useState<CustomerLifecycle | null>(null);
  const [loadingLifecycle, setLoadingLifecycle] = useState(false);
  const [recommendations, setRecommendations] = useState<CustomerRecommendationItem[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);

  // Conteúdo personalizado por algoritmo
  type ContentData = {
    email: string | null;
    whatsapp: string | null;
    push: { image_url?: string } | null;
  };
  const ALGOS = ['pessoal', 'descoberta', 'topseller'] as const;
  const ALGO_LABELS: Record<string, string> = { pessoal: 'Pessoal', descoberta: 'Descoberta', topseller: 'Top Sellers' };
  const [contentByAlgo, setContentByAlgo] = useState<Record<string, ContentData>>({});
  const [loadingContent, setLoadingContent] = useState(false);
  const [contentAlgo, setContentAlgo] = useState<string>('pessoal');
  const [contentChannel, setContentChannel] = useState<'email' | 'whatsapp' | 'push'>('email');

  // Lifecycle job panel
  const [lastJob, setLastJob] = useState<LifecycleJob | null>(null);
  const [runningJob, setRunningJob] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Recommendation job panel
  const [lastRecJob, setLastRecJob] = useState<RecommendationJob | null>(null);
  const [runningRecJob, setRunningRecJob] = useState(false);
  const recPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup panel
  const [cleanupOpen, setCleanupOpen] = useState(false);
  const [purging, setPurging] = useState<string | null>(null);
  const [purgeResults, setPurgeResults] = useState<Record<string, { total: number; ts: number }>>({});

  const load = useCallback(async (q: string, p: number, seg: string) => {
    setLoading(true);
    try {
      const res = await customerService.list(q || undefined, undefined, p * PAGE_SIZE, PAGE_SIZE, seg || undefined);
      setCustomers(res.items);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  }, []);

  // Reset page when search or segment filter changes
  useEffect(() => {
    setPage(0);
  }, [search, segmentFilter]);

  useEffect(() => {
    const t = setTimeout(() => load(search, page, segmentFilter), search ? 400 : 0);
    return () => clearTimeout(t);
  }, [search, page, segmentFilter, load]);

  const drawerAbortRef = useRef<AbortController | null>(null);

  async function openCustomer(c: Customer) {
    // Cancel previous in-flight requests
    if (drawerAbortRef.current) drawerAbortRef.current.abort();
    const controller = new AbortController();
    drawerAbortRef.current = controller;

    setSelected(c);
    setOrders([]);
    setLifecycle(null);
    setRecommendations([]);
    setContentByAlgo({});
    setLoadingOrders(true);
    setLoadingLifecycle(true);
    setLoadingRecs(true);
    setLoadingContent(true);

    const signal = controller.signal;
    try { const o = await customerService.getOrders(c.customer_id, 10); if (!signal.aborted) setOrders(o); }
    finally { if (!signal.aborted) setLoadingOrders(false); }
    try { const lc = await customerService.getLifecycle(c.customer_id); if (!signal.aborted) setLifecycle(lc); }
    catch { /* lifecycle pode não existir ainda */ }
    finally { if (!signal.aborted) setLoadingLifecycle(false); }
    try {
      const res = await recommendationService.getForCustomer(c.customer_id, 6);
      if (!signal.aborted) setRecommendations(res.recommendations ?? []);
    } catch { /* recomendações podem não existir ainda */ }
    finally { if (!signal.aborted) setLoadingRecs(false); }

    // Conteúdo personalizado — busca para cada algoritmo em paralelo
    const ref = c.customer_id;
    const algoPromises = ALGOS.map(async (algo) => {
      const results: ContentData = { email: null, whatsapp: null, push: null };
      const [emailRes, waRes, pushRes] = await Promise.allSettled([
        api.get(`/content/email/${ref}?algorithm=${algo}`),
        api.get(`/content/whatsapp/${ref}?algorithm=${algo}`),
        api.get(`/content/push/${ref}?algorithm=${algo}`),
      ]);
      if (emailRes.status === 'fulfilled') results.email = emailRes.value.data.html_body;
      if (waRes.status === 'fulfilled') results.whatsapp = waRes.value.data.image_url;
      if (pushRes.status === 'fulfilled') results.push = { image_url: pushRes.value.data.image_url };
      return { algo, results };
    });
    Promise.all(algoPromises).then(items => {
      if (signal.aborted) return;
      const map: Record<string, ContentData> = {};
      for (const { algo, results } of items) {
        if (results.email || results.whatsapp || results.push) map[algo] = results;
      }
      setContentByAlgo(map);
      // Seleciona primeiro algoritmo com conteúdo
      const first = ALGOS.find(a => map[a]);
      if (first) setContentAlgo(first);
      setLoadingContent(false);
    });
  }

  // --- Lifecycle job controls ---
  const fetchJobStatus = useCallback(async () => {
    try {
      const res = await lifecycleService.status(1);
      setLastJob(res.items[0] ?? null);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    fetchJobStatus();
  }, [fetchJobStatus]);

  // Poll while job is queued/running
  useEffect(() => {
    if (lastJob && (lastJob.status === 'queued' || lastJob.status === 'running')) {
      pollRef.current = setInterval(fetchJobStatus, 3000);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [lastJob?.status, fetchJobStatus]);

  async function handleRunLifecycle() {
    setRunningJob(true);
    try {
      await lifecycleService.run();
      await fetchJobStatus();
    } finally {
      setRunningJob(false);
    }
  }

  // --- Recommendation job controls ---
  const fetchRecJobStatus = useCallback(async () => {
    try {
      const res = await recommendationService.status(1);
      setLastRecJob(res.items[0] ?? null);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    fetchRecJobStatus();
  }, [fetchRecJobStatus]);

  useEffect(() => {
    if (lastRecJob && (lastRecJob.status === 'queued' || lastRecJob.status === 'running')) {
      recPollRef.current = setInterval(fetchRecJobStatus, 3000);
    }
    return () => {
      if (recPollRef.current) clearInterval(recPollRef.current);
    };
  }, [lastRecJob?.status, fetchRecJobStatus]);

  async function handleRunRecommendations() {
    setRunningRecJob(true);
    try {
      await recommendationService.run();
      await fetchRecJobStatus();
    } finally {
      setRunningRecJob(false);
    }
  }

  async function handlePurge(entity: string, label: string) {
    if (!confirm(`Limpar todos os registros de "${label}" do tenant? Esta ação não pode ser desfeita.`)) return;
    setPurging(entity);
    try {
      const res = await adminService.purge(entity);
      setPurgeResults(prev => ({ ...prev, [entity]: { total: res.total_deleted, ts: Date.now() } }));
      // Refresh list after purge
      load(search, page, segmentFilter);
    } catch (e: any) {
      alert(`Erro ao limpar ${label}: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setPurging(null);
    }
  }

  const CLEANUP_ITEMS: { key: string; label: string; desc: string }[] = [
    { key: 'orders',    label: 'Pedidos + Itens',    desc: 'Remove pedidos, itens, summary, segmentos e recomendações' },
    { key: 'offers',    label: 'Ofertas',             desc: 'Remove ofertas, produtos da oferta e audiências' },
    { key: 'stock',     label: 'Estoque',             desc: 'Remove todo o estoque' },
    { key: 'prices',    label: 'Preços',              desc: 'Remove todos os preços' },
    { key: 'lifecycle', label: 'Lifecycle',            desc: 'Remove summary e segmentos (mantém pedidos)' },
    { key: 'recs',      label: 'Recomendações',       desc: 'Remove recomendações, top sellers e similares' },
    { key: 'jobs',      label: 'Jobs',                desc: 'Remove fila de jobs (segmentação + recomendação)' },
  ];

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border/40 py-4 px-6 md:px-8 -mx-6 md:-mx-8 mb-6 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Clientes</h1>
          <p className="text-sm text-muted-foreground">
            {total.toLocaleString()} clientes{search ? ' encontrados' : ' no total'}
          </p>
        </div>
        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-72">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por nome, ID ou CRM..."
              className="pl-9 bg-muted/50"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <select
            value={segmentFilter}
            onChange={e => setSegmentFilter(e.target.value)}
            className="h-9 rounded-md border border-input bg-muted/50 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Todos os segmentos</option>
            {Object.keys(SEGMENT_COLORS).map(seg => (
              <option key={seg} value={seg}>{seg}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Lifecycle Panel */}
      <div className="mb-4 rounded-xl border border-border bg-card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <p className="text-sm font-semibold">Segmentacao de Clientes</p>
            {lastJob ? (
              <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                {lastJob.status === 'done' && (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                    <span>Concluido — {lastJob.customers_processed} clientes processados</span>
                    {lastJob.finished_at && <span className="opacity-60">({fmtDate(lastJob.finished_at)})</span>}
                  </>
                )}
                {lastJob.status === 'running' && (
                  <>
                    <Loader2 className="h-3.5 w-3.5 text-blue-500 animate-spin" />
                    <span>Calculando segmentos...</span>
                  </>
                )}
                {lastJob.status === 'queued' && (
                  <>
                    <Clock className="h-3.5 w-3.5 text-amber-500" />
                    <span>Na fila, aguardando...</span>
                  </>
                )}
                {lastJob.status === 'failed' && (
                  <>
                    <XCircle className="h-3.5 w-3.5 text-red-500" />
                    <span>Falhou: {lastJob.error_msg || 'erro desconhecido'}</span>
                  </>
                )}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground mt-1">Nenhum calculo executado ainda.</p>
            )}
          </div>
        </div>
        <Button
          size="sm"
          onClick={handleRunLifecycle}
          disabled={runningJob || lastJob?.status === 'queued' || lastJob?.status === 'running'}
          className="gap-2"
        >
          {(runningJob || lastJob?.status === 'running' || lastJob?.status === 'queued')
            ? <><Loader2 className="h-4 w-4 animate-spin" /> Processando...</>
            : <><Play className="h-4 w-4" /> Calcular Segmentos</>}
        </Button>
      </div>

      {/* Recommendation Panel */}
      <div className="mb-4 rounded-xl border border-border bg-card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <p className="text-sm font-semibold">Motor de Recomendação</p>
            {lastRecJob ? (
              <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                {lastRecJob.status === 'done' && (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                    <span>Concluído — {lastRecJob.customers_processed} clientes processados</span>
                    {lastRecJob.finished_at && <span className="opacity-60">({fmtDate(lastRecJob.finished_at)})</span>}
                  </>
                )}
                {lastRecJob.status === 'running' && (
                  <>
                    <Loader2 className="h-3.5 w-3.5 text-blue-500 animate-spin" />
                    <span>Calculando recomendações...</span>
                  </>
                )}
                {lastRecJob.status === 'queued' && (
                  <>
                    <Clock className="h-3.5 w-3.5 text-amber-500" />
                    <span>Na fila, aguardando...</span>
                  </>
                )}
                {lastRecJob.status === 'failed' && (
                  <>
                    <XCircle className="h-3.5 w-3.5 text-red-500" />
                    <span>Falhou: {lastRecJob.error_msg || 'erro desconhecido'}</span>
                  </>
                )}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground mt-1">Nenhum cálculo executado ainda.</p>
            )}
          </div>
        </div>
        <Button
          size="sm"
          onClick={handleRunRecommendations}
          disabled={runningRecJob || lastRecJob?.status === 'queued' || lastRecJob?.status === 'running'}
          className="gap-2"
        >
          {(runningRecJob || lastRecJob?.status === 'running' || lastRecJob?.status === 'queued')
            ? <><Loader2 className="h-4 w-4 animate-spin" /> Processando...</>
            : <><Play className="h-4 w-4" /> Calcular Recomendações</>}
        </Button>
      </div>

      {/* Cleanup Panel */}
      <div className="mb-4 rounded-xl border border-border bg-card">
        <button
          onClick={() => setCleanupOpen(o => !o)}
          className="w-full flex items-center justify-between p-4 text-left hover:bg-muted/30 transition-colors rounded-xl"
        >
          <div className="flex items-center gap-2">
            <Trash2 className="h-4 w-4 text-red-500" />
            <p className="text-sm font-semibold">Limpeza de Dados</p>
            <span className="text-xs text-muted-foreground">Limpe entidades antes de reimportar</span>
          </div>
          <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${cleanupOpen ? 'rotate-180' : ''}`} />
        </button>
        {cleanupOpen && (
          <div className="px-4 pb-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {CLEANUP_ITEMS.map(item => {
              const result = purgeResults[item.key];
              const isRecent = result && Date.now() - result.ts < 10000;
              return (
                <div key={item.key} className="rounded-lg border border-border/40 p-3 bg-muted/10 space-y-2">
                  <p className="text-xs font-semibold">{item.label}</p>
                  <p className="text-[10px] text-muted-foreground leading-tight">{item.desc}</p>
                  <Button
                    size="sm"
                    variant="destructive"
                    className="w-full h-7 text-xs gap-1"
                    disabled={purging === item.key}
                    onClick={() => handlePurge(item.key, item.label)}
                  >
                    {purging === item.key ? (
                      <><Loader2 className="h-3 w-3 animate-spin" /> Limpando...</>
                    ) : (
                      <><Trash2 className="h-3 w-3" /> Limpar</>
                    )}
                  </Button>
                  {isRecent && (
                    <p className="text-[10px] text-green-600 font-medium">
                      {result.total} registros removidos
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-2">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-14 w-full rounded-lg" />)}</div>
      ) : customers.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 border border-dashed rounded-xl text-center">
          <Users className="h-12 w-12 text-muted-foreground mb-3" />
          <p className="font-semibold">Nenhum cliente encontrado</p>
          <p className="text-sm text-muted-foreground">Faça upload do CSV de clientes na tela de Cargas.</p>
        </div>
      ) : (
        <>
          <div className="rounded-xl border border-border overflow-hidden bg-card">
            <div className="grid grid-cols-12 gap-4 px-4 py-2 bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span className="col-span-4">Nome</span>
              <span className="col-span-3">ID / CRM</span>
              <span className="col-span-2">Tipo</span>
              <span className="col-span-2">Cliente desde</span>
              <span className="col-span-1" />
            </div>
            {customers.map((c, i) => (
              <div
                key={c.id}
                onClick={() => openCustomer(c)}
                className={`grid grid-cols-12 gap-4 px-4 py-3 items-center cursor-pointer hover:bg-muted/30 transition-colors text-sm ${i > 0 ? 'border-t border-border/40' : ''}`}
              >
                <div className="col-span-4 font-medium truncate">{c.name}</div>
                <div className="col-span-3 font-mono text-xs text-muted-foreground space-y-0.5">
                  <div>{c.customer_id}</div>
                  {c.customer_add_id && <div className="opacity-60">{c.customer_add_id}</div>}
                </div>
                <div className="col-span-2">
                  {c.customer_type
                    ? <Badge variant="outline" className="text-[10px] capitalize">{c.customer_type}</Badge>
                    : <span className="text-muted-foreground text-xs">—</span>}
                </div>
                <div className="col-span-2 text-muted-foreground text-xs">{fmtDate(c.created_at)}</div>
                <div className="col-span-1 flex justify-end"><ChevronRight className="h-4 w-4 text-muted-foreground" /></div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-xs text-muted-foreground">
                Página {page + 1} de {totalPages} · {total.toLocaleString()} registros
              </p>
              <div className="flex items-center gap-2">
                <Button
                  size="sm" variant="outline" className="h-8 text-xs"
                  disabled={page === 0}
                  onClick={() => setPage(p => p - 1)}
                >
                  <ChevronLeft className="h-3 w-3 mr-1" /> Anterior
                </Button>
                <Button
                  size="sm" variant="outline" className="h-8 text-xs"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage(p => p + 1)}
                >
                  Próxima <ChevronRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Drawer */}
      <Sheet open={!!selected} onOpenChange={open => !open && setSelected(null)}>
        <SheetContent className="w-[95vw] sm:max-w-4xl overflow-y-auto p-0 gap-0">
          {selected && (
            <div className="p-6 space-y-6">
              <SheetHeader>
                <SheetTitle className="text-xl font-bold">{selected.name}</SheetTitle>
              </SheetHeader>

              {/* Info */}
              <div className="grid grid-cols-2 gap-4">
                {[
                  { icon: Hash, label: 'ID ERP', value: selected.customer_id },
                  { icon: Hash, label: 'ID CRM', value: selected.customer_add_id || '—' },
                  { icon: Tag, label: 'Tipo', value: selected.customer_type || '—' },
                  { icon: Phone, label: 'Documento', value: selected.document || '—' },
                  { icon: User, label: 'Cliente desde', value: fmtDate(selected.created_at) },
                  { icon: User, label: 'Origem', value: selected.source_created_at ? fmtDate(selected.source_created_at) : '—' },
                ].map(({ icon: Icon, label, value }) => (
                  <div key={label} className="bg-muted/20 rounded-lg p-3 border border-border/40">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1 flex items-center gap-1"><Icon className="h-3 w-3" />{label}</p>
                    <p className="text-sm font-medium truncate">{value}</p>
                  </div>
                ))}
              </div>

              {/* Lifecycle */}
              {loadingLifecycle ? (
                <Skeleton className="h-32 w-full rounded-lg" />
              ) : lifecycle?.lifecycle ? (
                <div className="rounded-lg border border-border p-4 bg-muted/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-sm">Ciclo de Vida</p>
                    <Badge className={SEGMENT_COLORS[lifecycle.lifecycle.segment] ?? 'bg-muted text-muted-foreground'}>
                      {lifecycle.lifecycle.segment}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    {[
                      { label: 'Recência', value: lifecycle.lifecycle.indicators.recency_days != null ? `${lifecycle.lifecycle.indicators.recency_days}d` : '—' },
                      { label: 'Pedidos', value: lifecycle.lifecycle.indicators.number_of_invoices ?? '—' },
                      { label: 'Ticket Médio', value: lifecycle.lifecycle.indicators.avg_ticket != null ? fmtMoney(lifecycle.lifecycle.indicators.avg_ticket) : '—' },
                      { label: 'Intervalo Médio', value: lifecycle.lifecycle.indicators.avg_days_between != null ? `${lifecycle.lifecycle.indicators.avg_days_between.toFixed(0)}d` : '—' },
                      { label: 'Regularidade', value: lifecycle.lifecycle.indicators.purchase_regularity != null ? lifecycle.lifecycle.indicators.purchase_regularity.toFixed(2) : '—' },
                      { label: 'Vel. Compra', value: lifecycle.lifecycle.indicators.purchase_velocity_trend != null ? `${(lifecycle.lifecycle.indicators.purchase_velocity_trend * 100).toFixed(0)}%` : '—' },
                      { label: 'P(Vivo)', value: lifecycle.lifecycle.indicators.p_alive != null ? `${(lifecycle.lifecycle.indicators.p_alive * 100).toFixed(0)}%` : '—' },
                      { label: 'Previsão 90d', value: lifecycle.lifecycle.indicators.expected_transactions != null ? `${lifecycle.lifecycle.indicators.expected_transactions.toFixed(1)} ped.` : '—' },
                      { label: '% Promo', value: lifecycle.lifecycle.indicators.promo_ratio != null ? `${(lifecycle.lifecycle.indicators.promo_ratio * 100).toFixed(0)}%` : '—' },
                      { label: 'SKUs Distintos', value: lifecycle.lifecycle.indicators.distinct_articles ?? '—' },
                      { label: 'Categorias', value: lifecycle.lifecycle.indicators.category_diversity ?? '—' },
                    ].map(({ label, value }) => (
                      <div key={label} className="bg-background rounded p-2 border border-border/30">
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
                        <p className="font-semibold">{value}</p>
                      </div>
                    ))}
                  </div>
                  {lifecycle.lifecycle.preferences.top_5_categories && lifecycle.lifecycle.preferences.top_5_categories.length > 0 && (
                    <div>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Top Categorias</p>
                      <div className="flex flex-wrap gap-1">
                        {lifecycle.lifecycle.preferences.top_5_categories.map(c => (
                          <Badge key={c} variant="outline" className="text-[10px]">{c}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {lifecycle.lifecycle.preferences.preferred_channel && (
                    <p className="text-[10px] text-muted-foreground">
                      Canal preferido: <span className="font-medium text-foreground">{lifecycle.lifecycle.preferences.preferred_channel}</span>
                    </p>
                  )}
                </div>
              ) : lifecycle?.summary ? (
                <div className="rounded-lg border border-border p-4 bg-muted/10 space-y-2">
                  <p className="font-semibold text-sm">Resumo de Compras</p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="bg-background rounded p-2 border border-border/30">
                      <p className="text-[10px] text-muted-foreground uppercase">Pedidos</p>
                      <p className="font-semibold">{lifecycle.summary.total_orders}</p>
                    </div>
                    <div className="bg-background rounded p-2 border border-border/30">
                      <p className="text-[10px] text-muted-foreground uppercase">Total</p>
                      <p className="font-semibold">{fmtMoney(lifecycle.summary.total_value)}</p>
                    </div>
                    <div className="bg-background rounded p-2 border border-border/30">
                      <p className="text-[10px] text-muted-foreground uppercase">Últ. 90d</p>
                      <p className="font-semibold">{lifecycle.summary.orders_90d} ped.</p>
                    </div>
                  </div>
                  <p className="text-[10px] text-muted-foreground italic">Segmento será calculado no próximo ciclo.</p>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-border p-4 text-center text-muted-foreground text-sm bg-muted/10">
                  <p className="font-semibold mb-1">Indicadores de Ciclo de Vida</p>
                  <p className="text-xs">Disponíveis após ingestão de pedidos e cálculo de segmentos.</p>
                </div>
              )}

              <Separator />

              {/* Recomendações */}
              <div>
                <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <ShoppingCart className="h-4 w-4 text-primary" /> Recomendações
                </h4>
                {loadingRecs ? (
                  <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-20 w-full rounded" />)}</div>
                ) : recommendations.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-border p-4 text-center text-muted-foreground text-sm bg-muted/10">
                    <p className="text-xs">Nenhuma recomendação disponível. Execute o motor de recomendação primeiro.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {(['pessoal', 'descoberta', 'topseller'] as const).map(algo => {
                      const items = recommendations.filter(r => r.algorithm === algo);
                      if (items.length === 0) return null;
                      const algoLabel: Record<string, string> = {
                        pessoal: 'Para Você',
                        descoberta: 'Descubra',
                        topseller: 'Mais Vendidos',
                      };
                      const algoColor: Record<string, string> = {
                        pessoal: 'text-blue-600 bg-blue-50 border-blue-200',
                        descoberta: 'text-purple-600 bg-purple-50 border-purple-200',
                        topseller: 'text-amber-600 bg-amber-50 border-amber-200',
                      };
                      return (
                        <div key={algo}>
                          <Badge variant="outline" className={`text-[10px] mb-2 ${algoColor[algo] ?? ''}`}>
                            {algoLabel[algo] ?? algo}
                          </Badge>
                          <div className="grid grid-cols-3 gap-2">
                            {items.sort((a, b) => a.rank - b.rank).map(rec => (
                              <div key={`${rec.algorithm}-${rec.rank}`} className="rounded-lg border border-border/40 p-3 bg-muted/10 hover:bg-muted/20 transition-colors">
                                <p className="text-xs font-medium line-clamp-2 leading-tight" title={rec.product_name}>{rec.product_name}</p>
                                {rec.product_category && (
                                  <p className="text-[10px] text-muted-foreground truncate mt-0.5">{rec.product_category}</p>
                                )}
                                <div className="flex items-center gap-2 mt-2">
                                  {rec.offer_price != null ? (
                                    <>
                                      <span className="text-[10px] line-through text-muted-foreground">{fmtMoney(rec.base_price)}</span>
                                      <span className="text-sm font-bold text-green-600">{fmtMoney(rec.offer_price)}</span>
                                    </>
                                  ) : (
                                    <span className="text-sm font-bold">{fmtMoney(rec.base_price)}</span>
                                  )}
                                </div>
                                {rec.offer_name && (
                                  <Badge variant="outline" className="text-[9px] mt-1.5 bg-green-50 text-green-700 border-green-200">{rec.offer_name}</Badge>
                                )}
                                <p className="text-[9px] text-muted-foreground mt-1.5 opacity-60">Score: {rec.score.toFixed(3)}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <Separator />

              {/* Conteúdo Personalizado */}
              <div>
                <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <Mail className="h-4 w-4 text-primary" /> Conteúdo Personalizado
                </h4>
                {loadingContent ? (
                  <div className="space-y-2">{[1,2].map(i => <Skeleton key={i} className="h-20 w-full rounded" />)}</div>
                ) : Object.keys(contentByAlgo).length === 0 ? (
                  <div className="rounded-lg border border-dashed border-border p-4 text-center text-muted-foreground text-sm bg-muted/10">
                    <p className="text-xs">Nenhum conteúdo gerado. Execute a personalização na página de Conteúdo.</p>
                  </div>
                ) : (() => {
                  const current = contentByAlgo[contentAlgo];
                  return (
                    <div>
                      {/* Seletor de algoritmo */}
                      <div className="flex gap-1 mb-2">
                        {ALGOS.filter(a => contentByAlgo[a]).map(algo => (
                          <Button key={algo} size="sm" variant={contentAlgo === algo ? 'default' : 'outline'} className="h-7 text-xs" onClick={() => setContentAlgo(algo)}>
                            {ALGO_LABELS[algo]}
                          </Button>
                        ))}
                      </div>

                      {/* Seletor de canal */}
                      {current && (
                        <div className="flex gap-1 mb-3">
                          {current.email && (
                            <Button size="sm" variant={contentChannel === 'email' ? 'secondary' : 'ghost'} className="h-6 text-[10px] gap-1" onClick={() => setContentChannel('email')}>
                              <Mail className="h-3 w-3" /> Email
                            </Button>
                          )}
                          {current.whatsapp && (
                            <Button size="sm" variant={contentChannel === 'whatsapp' ? 'secondary' : 'ghost'} className="h-6 text-[10px] gap-1" onClick={() => setContentChannel('whatsapp')}>
                              <MessageSquare className="h-3 w-3" /> WhatsApp
                            </Button>
                          )}
                          {current.push && (
                            <Button size="sm" variant={contentChannel === 'push' ? 'secondary' : 'ghost'} className="h-6 text-[10px] gap-1" onClick={() => setContentChannel('push')}>
                              <Bell className="h-3 w-3" /> Push
                            </Button>
                          )}
                        </div>
                      )}

                      {/* Email preview */}
                      {contentChannel === 'email' && current?.email && (
                        <div className="rounded-lg border border-border overflow-hidden bg-white">
                          <iframe
                            srcDoc={`<style>body{margin:0;overflow-x:hidden}table[width="600"],table[width="100%"]{width:100%!important;max-width:100%!important}td[style*="padding"]{padding-left:12px!important;padding-right:12px!important}img{max-width:100%;height:auto!important}</style>${current.email}`}
                            title="Email preview"
                            className="w-full border-0"
                            style={{ height: '480px' }}
                            sandbox="allow-same-origin"
                          />
                        </div>
                      )}

                      {/* WhatsApp preview */}
                      {contentChannel === 'whatsapp' && current?.whatsapp && (
                        <div className="rounded-lg border border-border overflow-hidden bg-muted/10 p-4 text-center">
                          <img src={current.whatsapp} alt="WhatsApp content" className="max-w-full rounded-lg mx-auto shadow-md" style={{ maxHeight: '500px' }} />
                        </div>
                      )}

                      {/* Push preview — só imagem */}
                      {contentChannel === 'push' && current?.push && (
                        <div className="rounded-lg border border-border bg-white p-2 max-w-md mx-auto shadow-sm">
                          {current.push.image_url ? (
                            <img src={current.push.image_url} alt="Push" className="w-full rounded-lg" />
                          ) : (
                            <p className="text-xs text-muted-foreground text-center py-4">Imagem não disponível</p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>

              <Separator />

              {/* Últimos pedidos */}
              <div>
                <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                  <ShoppingCart className="h-4 w-4 text-primary" /> Últimos Pedidos
                </h4>
                {loadingOrders ? (
                  <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-12 w-full rounded" />)}</div>
                ) : orders.length === 0 ? (
                  <p className="text-xs text-muted-foreground italic">Nenhum pedido encontrado para este cliente.</p>
                ) : (
                  <div className="space-y-2">
                    {orders.map(o => (
                      <div key={o.order_id} className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2.5 bg-muted/10 text-sm">
                        <div className="space-y-0.5">
                          <p className="font-mono text-xs font-medium">{o.order_id}</p>
                          <p className="text-xs text-muted-foreground">{fmtDate(o.ordered_at)} · {o.items_count} iten{o.items_count !== 1 ? 's' : ''}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${STATUS_COLORS[o.status] ?? 'bg-muted text-muted-foreground'}`}>{o.status}</span>
                          <span className="font-bold text-sm text-primary">{fmtMoney(o.net_value)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
