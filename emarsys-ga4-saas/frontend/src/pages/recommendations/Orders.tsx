import { useEffect, useState, useCallback } from 'react';
import { Search, ShoppingCart, ChevronDown, ChevronRight, ChevronLeft, Filter, X } from 'lucide-react';
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { orderService, type Order } from '@/api/recommendations/commerce';

const PAGE_SIZE = 50;

const STATUS_OPTIONS = ['', 'delivered', 'confirmed', 'cancelled', 'returned'];

const STATUS_COLORS: Record<string, string> = {
  delivered: 'bg-green-500/10 text-green-600 border-green-500/20',
  confirmed:  'bg-blue-500/10 text-blue-600 border-blue-500/20',
  cancelled:  'bg-red-500/10 text-red-600 border-red-500/20',
  returned:   'bg-orange-500/10 text-orange-600 border-orange-500/20',
};

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function fmtMoney(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function Orders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const [customerFilter, setCustomerFilter] = useState('');
  const [productFilter, setProductFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [appliedFilters, setAppliedFilters] = useState<{ customer?: string; product?: string; status?: string }>({});

  const load = useCallback(async (filters: typeof appliedFilters, p: number) => {
    setLoading(true);
    try {
      const res = await orderService.list({
        customer_ref: filters.customer || undefined,
        status: filters.status || undefined,
        product_external_id: filters.product || undefined,
        skip: p * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setOrders(res.items);
      setTotal(res.total);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load({}, 0); }, [load]);

  function applyFilters() {
    const f = {
      customer: customerFilter || undefined,
      product: productFilter || undefined,
      status: statusFilter || undefined,
    };
    setAppliedFilters(f);
    setPage(0);
    load(f, 0);
  }

  function clearFilters() {
    setCustomerFilter('');
    setProductFilter('');
    setStatusFilter('');
    setAppliedFilters({});
    setPage(0);
    load({}, 0);
  }

  function goToPage(p: number) {
    setPage(p);
    load(appliedFilters, p);
    setExpanded(new Set());
  }

  function toggleExpand(id: string) {
    setExpanded(prev => {
      const s = new Set(prev);
      s.has(id) ? s.delete(id) : s.add(id);
      return s;
    });
  }

  const hasFilters = !!(appliedFilters.customer || appliedFilters.product || appliedFilters.status);
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border/40 py-4 px-6 md:px-8 -mx-6 md:-mx-8 mb-6 shadow-sm">
        <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Pedidos</h1>
            <p className="text-sm text-muted-foreground">
              {total.toLocaleString()} pedidos{hasFilters ? ' (filtrado)' : ''}
            </p>
          </div>
        </div>

        {/* Filtros */}
        <div className="flex flex-wrap gap-2 items-end">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Cliente (ID ou nome)..."
              className="pl-8 h-8 w-48 text-xs bg-muted/50"
              value={customerFilter}
              onChange={e => setCustomerFilter(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && applyFilters()}
            />
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="SKU do produto..."
              className="pl-8 h-8 w-40 text-xs bg-muted/50"
              value={productFilter}
              onChange={e => setProductFilter(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && applyFilters()}
            />
          </div>
          <select
            className="h-8 px-2 text-xs rounded-md border border-input bg-muted/50 text-foreground"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value="">Todos os status</option>
            {STATUS_OPTIONS.filter(Boolean).map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <Button size="sm" className="h-8 text-xs" onClick={applyFilters}>
            <Filter className="h-3 w-3 mr-1" /> Filtrar
          </Button>
          {hasFilters && (
            <Button size="sm" variant="ghost" className="h-8 text-xs text-muted-foreground" onClick={clearFilters}>
              <X className="h-3 w-3 mr-1" /> Limpar
            </Button>
          )}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-2">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-14 w-full rounded-lg" />)}</div>
      ) : orders.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 border border-dashed rounded-xl text-center">
          <ShoppingCart className="h-12 w-12 text-muted-foreground mb-3" />
          <p className="font-semibold">Nenhum pedido encontrado</p>
          <p className="text-sm text-muted-foreground">Ajuste os filtros ou faça upload do CSV de pedidos.</p>
        </div>
      ) : (
        <>
          <div className="rounded-xl border border-border overflow-hidden bg-card">
            <div className="grid grid-cols-12 gap-2 px-4 py-2 bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span className="col-span-1" />
              <span className="col-span-2">Pedido</span>
              <span className="col-span-2">Status</span>
              <span className="col-span-3">Data</span>
              <span className="col-span-1 text-right">Itens</span>
              <span className="col-span-3 text-right">Valor Líquido</span>
            </div>

            {orders.map((o, i) => {
              const isOpen = expanded.has(o.order_id);
              return (
                <div key={o.order_id} className={i > 0 ? 'border-t border-border/40' : ''}>
                  {/* Row */}
                  <div
                    onClick={() => toggleExpand(o.order_id)}
                    className="grid grid-cols-12 gap-2 px-4 py-3 items-center cursor-pointer hover:bg-muted/30 transition-colors text-sm"
                  >
                    <div className="col-span-1">
                      {isOpen
                        ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
                    </div>
                    <div className="col-span-2 font-mono text-xs font-medium">{o.order_id}</div>
                    <div className="col-span-2">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${STATUS_COLORS[o.status] ?? 'bg-muted text-muted-foreground border-border'}`}>
                        {o.status}
                      </span>
                    </div>
                    <div className="col-span-3 text-xs text-muted-foreground">{fmtDate(o.ordered_at)}</div>
                    <div className="col-span-1 text-right text-xs text-muted-foreground">{o.items_count}</div>
                    <div className="col-span-3 text-right font-bold text-primary">{fmtMoney(o.net_value)}</div>
                  </div>

                  {/* Expanded items */}
                  {isOpen && (
                    <div className="bg-muted/10 border-t border-border/30 px-4 py-3 space-y-1">
                      {/* Financial summary */}
                      <div className="flex gap-6 text-xs text-muted-foreground mb-3 pb-2 border-b border-border/30">
                        <span>Bruto: <strong className="text-foreground">{fmtMoney(o.gross_value)}</strong></span>
                        <span>Desconto: <strong className="text-red-500">-{fmtMoney(o.discount_value)}</strong></span>
                        <span>Impostos: <strong className="text-foreground">+{fmtMoney(o.tax_value)}</strong></span>
                        <span>Líquido: <strong className="text-primary">{fmtMoney(o.net_value)}</strong></span>
                      </div>
                      {/* Items */}
                      <div className="grid grid-cols-12 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold px-1 mb-1">
                        <span className="col-span-4">SKU</span>
                        <span className="col-span-1 text-right">Qtd</span>
                        <span className="col-span-2 text-right">Unit</span>
                        <span className="col-span-2 text-right">Desc.</span>
                        <span className="col-span-1 text-right">Imp.</span>
                        <span className="col-span-2 text-right">Líquido</span>
                      </div>
                      {o.items.map((item, j) => (
                        <div key={j} className="grid grid-cols-12 text-xs px-1 py-1 rounded hover:bg-muted/20">
                          <div className="col-span-4 font-mono font-medium flex items-center gap-1.5">
                            {item.product_external_id}
                            {item.is_promo && <Badge className="text-[9px] h-4 px-1 bg-orange-500/10 text-orange-600 border-orange-500/20 border">promo</Badge>}
                          </div>
                          <div className="col-span-1 text-right text-muted-foreground">{item.quantity}</div>
                          <div className="col-span-2 text-right">{fmtMoney(item.unit_price)}</div>
                          <div className="col-span-2 text-right text-red-500">{item.discount_amount > 0 ? `-${fmtMoney(item.discount_amount)}` : '—'}</div>
                          <div className="col-span-1 text-right text-muted-foreground">{fmtMoney(item.tax_amount)}</div>
                          <div className="col-span-2 text-right font-semibold">{fmtMoney(item.net_price)}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-xs text-muted-foreground">
                Página {page + 1} de {totalPages} · {total.toLocaleString()} pedidos
              </p>
              <div className="flex items-center gap-2">
                <Button
                  size="sm" variant="outline" className="h-8 text-xs"
                  disabled={page === 0}
                  onClick={() => goToPage(page - 1)}
                >
                  <ChevronLeft className="h-3 w-3 mr-1" /> Anterior
                </Button>
                <Button
                  size="sm" variant="outline" className="h-8 text-xs"
                  disabled={page >= totalPages - 1}
                  onClick={() => goToPage(page + 1)}
                >
                  Próxima <ChevronRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
