import { useState, useRef } from 'react';
import {
  UploadCloud, FileText, AlertCircle, X, Loader2,
  Network, Store, Package, Users, Tag, Warehouse, Percent, ShoppingCart
} from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TEXTS } from '@/constants/pt-br';
import {
  uploadChannels, uploadStores, uploadProducts,
  uploadCustomers, uploadPrices, uploadStock, uploadOrders, uploadOffers,
  type BatchResult,
} from '@/api/recommendations/ingestion';

interface CardState {
  file: File | null;
  uploading: boolean;
  result: BatchResult | null;
  error: string | null;
  dragging: boolean;
}

type EntityKey = 'channels' | 'stores' | 'products' | 'customers' | 'prices' | 'stock' | 'orders' | 'offers';

interface EntityConfig {
  key: EntityKey;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  upload: (file: File) => Promise<BatchResult>;
}

const ENTITIES: EntityConfig[] = [
  {
    key: 'channels',
    label: TEXTS.CARGAS.CHANNELS,
    description: TEXTS.CARGAS.CHANNELS_DESC,
    icon: Network,
    upload: uploadChannels,
  },
  {
    key: 'stores',
    label: TEXTS.CARGAS.STORES,
    description: TEXTS.CARGAS.STORES_DESC,
    icon: Store,
    upload: uploadStores,
  },
  {
    key: 'products',
    label: TEXTS.CARGAS.PRODUCTS,
    description: TEXTS.CARGAS.PRODUCTS_DESC,
    icon: Package,
    upload: uploadProducts,
  },
  {
    key: 'customers',
    label: TEXTS.CARGAS.CUSTOMERS,
    description: TEXTS.CARGAS.CUSTOMERS_DESC,
    icon: Users,
    upload: uploadCustomers,
  },
  {
    key: 'prices',
    label: TEXTS.CARGAS.PRICES,
    description: TEXTS.CARGAS.PRICES_DESC,
    icon: Tag,
    upload: uploadPrices,
  },
  {
    key: 'stock',
    label: TEXTS.CARGAS.STOCK,
    description: TEXTS.CARGAS.STOCK_DESC,
    icon: Warehouse,
    upload: uploadStock,
  },
  {
    key: 'orders',
    label: TEXTS.CARGAS.ORDERS,
    description: TEXTS.CARGAS.ORDERS_DESC,
    icon: ShoppingCart,
    upload: uploadOrders,
  },
  {
    key: 'offers',
    label: TEXTS.CARGAS.OFFERS,
    description: TEXTS.CARGAS.OFFERS_DESC,
    icon: Percent,
    upload: uploadOffers,
  },
];

const initialCardState = (): CardState => ({
  file: null,
  uploading: false,
  result: null,
  error: null,
  dragging: false,
});

export function Cargas() {
  const [states, setStates] = useState<Record<EntityKey, CardState>>(
    () => Object.fromEntries(ENTITIES.map(e => [e.key, initialCardState()])) as Record<EntityKey, CardState>
  );
  const inputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const update = (key: EntityKey, patch: Partial<CardState>) =>
    setStates(prev => ({ ...prev, [key]: { ...prev[key], ...patch } }));

  const handleDrop = (key: EntityKey, e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) update(key, { file, error: null, result: null, dragging: false });
  };

  const handleFileSelect = (key: EntityKey, e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) update(key, { file: e.target.files[0], error: null, result: null });
    e.target.value = '';
  };

  const handleUpload = async (entity: EntityConfig) => {
    const { key, upload } = entity;
    const { file } = states[key];
    if (!file) return;

    update(key, { uploading: true, error: null });
    try {
      const result = await upload(file);
      update(key, { uploading: false, result, file: null });
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      let errorMsg = TEXTS.CARGAS.ERROR_MSG;
      if (typeof detail === 'string') {
        errorMsg = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        errorMsg = detail.map((e: any) => `${e.loc?.slice(1).join('.')}: ${e.msg}`).join(' | ');
      }
      update(key, { uploading: false, error: errorMsg });
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">{TEXTS.CARGAS.TITLE}</h1>
        <p className="text-muted-foreground mt-2">{TEXTS.CARGAS.SUBTITLE}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {ENTITIES.map(entity => {
          const { key, label, description, icon: Icon } = entity;
          const state = states[key];

          return (
            <Card key={key} className="flex flex-col">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 bg-primary/10 rounded-lg flex items-center justify-center shrink-0">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <CardTitle className="text-base">{label}</CardTitle>
                    <CardDescription className="text-xs mt-0.5 leading-snug">{description}</CardDescription>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="flex-1 flex flex-col gap-3">

                {/* Drop zone */}
                {!state.file && !state.result && (
                  <div
                    onClick={() => inputRefs.current[key]?.click()}
                    onDrop={(e) => handleDrop(key, e)}
                    onDragOver={(e) => { e.preventDefault(); update(key, { dragging: true }); }}
                    onDragLeave={() => update(key, { dragging: false })}
                    className={`border-2 border-dashed rounded-lg h-28 flex flex-col items-center justify-center cursor-pointer transition-all duration-200
                      ${state.dragging
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:border-primary/50 hover:bg-muted/50'
                      }`}
                  >
                    <UploadCloud className={`h-6 w-6 mb-1 ${state.dragging ? 'text-primary' : 'text-muted-foreground'}`} />
                    <p className="text-xs text-muted-foreground text-center px-4">{TEXTS.CARGAS.DROP_HINT}</p>
                    <input
                      ref={el => { inputRefs.current[key] = el; }}
                      type="file"
                      accept=".csv"
                      className="hidden"
                      onChange={(e) => handleFileSelect(key, e)}
                    />
                  </div>
                )}

                {/* Selected file */}
                {state.file && (
                  <div className="border border-border rounded-lg p-3 flex items-center justify-between bg-card">
                    <div className="flex items-center gap-3 min-w-0">
                      <FileText className="h-4 w-4 text-primary shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">{state.file.name}</p>
                        <p className="text-xs text-muted-foreground">{(state.file.size / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    {!state.uploading && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="shrink-0"
                        onClick={() => update(key, { file: null })}
                      >
                        <X className="h-4 w-4 text-muted-foreground" />
                      </Button>
                    )}
                  </div>
                )}

                {/* Result */}
                {state.result && (
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-1.5">
                      <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 hover:bg-green-100">
                        +{state.result.created} {TEXTS.CARGAS.CREATED}
                      </Badge>
                      <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 hover:bg-blue-100">
                        ~{state.result.updated} {TEXTS.CARGAS.UPDATED}
                      </Badge>
                      <Badge variant="secondary">
                        ={state.result.unchanged} {TEXTS.CARGAS.UNCHANGED}
                      </Badge>
                      {state.result.errors.length > 0 && (
                        <Badge variant="destructive">
                          {state.result.errors.length} {TEXTS.CARGAS.ERRORS}
                        </Badge>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs h-7 px-2 text-muted-foreground"
                      onClick={() => update(key, { result: null })}
                    >
                      {TEXTS.CARGAS.SEND_ANOTHER}
                    </Button>
                  </div>
                )}

                {/* Error */}
                {state.error && (
                  <div className="flex items-start gap-2 text-destructive bg-destructive/10 rounded-lg p-3">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                    <p className="text-xs">{state.error}</p>
                  </div>
                )}

                {/* Actions */}
                {state.file && !state.uploading && (
                  <Button size="sm" className="mt-auto" onClick={() => handleUpload(entity)}>
                    {TEXTS.CARGAS.BTN_PROCESS}
                  </Button>
                )}
                {state.uploading && (
                  <Button size="sm" disabled className="mt-auto">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {TEXTS.CARGAS.PROCESSING}
                  </Button>
                )}

              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
