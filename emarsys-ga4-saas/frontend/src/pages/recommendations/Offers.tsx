import { useEffect, useState, useMemo } from 'react';
import { Search, Percent, ChevronRight, Filter, X, Tag, Users, Calendar } from 'lucide-react';
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { offerService, type Offer } from '../../api/recommendations/commerce';

// ---- Helpers ----

const TYPE_LABELS: Record<string, string> = {
  DIRECT_DISCOUNT:  'Desconto Direto',
  TAKE_X_PAY_Y:     'Leve X Pague Y',
  BUY_X_GET_Y:      'Compre X Ganhe Y',
  BUY_X_GET_PRODUCT:'Compre A Ganhe B',
  PROGRESSIVE:      'Desconto Progressivo',
  COMBO:            'Combo / Kit',
  CASHBACK:         'Cashback',
};

const TYPE_COLORS: Record<string, string> = {
  DIRECT_DISCOUNT:  'bg-blue-500/10 text-blue-600 border-blue-500/20',
  TAKE_X_PAY_Y:     'bg-purple-500/10 text-purple-600 border-purple-500/20',
  BUY_X_GET_Y:      'bg-orange-500/10 text-orange-600 border-orange-500/20',
  BUY_X_GET_PRODUCT:'bg-teal-500/10 text-teal-600 border-teal-500/20',
  PROGRESSIVE:      'bg-green-500/10 text-green-600 border-green-500/20',
  COMBO:            'bg-yellow-500/10 text-yellow-700 border-yellow-500/20',
  CASHBACK:         'bg-pink-500/10 text-pink-600 border-pink-500/20',
};

const AUDIENCE_LABELS: Record<string, string> = {
  ALL:              'Geral (todos)',
  CUSTOMER_IDS:     'Clientes específicos',
  CUSTOMER_TYPE:    'Por tipo de cliente',
  LIFECYCLE_SEGMENT:'Por segmento',
};

function offerStatus(o: Offer): { label: string; cls: string } {
  const now = Date.now();
  const start = new Date(o.start_at).getTime();
  const end = new Date(o.end_at).getTime();
  if (now < start) return { label: 'Agendada', cls: 'bg-blue-500/10 text-blue-600 border-blue-500/20' };
  if (now > end)   return { label: 'Expirada',  cls: 'bg-muted text-muted-foreground border-border' };
  return { label: 'Ativa', cls: 'bg-green-500/10 text-green-600 border-green-500/20' };
}

function formatMechanic(type: string, params: Record<string, any>): string {
  try {
    if (type === 'DIRECT_DISCOUNT')
      return params.discount_type === 'percent'
        ? `${params.discount_value}% de desconto`
        : `R$ ${params.discount_value.toFixed(2)} de desconto`;
    if (type === 'TAKE_X_PAY_Y')
      return `Leve ${params.take}, pague ${params.pay}`;
    if (type === 'BUY_X_GET_Y')
      return `Compre ${params.trigger_quantity}, ganhe ${params.reward_quantity} (${params.reward_discount_percent}% desc.)`;
    if (type === 'BUY_X_GET_PRODUCT')
      return `Compre ${params.trigger_quantity ?? 1} e ganhe ${params.reward_quantity ?? 1} de outro produto`;
    if (type === 'PROGRESSIVE')
      return (params.tiers as any[]).map((t: any) => `${t.min_qty}+ un: ${t.discount_percent}%`).join(' · ');
    if (type === 'COMBO')
      return params.combo_price
        ? `Kit por R$ ${params.combo_price.toFixed(2)}`
        : `Kit com ${params.combo_discount_percent}% de desconto`;
    if (type === 'CASHBACK')
      return `${params.cashback_percent}% cashback (${params.credit_type})`;
  } catch { /* fallthrough */ }
  return JSON.stringify(params);
}

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function fmtMoney(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function Offers() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Offer | null>(null);
  const [productSearch, setProductSearch] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);

  useEffect(() => {
    offerService.list().then(setOffers).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let list = offers;
    if (activeOnly) list = list.filter(o => offerStatus(o).label === 'Ativa');
    if (productSearch) {
      const q = productSearch.toLowerCase();
      list = list.filter(o =>
        o.products.some(p =>
          p.product_external_id.toLowerCase().includes(q) ||
          p.product_name.toLowerCase().includes(q)
        )
      );
    }
    return list;
  }, [offers, activeOnly, productSearch]);

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border/40 py-4 px-6 md:px-8 -mx-6 md:-mx-8 mb-6 shadow-sm">
        <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Ofertas</h1>
            <p className="text-sm text-muted-foreground">{filtered.length} de {offers.length} ofertas</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Filtrar por produto..."
              className="pl-8 h-8 w-52 text-xs bg-muted/50"
              value={productSearch}
              onChange={e => setProductSearch(e.target.value)}
            />
          </div>
          <Button
            size="sm"
            variant={activeOnly ? 'default' : 'outline'}
            className="h-8 text-xs"
            onClick={() => setActiveOnly(v => !v)}
          >
            <Filter className="h-3 w-3 mr-1" /> Somente ativas
          </Button>
          {(productSearch || activeOnly) && (
            <Button size="sm" variant="ghost" className="h-8 text-xs text-muted-foreground" onClick={() => { setProductSearch(''); setActiveOnly(false); }}>
              <X className="h-3 w-3 mr-1" /> Limpar
            </Button>
          )}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-14 w-full rounded-lg" />)}</div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 border border-dashed rounded-xl text-center">
          <Percent className="h-12 w-12 text-muted-foreground mb-3" />
          <p className="font-semibold">Nenhuma oferta encontrada</p>
          <p className="text-sm text-muted-foreground">Ajuste os filtros ou faça upload do CSV de ofertas.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-border overflow-hidden bg-card">
          <div className="grid grid-cols-12 gap-2 px-4 py-2 bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <span className="col-span-3">Nome</span>
            <span className="col-span-2">Tipo</span>
            <span className="col-span-2">Mecânica</span>
            <span className="col-span-1 text-center">Status</span>
            <span className="col-span-1 text-center">Prods</span>
            <span className="col-span-2">Vigência</span>
            <span className="col-span-1" />
          </div>

          {filtered.map((o, i) => {
            const { label: statusLabel, cls: statusCls } = offerStatus(o);
            return (
              <div
                key={o.offer_id}
                onClick={() => setSelected(o)}
                className={`grid grid-cols-12 gap-2 px-4 py-3 items-center cursor-pointer hover:bg-muted/30 transition-colors text-sm ${i > 0 ? 'border-t border-border/40' : ''}`}
              >
                <div className="col-span-3">
                  <p className="font-medium truncate">{o.name}</p>
                  <p className="text-[10px] text-muted-foreground font-mono">{o.offer_id}</p>
                </div>
                <div className="col-span-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${TYPE_COLORS[o.type] ?? 'bg-muted border-border text-muted-foreground'}`}>
                    {TYPE_LABELS[o.type] ?? o.type}
                  </span>
                </div>
                <div className="col-span-2 text-xs text-muted-foreground truncate">{formatMechanic(o.type, o.mechanic_params)}</div>
                <div className="col-span-1 text-center">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${statusCls}`}>{statusLabel}</span>
                </div>
                <div className="col-span-1 text-center text-xs text-muted-foreground">{o.products.filter(p => p.role === 'TRIGGER' || p.role === 'COMBO_MEMBER').length}</div>
                <div className="col-span-2 text-xs text-muted-foreground">
                  <div>{fmtDate(o.start_at)}</div>
                  <div className="opacity-60">até {fmtDate(o.end_at)}</div>
                </div>
                <div className="col-span-1 flex justify-end"><ChevronRight className="h-4 w-4 text-muted-foreground" /></div>
              </div>
            );
          })}
        </div>
      )}

      {/* Drawer */}
      <Sheet open={!!selected} onOpenChange={open => !open && setSelected(null)}>
        <SheetContent className="w-[95vw] sm:max-w-xl overflow-y-auto p-0 gap-0">
          {selected && (() => {
            const { label: statusLabel, cls: statusCls } = offerStatus(selected);
            return (
              <div className="p-6 space-y-5">
                <SheetHeader>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <SheetTitle className="text-xl font-bold">{selected.name}</SheetTitle>
                      <p className="text-xs text-muted-foreground font-mono mt-0.5">{selected.offer_id}</p>
                    </div>
                    <span className={`text-[10px] px-2 py-1 rounded-full border font-medium shrink-0 ${statusCls}`}>{statusLabel}</span>
                  </div>
                </SheetHeader>

                {/* Meta */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-muted/20 rounded-lg p-3 border border-border/40">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">Tipo</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${TYPE_COLORS[selected.type] ?? ''}`}>
                      {TYPE_LABELS[selected.type] ?? selected.type}
                    </span>
                  </div>
                  <div className="bg-muted/20 rounded-lg p-3 border border-border/40">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">Prioridade</p>
                    <p className="text-sm font-bold">{selected.priority}</p>
                  </div>
                  <div className="bg-muted/20 rounded-lg p-3 border border-border/40">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1 flex items-center gap-1"><Calendar className="h-3 w-3"/>Início</p>
                    <p className="text-sm font-medium">{fmtDate(selected.start_at)}</p>
                  </div>
                  <div className="bg-muted/20 rounded-lg p-3 border border-border/40">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1 flex items-center gap-1"><Calendar className="h-3 w-3"/>Fim</p>
                    <p className="text-sm font-medium">{fmtDate(selected.end_at)}</p>
                  </div>
                </div>

                {/* Mecânica */}
                <div className="bg-primary/5 rounded-lg p-4 border border-primary/20">
                  <p className="text-xs font-semibold uppercase tracking-wider text-primary mb-1.5">Mecânica da Promoção</p>
                  <p className="text-sm font-medium">{formatMechanic(selected.type, selected.mechanic_params)}</p>
                </div>

                {/* Audiência */}
                <div className="bg-muted/20 rounded-lg p-3 border border-border/40">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-2 flex items-center gap-1"><Users className="h-3 w-3"/>Audiência</p>
                  <p className="text-sm font-medium">{AUDIENCE_LABELS[selected.audience_type] ?? selected.audience_type}</p>
                  {selected.channel_ids && selected.channel_ids.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {selected.channel_ids.map(c => <Badge key={c} variant="outline" className="text-[10px]">{c}</Badge>)}
                    </div>
                  )}
                </div>

                <Separator />

                {/* Produtos */}
                {selected.products.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-sm mb-3 flex items-center gap-2"><Tag className="h-4 w-4 text-primary"/>Produtos</h4>
                    <div className="rounded border border-border overflow-hidden">
                      <table className="w-full text-xs">
                        <thead className="bg-muted/40">
                          <tr>
                            <th className="text-left px-3 py-2 font-semibold text-muted-foreground">Produto</th>
                            <th className="text-left px-3 py-2 font-semibold text-muted-foreground">Papel</th>
                            <th className="text-right px-3 py-2 font-semibold text-muted-foreground">Preço base</th>
                            <th className="text-right px-3 py-2 font-semibold text-muted-foreground">Preço promo</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selected.products.map((p, j) => (
                            <tr key={j} className="border-t border-border/40 hover:bg-muted/20">
                              <td className="px-3 py-2">
                                <p className="font-medium truncate max-w-[140px]" title={p.product_name}>{p.product_name}</p>
                                <p className="font-mono text-[10px] text-muted-foreground">{p.product_external_id}</p>
                              </td>
                              <td className="px-3 py-2">
                                <Badge variant="outline" className="text-[9px]">{p.role}</Badge>
                              </td>
                              <td className="px-3 py-2 text-right text-muted-foreground">{fmtMoney(p.base_price)}</td>
                              <td className="px-3 py-2 text-right font-bold text-primary">{fmtMoney(p.promo_price)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
        </SheetContent>
      </Sheet>
    </div>
  );
}
