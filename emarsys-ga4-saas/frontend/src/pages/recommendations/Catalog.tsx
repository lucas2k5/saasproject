import { useEffect, useState, useRef } from 'react';
import { Search, ShoppingBag, Sparkles, TrendingUp, TrendingDown, Tag, Loader2, Filter, X, ChevronRight, ChevronDown, Folder, FolderOpen, Hash, Barcode, DollarSign, Package, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { TEXTS } from '@/constants/pt-br';
import {
  productService,
  type Product,
  type ProductDetail,
  type RecommendationResponse,
  type RecommendationItem,
  type CategoryNode,
  type ProductPricesStock,
} from '@/api/recommendations/products';
import api from '@/api/recommendations/axios';

// --- COMPONENTE DE ÁRVORE (Mantido igual) ---
const CategoryTreeItem = ({ node, level = 0, selectedCategory, onSelect }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  const hasChildren = node.children && node.children.length > 0;
  useEffect(() => {
    if (selectedCategory && selectedCategory.startsWith(node.value)) setIsOpen(true);
  }, [selectedCategory, node.value]);
  const isSelected = selectedCategory === node.value;
  const handleToggle = (e: React.MouseEvent) => { e.stopPropagation(); setIsOpen(!isOpen); };
  const handleClick = (e: React.MouseEvent) => { e.stopPropagation(); onSelect(node.value); if (!isOpen) setIsOpen(true); };
  return (
    <div className="select-none">
      <div className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors text-sm ${isSelected ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}`} style={{ paddingLeft: `${level * 12 + 8}px` }} onClick={handleClick}>
        {hasChildren ? (<button onClick={handleToggle} className="p-0.5 hover:bg-muted rounded text-muted-foreground/70">{isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}</button>) : (<span className="w-4" />)}
        {isOpen ? <FolderOpen className="h-3.5 w-3.5 opacity-70" /> : <Folder className="h-3.5 w-3.5 opacity-70" />}
        <span className="truncate">{node.label}</span>
      </div>
      {isOpen && hasChildren && (<div className="mt-0.5 border-l border-border/40 ml-4">{node.children.map((child: any) => (<CategoryTreeItem key={child.value} node={child} level={level + 1} selectedCategory={selectedCategory} onSelect={onSelect} />))}</div>)}
    </div>
  );
};

// --- NOVO: COMPONENTE CARD DA LISTA PRINCIPAL (COM PROTEÇÃO DE IMAGEM) ---
const ProductCard = ({ product, onClick }: { product: Product; onClick: (p: Product) => void }) => {
    const [imgError, setImgError] = useState(false);

    return (
        <Card 
            className="group cursor-pointer hover:shadow-xl hover:border-primary/40 transition-all duration-300 border-border overflow-hidden bg-card flex flex-col h-full"
            onClick={() => onClick(product)}
        >
            <CardHeader className="p-0">
                <div className="h-60 w-full bg-muted/30 flex items-center justify-center overflow-hidden relative p-4">
                    {/* Lógica de Imagem Robusta */}
                    {!imgError && product.image_url ? (
                        <img 
                            src={product.image_url} 
                            alt={product.name} 
                            className="h-full w-full object-contain transition-transform duration-500 group-hover:scale-110 drop-shadow-sm"
                            onError={() => setImgError(true)} 
                        />
                    ) : (
                        // Fallback bonito
                        <ShoppingBag className="h-16 w-16 text-muted-foreground/20 group-hover:text-primary/30 transition-colors" />
                    )}
                </div>
            </CardHeader>
            <CardContent className="p-5 flex-1 flex flex-col">
                <div className="mb-2">
                    <Badge variant="outline" className="text-[10px] truncate max-w-full bg-background/50">{product.category}</Badge>
                </div>
                
                <CardTitle className="text-base font-medium line-clamp-2 mb-2 leading-snug group-hover:text-primary transition-colors" title={product.name}>
                    {product.name}
                </CardTitle>
                
                {product.external_id && (
                    <p className="text-[10px] text-muted-foreground flex items-center gap-1.5 mb-3 font-mono bg-muted/30 w-fit px-1.5 py-0.5 rounded">
                        <Barcode className="h-3 w-3 opacity-70"/> {product.external_id}
                    </p>
                )}

                <div className="mt-auto pt-2 border-t border-border/40">
                    <div className="font-bold text-xl text-primary">
                        {TEXTS.CATALOG.PRICE_PREFIX}{product.price.toFixed(2)}
                    </div>
                </div>
            </CardContent>
            <CardFooter className="p-4 pt-0">
                <Button size="sm" variant="secondary" className="w-full text-xs font-semibold group-hover:bg-primary group-hover:text-primary-foreground transition-all">
                    Ver Detalhes
                </Button>
            </CardFooter>
        </Card>
    );
};

// --- COMPONENTE CARD DE RECOMENDAÇÃO (MANTIDO) ---
const RecommendationCard = ({ rec, onClick }: { rec: RecommendationItem; onClick: (p: Product) => void }) => {
    if (!rec || !rec.product) return null;
    const [imgError, setImgError] = useState(false);

    return (
      <div 
          className="flex-shrink-0 w-44 p-3 rounded-lg border border-border bg-card hover:shadow-md transition-all cursor-pointer group flex flex-col h-full select-none"
          onClick={() => onClick(rec.product)} 
      >
        <div className="relative aspect-square w-full bg-muted/30 rounded-md overflow-hidden mb-3 flex items-center justify-center p-2">
          {!imgError && rec.product.image_url ? (
             <img 
                src={rec.product.image_url}
                className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300"
                alt={rec.product.name}
                onError={() => setImgError(true)} 
            />
          ) : (
            <ShoppingBag className="h-8 w-8 text-muted-foreground/30" />
          )}
          <Badge className="absolute top-2 right-2 text-[10px] px-1.5 h-5 bg-black/70 hover:bg-black/80 backdrop-blur-md border-0 text-white font-mono shadow-sm">
              {(rec.score * 100).toFixed(0)}%
          </Badge>
        </div>
        <div className="space-y-1 flex-1 flex flex-col">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground line-clamp-1">{rec.product.category}</p>
          <h4 className="font-medium text-sm leading-tight line-clamp-2 min-h-[2.5rem] mb-1 group-hover:text-primary transition-colors" title={rec.product.name}>{rec.product.name}</h4>
          <div className="mt-auto pt-2">
            <p className="font-bold text-sm text-primary">{TEXTS.CATALOG.PRICE_PREFIX}{rec.product.price?.toFixed(2)}</p>
          </div>
        </div>
      </div>
    );
};

export function Catalog() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<CategoryNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [skip, setSkip] = useState(0);
  const LIMIT = 100;
  const observerTarget = useRef<HTMLDivElement>(null);
  const [selectedProduct, setSelectedProduct] = useState<ProductDetail | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [pricesStock, setPricesStock] = useState<ProductPricesStock | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [reindexPending, setReindexPending] = useState<number | null>(null);
  const [reindexDone, setReindexDone] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => { loadCategories(); }, []);
  async function loadCategories() {
    try { const cats = await productService.getCategoryTree(); setCategories(cats); } 
    catch (error) { console.error("Erro ao carregar categorias:", error); }
  }

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => { searchTerm ? performSearch(searchTerm) : resetToList(); }, 500);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, selectedCategory]);

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasMore && !loading && !searchTerm) {
          const nextSkip = skip + LIMIT;
          setSkip(nextSkip);
          loadMoreProducts(nextSkip, false);
        }
      }, { threshold: 1.0 });
    if (observerTarget.current) observer.observe(observerTarget.current);
    return () => observer.disconnect();
  }, [hasMore, loading, skip, searchTerm, selectedCategory]);

  function resetToList() { setSkip(0); setHasMore(true); setProducts([]); loadMoreProducts(0, true); }
  async function loadMoreProducts(skipVal: number, isInitial: boolean) {
    if (isInitial) setLoading(true);
    try {
      const newProducts = await productService.getProducts(skipVal, LIMIT, undefined, selectedCategory || undefined);
      if (newProducts.length < LIMIT) setHasMore(false);
      setProducts(prev => isInitial ? newProducts : [...prev, ...newProducts]);
    } catch (error) { console.error("Erro ao listar:", error); } finally { setLoading(false); }
  }
  async function performSearch(query: string) {
    setLoading(true); setHasMore(false); setSelectedCategory(null);
    try { const results = await productService.searchProducts(query, 50); setProducts(results); } 
    catch (error) { console.error(error); } finally { setLoading(false); }
  }

  async function handleProductClick(productSummary: Product) {
    setSelectedProduct({ ...productSummary, attributes: {} });
    setLoadingDetails(true);
    setRecommendations(null);
    setPricesStock(null);
    try {
      const recId = productSummary.external_id || productSummary.id;
      const [detailsData, recsData, psData] = await Promise.all([
        productService.getProductDetail(recId),
        productService.getRecommendations(recId),
        productService.getProductPricesStock(recId),
      ]);
      setSelectedProduct(detailsData);
      setRecommendations(recsData);
      setPricesStock(psData);
    } catch (error) { console.error(error); } finally { setLoadingDetails(false); }
  }

  function stopPolling() {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }

  function startPolling() {
    pollingRef.current = setInterval(async () => {
      try {
        const r = await api.get('/products/reindex/status');
        setReindexPending(r.data.pending);
        if (!r.data.running) {
          stopPolling();
          setReindexPending(null);
          setReindexDone(true);
          setTimeout(() => setReindexDone(false), 3000);
        }
      } catch {
        stopPolling();
        setReindexPending(null);
      }
    }, 10000);
  }

  async function handleReindex() {
    setReindexing(true);
    setReindexDone(false);
    try {
      await api.post('/products/reindex');
      setReindexPending(0);
      startPolling();
    } catch (error) {
      console.error('Erro ao reindexar:', error);
    } finally {
      setReindexing(false);
    }
  }

  useEffect(() => () => stopPolling(), []);

  const CarouselSection = ({ title, icon: Icon, items }: { title: string, icon: any, items: RecommendationItem[] }) => {
    if (!items || items.length === 0) return null;
    return (
        <div className="mb-6 last:mb-0">
            <h4 className="font-semibold mb-3 flex items-center gap-2 text-sm text-foreground">
                <Icon className="h-4 w-4 text-primary"/> {title}
            </h4>
            <div className="flex gap-3 overflow-x-auto pb-4 -mx-2 px-2 scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent">
                {items.map((r, i) => <RecommendationCard key={i} rec={r} onClick={handleProductClick} />)}
            </div>
        </div>
    );
  };

  return (
    <div className="animate-in fade-in duration-500 pb-10 h-full">
      <div className="sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border/40 py-4 px-6 md:px-8 -mx-6 md:-mx-8 mb-6 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
        <div><h1 className="text-2xl font-bold tracking-tight text-foreground">{TEXTS.CATALOG.TITLE}</h1><p className="text-sm text-muted-foreground">{TEXTS.CATALOG.SUBTITLE}</p></div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-80"><Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" /><Input placeholder={TEXTS.CATALOG.SEARCH_PLACEHOLDER} className="pl-9 bg-muted/50 focus-visible:ring-primary border-border" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} /></div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleReindex}
            disabled={reindexing || reindexPending !== null}
            title="Re-enriquece todos os produtos com IA e atualiza os índices de busca no Qdrant"
            className={
              reindexDone ? 'border-green-500 text-green-600' :
              reindexPending !== null ? 'border-amber-400 text-amber-600' : ''
            }
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${reindexing || reindexPending !== null ? 'animate-spin' : ''}`} />
            {reindexing ? 'Enviando...' :
             reindexDone ? 'Concluído!' :
             reindexPending !== null ? `Processando... (${reindexPending} restantes)` :
             'Reindexar IA'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          <div className="hidden md:block col-span-3 sticky top-32">
            <div className="space-y-3">
                <div className="flex items-center justify-between px-2"><h3 className="font-semibold text-sm flex items-center gap-2 text-foreground"><Filter className="h-4 w-4" /> Navegação</h3>{selectedCategory && (<Button variant="ghost" size="sm" onClick={() => setSelectedCategory(null)} className="h-6 text-[10px] px-2 text-muted-foreground hover:text-destructive uppercase tracking-wider">Limpar</Button>)}</div>
                <ScrollArea className="h-[calc(100vh-250px)]"><div className="space-y-0.5 pb-4">{categories.map((node) => (<CategoryTreeItem key={node.value} node={node} selectedCategory={selectedCategory} onSelect={(val: string) => { if (selectedCategory === val) setSelectedCategory(null); else setSelectedCategory(val); setSearchTerm(''); }} />))}</div></ScrollArea>
            </div>
          </div>

          <div className="col-span-1 md:col-span-9 space-y-6">
            {selectedCategory && (<div className="flex items-center gap-2 mb-4"><span className="text-sm text-muted-foreground">Filtrando por:</span><Badge variant="secondary" className="pl-2 pr-1 py-1 flex items-center gap-1 bg-primary/10 text-primary border-primary/20">{selectedCategory}<Button variant="ghost" size="icon" className="h-4 w-4 rounded-full hover:bg-primary/20 p-0" onClick={() => setSelectedCategory(null)}><X className="h-3 w-3" /></Button></Badge></div>)}
            {loading && products.length === 0 ? (<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">{[1,2,3,4,5,6].map(i => <Skeleton key={i} className="h-72 w-full rounded-xl" />)}</div>) : products.length === 0 ? (<div className="flex flex-col items-center justify-center py-20 bg-muted/10 rounded-xl border border-dashed border-border text-center"><ShoppingBag className="h-12 w-12 text-muted-foreground mb-4" /><h3 className="text-lg font-semibold">{TEXTS.CATALOG.EMPTY_STATE}</h3><p className="text-sm text-muted-foreground">Tente limpar os filtros.</p></div>) : (
                <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {/* USO DO NOVO COMPONENTE PRODUCTCARD */}
                        {products.map((product) => (
                            <ProductCard 
                                key={product.id} 
                                product={product} 
                                onClick={handleProductClick} 
                            />
                        ))}
                    </div>
                    {hasMore && !searchTerm && (<div ref={observerTarget} className="flex justify-center py-8 w-full"><div className="flex items-center gap-2 text-muted-foreground bg-muted/30 px-4 py-2 rounded-full text-sm"><Loader2 className="h-4 w-4 animate-spin text-primary" /> Carregando mais...</div></div>)}
                </>
            )}
          </div>
      </div>

      <Sheet open={!!selectedProduct} onOpenChange={(open) => !open && setSelectedProduct(null)}>
        <SheetContent className="w-[95vw] sm:max-w-4xl overflow-y-auto border-l-border bg-background p-0 gap-0 shadow-2xl">
            {selectedProduct && (
               <div className="p-6 space-y-6">
                 <SheetHeader>
                    <SheetTitle className="text-xl font-bold text-foreground">{selectedProduct.name}</SheetTitle>
                    <SheetDescription asChild>
                       <div className="text-sm text-muted-foreground flex flex-col gap-1">
                          <span>{Array.isArray(selectedProduct.category) ? selectedProduct.category.join(' > ') : selectedProduct.category}</span>
                       </div>
                    </SheetDescription>
                    <div className="flex flex-wrap gap-2 mt-1">
                        <Badge variant="outline" className="font-mono text-[10px] flex items-center gap-1"><Hash className="h-3 w-3"/> ID: {selectedProduct.id}</Badge>
                        {selectedProduct.external_id && (<Badge variant="outline" className="font-mono text-[10px] flex items-center gap-1"><Barcode className="h-3 w-3"/> SKU: {selectedProduct.external_id}</Badge>)}
                    </div>
                 </SheetHeader>
                 
                 <div className="flex gap-6 items-start">
                    <div className="h-32 w-32 bg-muted/20 rounded-xl overflow-hidden shrink-0 border border-border flex items-center justify-center">
                         {/* IMAGEM DO DETALHE TAMBÉM PODE USAR A LOGICA, VAMOS SIMPLIFICAR AQUI COM UM FALLBACK DIRETO */}
                         {selectedProduct.image_url ? (
                             <img src={selectedProduct.image_url} className="w-full h-full object-contain p-2" onError={(e) => { e.currentTarget.style.display='none'; e.currentTarget.parentElement?.classList.add('fallback-active') }} />
                         ) : <ShoppingBag className="h-10 w-10 text-muted-foreground/30"/>}
                    </div>
                    <div className="flex-1">
                        <h3 className="font-bold text-xl">{selectedProduct.name}</h3>
                        <p className="font-bold text-primary text-2xl mt-2">{TEXTS.CATALOG.PRICE_PREFIX}{selectedProduct.price.toFixed(2)}</p>
                    </div>
                 </div>

                 <div className="text-sm text-muted-foreground bg-muted/10 p-4 rounded border border-border/30">
                    <p className="font-semibold text-xs text-foreground mb-1 uppercase tracking-wider">Descrição</p>
                    {selectedProduct.description || "Sem descrição."}
                 </div>

                 {selectedProduct.enriched_text && (
                   <div className="text-sm text-muted-foreground bg-primary/5 p-4 rounded border border-primary/20">
                     <p className="font-semibold text-xs text-primary mb-1 uppercase tracking-wider flex items-center gap-1.5">
                       <Sparkles className="h-3 w-3"/> Contexto gerado por IA
                     </p>
                     {selectedProduct.enriched_text}
                   </div>
                 )}

                 <div className="bg-muted/30 p-4 rounded border border-border/50">
                    <h4 className="font-semibold text-sm mb-3 flex items-center gap-2"><Tag className="h-4 w-4"/> Especificações Técnicas</h4>
                    {loadingDetails ? (
                        <div className="grid grid-cols-2 gap-4"><Skeleton className="h-4 w-24 mb-1" /><Skeleton className="h-4 w-32" /><Skeleton className="h-4 w-20 mb-1" /><Skeleton className="h-4 w-28" /></div>
                    ) : (
                        selectedProduct.attributes && Object.keys(selectedProduct.attributes).length > 0 ? (
                            <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                                {Object.entries(selectedProduct.attributes).map(([k,v]) => (
                                    <div key={k} className="overflow-hidden"><span className="text-[10px] uppercase font-bold text-muted-foreground block mb-0.5">{k}</span><p className="text-sm font-medium text-foreground break-words whitespace-normal">{String(v)}</p></div>
                                ))}
                            </div>
                        ) : (<p className="text-xs text-muted-foreground italic">Nenhum atributo adicional.</p>)
                    )}
                 </div>
                 
                 <Separator/>

                 {/* PREÇOS */}
                 <div>
                   <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                     <DollarSign className="h-4 w-4 text-primary"/> {TEXTS.CATALOG_DETAIL.PRICES_TITLE}
                   </h4>
                   {loadingDetails ? (
                     <Skeleton className="h-20 w-full rounded" />
                   ) : pricesStock && pricesStock.prices.length > 0 ? (
                     <div className="rounded border border-border overflow-hidden">
                       <table className="w-full text-sm">
                         <thead className="bg-muted/40">
                           <tr>
                             <th className="text-left px-3 py-2 text-xs font-semibold text-muted-foreground">{TEXTS.CATALOG_DETAIL.COL_CHANNEL}</th>
                             <th className="text-left px-3 py-2 text-xs font-semibold text-muted-foreground">{TEXTS.CATALOG_DETAIL.COL_STORE}</th>
                             <th className="text-right px-3 py-2 text-xs font-semibold text-muted-foreground">{TEXTS.CATALOG_DETAIL.COL_PRICE}</th>
                           </tr>
                         </thead>
                         <tbody>
                           {pricesStock.prices.map((p, i) => (
                             <tr key={i} className="border-t border-border/40 hover:bg-muted/20 transition-colors">
                               <td className="px-3 py-2 text-xs">{p.channel_name}</td>
                               <td className="px-3 py-2 text-xs text-muted-foreground">{p.store_name}</td>
                               <td className="px-3 py-2 text-xs font-bold text-primary text-right">R$ {p.price.toFixed(2)}</td>
                             </tr>
                           ))}
                         </tbody>
                       </table>
                     </div>
                   ) : (
                     <p className="text-xs text-muted-foreground italic">{TEXTS.CATALOG_DETAIL.EMPTY_PRICES}</p>
                   )}
                 </div>

                 {/* ESTOQUE */}
                 <div>
                   <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                     <Package className="h-4 w-4 text-primary"/> {TEXTS.CATALOG_DETAIL.STOCK_TITLE}
                   </h4>
                   {loadingDetails ? (
                     <Skeleton className="h-20 w-full rounded" />
                   ) : pricesStock && pricesStock.stock.length > 0 ? (
                     <div className="rounded border border-border overflow-hidden">
                       <table className="w-full text-sm">
                         <thead className="bg-muted/40">
                           <tr>
                             <th className="text-left px-3 py-2 text-xs font-semibold text-muted-foreground">{TEXTS.CATALOG_DETAIL.COL_CHANNEL}</th>
                             <th className="text-left px-3 py-2 text-xs font-semibold text-muted-foreground">{TEXTS.CATALOG_DETAIL.COL_STORE}</th>
                             <th className="text-right px-3 py-2 text-xs font-semibold text-muted-foreground">{TEXTS.CATALOG_DETAIL.COL_QTY}</th>
                             <th className="text-center px-3 py-2 text-xs font-semibold text-muted-foreground">{TEXTS.CATALOG_DETAIL.COL_AVAILABLE}</th>
                           </tr>
                         </thead>
                         <tbody>
                           {pricesStock.stock.map((s, i) => (
                             <tr key={i} className="border-t border-border/40 hover:bg-muted/20 transition-colors">
                               <td className="px-3 py-2 text-xs">{s.channel_name}</td>
                               <td className="px-3 py-2 text-xs text-muted-foreground">{s.store_name}</td>
                               <td className="px-3 py-2 text-xs font-medium text-right">{s.quantity.toLocaleString()}</td>
                               <td className="px-3 py-2 text-center">
                                 {s.available
                                   ? <CheckCircle className="h-4 w-4 text-green-500 mx-auto" />
                                   : <XCircle className="h-4 w-4 text-red-400 mx-auto" />}
                               </td>
                             </tr>
                           ))}
                         </tbody>
                       </table>
                     </div>
                   ) : (
                     <p className="text-xs text-muted-foreground italic">{TEXTS.CATALOG_DETAIL.EMPTY_STOCK}</p>
                   )}
                 </div>

                 <Separator/>

                 <div>
                    <h4 className="font-bold text-lg mb-4 flex items-center gap-2"><Sparkles className="h-5 w-5 text-primary"/> Recomendações</h4>

                    <div className="space-y-6">
                      {/* Análise de Similaridade */}
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
                          <Sparkles className="h-3 w-3"/> {TEXTS.CATALOG.DRAWER_TITLE}
                        </p>
                        {loadingDetails ? <Skeleton className="h-40 w-full rounded-xl"/> : (
                          <div className="space-y-4">
                            <CarouselSection title="Opções Mais Econômicas" icon={TrendingDown} items={recommendations?.cheaper || []} />
                            <CarouselSection title="Similares / Equivalentes" icon={Sparkles} items={recommendations?.equivalent || []} />
                            <CarouselSection title="Opções Premium" icon={TrendingUp} items={recommendations?.expensive || []} />
                            {!recommendations?.cheaper?.length && !recommendations?.equivalent?.length && !recommendations?.expensive?.length && (
                              <p className="text-muted-foreground text-center py-8 border border-dashed rounded-lg bg-muted/10">Nenhuma recomendação similar encontrada.</p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                 </div>
               </div>
            )}
        </SheetContent>
      </Sheet>
    </div>
  );
}