import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import api from '@/api/recommendations/axios';

// ------------------------------------------------------------------ #
// Types
// ------------------------------------------------------------------ #

interface TenantConfig {
  price_threshold_low: number;
  price_threshold_high: number;
  similarity_threshold: number;
  recommendation_limit: number;
  recommendation_category_level: number;

  onetime_days_as_customer_min: number;
  onetime_p_alive_max: number;

  leaver_recency_min: number;
  leaver_p_alive_max: number;
  leaver_invoices_min: number;

  nonengaged_p_alive_max: number;
  nonengaged_recency_min: number;
  nonengaged_velocity_trend_max: number;

  loyalstar_regularity_max: number;
  loyalstar_velocity_trend_min: number;
  loyalstar_ticket_trend_min: number;
  loyalstar_category_diversity_min: number;
  loyalstar_p_alive_min: number;

  loyalrunner_regularity_max: number;
  loyalrunner_velocity_trend_min: number;
  loyalrunner_p_alive_min: number;

  config_suggestions: Record<string, number>;
  suggested_at: string | null;
}

const DEFAULTS: TenantConfig = {
  price_threshold_low: 0.9,
  price_threshold_high: 1.1,
  similarity_threshold: 0.7,
  recommendation_limit: 10,
  recommendation_category_level: 0,
  onetime_days_as_customer_min: 60,
  onetime_p_alive_max: 0.3,
  leaver_recency_min: 180,
  leaver_p_alive_max: 0.15,
  leaver_invoices_min: 3,
  nonengaged_p_alive_max: 0.2,
  nonengaged_recency_min: 180,
  nonengaged_velocity_trend_max: 0.3,
  loyalstar_regularity_max: 0.6,
  loyalstar_velocity_trend_min: 0.9,
  loyalstar_ticket_trend_min: 0.9,
  loyalstar_category_diversity_min: 3,
  loyalstar_p_alive_min: 0.7,
  loyalrunner_regularity_max: 0.8,
  loyalrunner_velocity_trend_min: 0.9,
  loyalrunner_p_alive_min: 0.5,
  config_suggestions: {},
  suggested_at: null,
};

// ------------------------------------------------------------------ #
// Field component
// ------------------------------------------------------------------ #

interface FieldProps {
  label: string;
  description: string;
  fieldKey: keyof TenantConfig;
  values: TenantConfig;
  onChange: (key: keyof TenantConfig, val: string) => void;
  type?: 'float' | 'int';
  min?: number;
  max?: number;
  step?: number;
  suggestion?: number;
  onApplySuggestion?: () => void;
}

function ConfigField({ label, description, fieldKey, values, onChange, type = 'float', min, max, step, suggestion, onApplySuggestion }: FieldProps) {
  return (
    <div className="grid gap-1.5">
      <div className="flex items-center gap-2">
        <Label htmlFor={fieldKey} className="font-medium">{label}</Label>
        {suggestion !== undefined && suggestion !== values[fieldKey] && (
          <button
            type="button"
            onClick={onApplySuggestion}
            className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors font-medium"
            title="Clique para aplicar sugestão"
          >
            sugerido: {suggestion}
          </button>
        )}
      </div>
      <p className="text-xs text-muted-foreground leading-snug">{description}</p>
      <Input
        id={fieldKey}
        type="number"
        step={step ?? (type === 'int' ? 1 : 0.05)}
        min={min}
        max={max}
        value={(values[fieldKey] as number) ?? ''}
        onChange={(e) => onChange(fieldKey, e.target.value)}
        className="w-40"
      />
    </div>
  );
}

// ------------------------------------------------------------------ #
// Block component
// ------------------------------------------------------------------ #

interface BlockProps {
  title: string;
  badge?: string;
  badgeColor?: string;
  description: string;
  children: React.ReactNode;
}

function ConfigBlock({ title, badge, badgeColor = 'bg-slate-100 text-slate-700', description, children }: BlockProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <CardTitle className="text-base">{title}</CardTitle>
          {badge && (
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeColor}`}>{badge}</span>
          )}
        </div>
        <CardDescription className="text-sm">{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {children}
        </div>
      </CardContent>
    </Card>
  );
}

// ------------------------------------------------------------------ #
// Main page
// ------------------------------------------------------------------ #

export function Config() {
  const [values, setValues] = useState<TenantConfig>(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/config/').then(r => {
      setValues({ ...DEFAULTS, ...r.data });
    }).catch(() => {
      setError('Não foi possível carregar as configurações.');
    }).finally(() => setLoading(false));
  }, []);

  function handleChange(key: keyof TenantConfig, raw: string) {
    const isInt = ['recommendation_limit', 'recommendation_category_level', 'onetime_days_as_customer_min', 'leaver_recency_min', 'leaver_invoices_min', 'nonengaged_recency_min', 'loyalstar_category_diversity_min'].includes(key);
    const parsed = isInt ? parseInt(raw, 10) : parseFloat(raw);
    if (!isNaN(parsed)) {
      setValues(prev => ({ ...prev, [key]: parsed }));
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await api.put('/config/', values);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      setError('Falha ao salvar. Verifique os valores e tente novamente.');
    } finally {
      setSaving(false);
    }
  }

  async function applySuggestions() {
    setSaving(true);
    setError(null);
    try {
      const r = await api.post('/config/apply-suggestions');
      setValues({ ...DEFAULTS, ...r.data });
      if (r.data.recalculating) {
        setRecalculating(true);
      } else {
        setSaved(true);
        setTimeout(() => setSaved(false), 2500);
      }
    } catch {
      setError('Falha ao aplicar sugestões.');
    } finally {
      setSaving(false);
    }
  }

  function applySingleSuggestion(key: keyof TenantConfig) {
    const suggested = values.config_suggestions[key as string];
    if (suggested !== undefined) {
      setValues(prev => {
        const { [key as string]: _removed, ...restSuggestions } = prev.config_suggestions;
        return { ...prev, [key]: suggested, config_suggestions: restSuggestions };
      });
    }
  }

  if (loading) {
    return <div className="p-6 text-muted-foreground text-sm">Carregando configurações...</div>;
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Configurações</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Parâmetros que controlam recomendações de IA e a classificação de segmentos de clientes.
        </p>
      </div>

      <Separator />

      {/* Banner de sugestões */}
      {Object.keys(values.config_suggestions).length > 0 && (
        <div className="flex items-start gap-3 p-4 rounded-lg border border-blue-200 bg-blue-50">
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-800">
              Sugestões disponíveis — analisamos sua base em {values.suggested_at ? new Date(values.suggested_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''}
            </p>
            <p className="text-xs text-blue-600 mt-0.5">
              {Object.keys(values.config_suggestions).length} parâmetros com valores sugeridos baseados na distribuição real da sua base. Revise abaixo e aplique os que fizer sentido.
            </p>
          </div>
          <Button
            size="sm"
            onClick={applySuggestions}
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 text-white shrink-0"
          >
            Aplicar todas
          </Button>
        </div>
      )}

      {/* ---- Bloco IA & Recomendações ---- */}
      <ConfigBlock
        title="IA & Recomendações"
        description="Controla como o motor de busca semântica filtra e retorna produtos similares ao usuário."
      >
        <ConfigField
          label="Similaridade mínima"
          description="Pontuação mínima de cosine similarity para um produto aparecer como recomendação. Valores mais altos = resultados mais precisos, porém menos opções."
          fieldKey="similarity_threshold"
          values={values}
          onChange={handleChange}
          min={0} max={1} step={0.05}
          suggestion={values.config_suggestions['similarity_threshold'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('similarity_threshold')}
        />
        <ConfigField
          label="Limite de recomendações"
          description="Número máximo de produtos retornados por busca/recomendação. Afeta performance e espaço na UI."
          fieldKey="recommendation_limit"
          values={values}
          onChange={handleChange}
          type="int"
          min={1} max={50}
          suggestion={values.config_suggestions['recommendation_limit'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('recommendation_limit')}
        />
        <ConfigField
          label="Variação de preço — mínimo"
          description="Fração do preço original abaixo da qual um produto não é exibido (ex: 0.9 = até 10% mais barato). Filtra itens muito abaixo do preço referência."
          fieldKey="price_threshold_low"
          values={values}
          onChange={handleChange}
          min={0.1} max={1} step={0.05}
          suggestion={values.config_suggestions['price_threshold_low'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('price_threshold_low')}
        />
        <ConfigField
          label="Variação de preço — máximo"
          description="Fração do preço original acima da qual um produto não é exibido (ex: 1.1 = até 10% mais caro). Filtra itens muito acima do preço referência."
          fieldKey="price_threshold_high"
          values={values}
          onChange={handleChange}
          min={1} max={3} step={0.05}
          suggestion={values.config_suggestions['price_threshold_high'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('price_threshold_high')}
        />
        <ConfigField
          label="Nível de categoria para recomendação"
          description="Restringe recomendações a produtos da mesma categoria até o nível escolhido. 0 = sem restrição (recomenda qualquer produto similar). 1 = mesma categoria raiz (ex: 'Alimentos'). 2 = segundo nível (ex: 'Alimentos > Bebidas'). 3+ = categorias mais específicas. Máx: 8."
          fieldKey="recommendation_category_level"
          values={values}
          onChange={handleChange}
          type="int"
          min={0} max={8} step={1}
        />
      </ConfigBlock>

      {/* ---- Bloco OneTime ---- */}
      <ConfigBlock
        title="Segmento: OneTime"
        badge="Comprou 1× e não voltou"
        badgeColor="bg-yellow-100 text-yellow-800"
        description="Cliente que fez apenas uma compra e, dado o tempo passado, tem baixa probabilidade de retornar. Diferente do Prospect (que nunca comprou) e do StuckInMiddle (que comprou mais mas parou)."
      >
        <ConfigField
          label="Tempo mínimo como cliente (dias)"
          description="Número de dias que o cliente precisa ter desde a criação para ser classificado como OneTime. Evita classificar clientes novos que simplesmente ainda não tiveram tempo de recomprar."
          fieldKey="onetime_days_as_customer_min"
          values={values}
          onChange={handleChange}
          type="int"
          min={1} max={365}
          suggestion={values.config_suggestions['onetime_days_as_customer_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('onetime_days_as_customer_min')}
        />
        <ConfigField
          label="P(Vivo) máximo"
          description="Probabilidade máxima de o cliente estar 'vivo' (BG/NBD) para ser OneTime. Se P(Vivo) for maior que esse valor, o cliente ainda pode recomprar e fica em outro segmento."
          fieldKey="onetime_p_alive_max"
          values={values}
          onChange={handleChange}
          min={0} max={1} step={0.05}
          suggestion={values.config_suggestions['onetime_p_alive_max'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('onetime_p_alive_max')}
        />
      </ConfigBlock>

      {/* ---- Bloco Leaver ---- */}
      <ConfigBlock
        title="Segmento: Leaver"
        badge="Churn confirmado"
        badgeColor="bg-rose-100 text-rose-700"
        description="Cliente que era ativo (3+ pedidos) mas sumiu completamente. Churn confirmado — diferente do NonEngaged que ainda pode ser recuperado."
      >
        <ConfigField
          label="Recência mínima (dias)"
          description="Número mínimo de dias desde o último pedido para considerar o cliente como Leaver."
          fieldKey="leaver_recency_min"
          values={values}
          onChange={handleChange}
          min={30} max={730} step={10}
          suggestion={values.config_suggestions['leaver_recency_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('leaver_recency_min')}
        />
        <ConfigField
          label="P(Vivo) máximo"
          description="Probabilidade máxima (BG/NBD) para classificar como Leaver. Deve ser menor que o threshold de NonEngaged — é o churn mais severo."
          fieldKey="leaver_p_alive_max"
          values={values}
          onChange={handleChange}
          min={0} max={1} step={0.05}
          suggestion={values.config_suggestions['leaver_p_alive_max'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('leaver_p_alive_max')}
        />
        <ConfigField
          label="Pedidos mínimos"
          description="Número mínimo de pedidos históricos para ser Leaver. Diferencia de OneTime (1 pedido). O cliente precisa ter tido atividade antes de abandonar."
          fieldKey="leaver_invoices_min"
          values={values}
          onChange={handleChange}
          min={2} max={20} step={1}
          suggestion={values.config_suggestions['leaver_invoices_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('leaver_invoices_min')}
        />
      </ConfigBlock>

      {/* ---- Bloco NonEngaged ---- */}
      <ConfigBlock
        title="Segmento: NonEngaged"
        badge="Em risco"
        badgeColor="bg-red-100 text-red-700"
        description="Cliente em risco de churn. Ainda compra esporadicamente, mas os sinais indicam desaceleração. Diferente do Leaver que já confirmou abandono."
      >
        <ConfigField
          label="P(Vivo) máximo"
          description="Se a probabilidade de o cliente estar vivo (BG/NBD) for menor que esse valor, ele é classificado como NonEngaged — independente de outros indicadores. É o sinal mais forte de churn."
          fieldKey="nonengaged_p_alive_max"
          values={values}
          onChange={handleChange}
          min={0} max={1} step={0.05}
          suggestion={values.config_suggestions['nonengaged_p_alive_max'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('nonengaged_p_alive_max')}
        />
        <ConfigField
          label="Recência mínima (dias)"
          description="Número mínimo de dias sem compra para considerar o cliente potencialmente inativo. Usado em conjunto com a queda de velocidade de compra."
          fieldKey="nonengaged_recency_min"
          values={values}
          onChange={handleChange}
          type="int"
          min={30} max={730}
          suggestion={values.config_suggestions['nonengaged_recency_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('nonengaged_recency_min')}
        />
        <ConfigField
          label="Queda de velocidade máxima"
          description="Razão entre pedidos nos últimos 90 dias e nos 90 dias anteriores. Se menor que esse valor com recência alta, o cliente é NonEngaged. Ex: 0.3 = caiu para menos de 30% do ritmo anterior."
          fieldKey="nonengaged_velocity_trend_max"
          values={values}
          onChange={handleChange}
          min={0} max={1} step={0.05}
          suggestion={values.config_suggestions['nonengaged_velocity_trend_max'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('nonengaged_velocity_trend_max')}
        />
      </ConfigBlock>

      {/* ---- Bloco LoyalStar ---- */}
      <ConfigBlock
        title="Segmento: LoyalStar"
        badge="Melhor cliente"
        badgeColor="bg-purple-100 text-purple-700"
        description="O cliente mais valioso: compra com regularidade, ticket alto (acima do p75 do tenant), tendência de crescimento, diversifica categorias e tem alta probabilidade de continuar comprando. Todos os critérios precisam ser atendidos."
      >
        <ConfigField
          label="Regularidade máxima (CoV)"
          description="Coeficiente de Variação dos intervalos entre compras (desvio / média). Quanto menor, mais regular. Ex: 0.6 = variação de até 60% é aceita. Valores altos indicam compras irregulares."
          fieldKey="loyalstar_regularity_max"
          values={values}
          onChange={handleChange}
          min={0} max={2} step={0.05}
          suggestion={values.config_suggestions['loyalstar_regularity_max'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('loyalstar_regularity_max')}
        />
        <ConfigField
          label="Velocidade mínima"
          description="Razão pedidos 90d / pedidos 90d anteriores. Garante que o cliente manteve ou acelerou o ritmo de compras. Ex: 0.9 = no mínimo 90% do ritmo anterior."
          fieldKey="loyalstar_velocity_trend_min"
          values={values}
          onChange={handleChange}
          min={0} max={3} step={0.05}
          suggestion={values.config_suggestions['loyalstar_velocity_trend_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('loyalstar_velocity_trend_min')}
        />
        <ConfigField
          label="Crescimento de ticket mínimo"
          description="Razão ticket médio 90d / ticket médio 90d anteriores. Garante que o valor por compra não caiu. Ex: 0.9 = ticket atual no mínimo 90% do anterior."
          fieldKey="loyalstar_ticket_trend_min"
          values={values}
          onChange={handleChange}
          min={0} max={3} step={0.05}
          suggestion={values.config_suggestions['loyalstar_ticket_trend_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('loyalstar_ticket_trend_min')}
        />
        <ConfigField
          label="Diversidade de categorias mínima"
          description="Número mínimo de categorias distintas que o cliente comprou. Clientes que diversificam são mais fiéis ao tenant e menos sensíveis a promoções de categoria única."
          fieldKey="loyalstar_category_diversity_min"
          values={values}
          onChange={handleChange}
          type="int"
          min={1} max={20}
          suggestion={values.config_suggestions['loyalstar_category_diversity_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('loyalstar_category_diversity_min')}
        />
        <ConfigField
          label="P(Vivo) mínimo"
          description="Probabilidade mínima (BG/NBD) de o cliente ainda estar ativo. LoyalStar exige um sinal forte de continuidade — clientes com P(Vivo) baixo vão para NonEngaged."
          fieldKey="loyalstar_p_alive_min"
          values={values}
          onChange={handleChange}
          min={0} max={1} step={0.05}
          suggestion={values.config_suggestions['loyalstar_p_alive_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('loyalstar_p_alive_min')}
        />
      </ConfigBlock>

      {/* ---- Bloco LoyalRunner ---- */}
      <ConfigBlock
        title="Segmento: LoyalRunner"
        badge="Bom cliente recorrente"
        badgeColor="bg-blue-100 text-blue-700"
        description="Cliente recorrente e estável, mas que não atinge todos os critérios premium do LoyalStar. Pode não diversificar categorias ou ter ticket médio mais baixo. Vale ação de upsell para mover para LoyalStar."
      >
        <ConfigField
          label="Regularidade máxima (CoV)"
          description="Coeficiente de Variação dos intervalos entre compras. LoyalRunner aceita mais variação que LoyalStar — compra com frequência razoável mas não necessariamente no mesmo ritmo."
          fieldKey="loyalrunner_regularity_max"
          values={values}
          onChange={handleChange}
          min={0} max={2} step={0.05}
          suggestion={values.config_suggestions['loyalrunner_regularity_max'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('loyalrunner_regularity_max')}
        />
        <ConfigField
          label="Velocidade mínima"
          description="Razão pedidos 90d / pedidos 90d anteriores. Garante que o cliente não está desacelerando fortemente. Ex: 0.9 = pelo menos 90% do ritmo anterior."
          fieldKey="loyalrunner_velocity_trend_min"
          values={values}
          onChange={handleChange}
          min={0} max={3} step={0.05}
          suggestion={values.config_suggestions['loyalrunner_velocity_trend_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('loyalrunner_velocity_trend_min')}
        />
        <ConfigField
          label="P(Vivo) mínimo"
          description="Probabilidade mínima (BG/NBD) de o cliente ainda estar ativo. Se P(Vivo) for menor, o cliente vai para NonEngaged mesmo que ainda compre às vezes."
          fieldKey="loyalrunner_p_alive_min"
          values={values}
          onChange={handleChange}
          min={0} max={1} step={0.05}
          suggestion={values.config_suggestions['loyalrunner_p_alive_min'] as number | undefined}
          onApplySuggestion={() => applySingleSuggestion('loyalrunner_p_alive_min')}
        />
      </ConfigBlock>

      {/* ---- Footer ---- */}
      <div className="flex items-center gap-4 pt-2">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Salvando...' : 'Salvar configurações'}
        </Button>
        {saved && <span className="text-sm text-green-600 font-medium">Salvo com sucesso!</span>}
        {recalculating && (
          <span className="text-sm text-blue-600 font-medium flex items-center gap-1.5">
            <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            Sugestões aplicadas — recalculando segmentos...
          </span>
        )}
        {error && <span className="text-sm text-red-500">{error}</span>}
      </div>

      <p className="text-xs text-muted-foreground pb-6">
        As alterações de segmentação terão efeito no próximo processamento do job de ciclo de vida.
      </p>
    </div>
  );
}
