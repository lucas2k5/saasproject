import api from './axios';

// ---- CSV Parser ----

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  result.push(current);
  return result;
}

function parseCSV(text: string): Record<string, string>[] {
  // Normaliza CRLF e CR solto para LF antes de dividir
  const normalized = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  const lines = normalized.split('\n').filter(l => l.trim());
  if (lines.length < 2) return [];
  const headers = parseCSVLine(lines[0]).map(h => h.trim());
  return lines.slice(1).map(line => {
    const values = parseCSVLine(line);
    const obj: Record<string, string> = {};
    headers.forEach((h, i) => { obj[h] = values[i] ?? ''; });
    return obj;
  });
}

// ---- Helpers ----

function chunkArray<T>(arr: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size));
  }
  return chunks;
}

export interface BatchResult {
  created: number;
  updated: number;
  unchanged: number;
  errors: any[];
}

function emptyResult(): BatchResult {
  return { created: 0, updated: 0, unchanged: 0, errors: [] };
}

function mergeResults(a: BatchResult, b: any): BatchResult {
  return {
    created: a.created + (b.created ?? 0),
    updated: a.updated + (b.updated ?? 0),
    unchanged: a.unchanged + (b.unchanged ?? 0),
    errors: [...a.errors, ...(b.errors ?? [])],
  };
}

async function sendChunked(
  endpoint: string,
  items: any[],
  chunkSize = 1000
): Promise<BatchResult> {
  let result = emptyResult();
  for (const ch of chunkArray(items, chunkSize)) {
    const resp = await api.post(endpoint, ch);
    result = mergeResults(result, resp.data);
  }
  return result;
}

// ---- Channels ----

export async function uploadChannels(file: File): Promise<BatchResult> {
  const text = await file.text();
  const rows = parseCSV(text);
  const items = rows
    .filter(r => r.channel_id && r.name)
    .map(r => {
      let stores: { store_id: string; name: string }[] = [];
      try { stores = JSON.parse(r.stores || '[]'); } catch { stores = []; }
      return {
        channel_id: r.channel_id,
        name: r.name,
        type: r.type,
        store_mode: r.store_mode,
        stores,
      };
    });
  return sendChunked('/channels/batch', items);
}

// ---- Stores ----

export async function uploadStores(file: File): Promise<BatchResult> {
  const text = await file.text();
  const rows = parseCSV(text);
  const items = rows
    .filter(r => r.store_id && r.name)
    .map(r => ({ store_id: r.store_id, name: r.name }));
  return sendChunked('/stores/batch', items);
}

// ---- Products ----

export async function uploadProducts(file: File): Promise<BatchResult> {
  const text = await file.text();
  const rows = parseCSV(text);
  const items = rows
    .filter(r => r.external_id && r.name)
    .map(r => {
      let category: string[] = [];
      let attributes: Record<string, any> = {};
      try { category = JSON.parse(r.category || '[]'); } catch {
        category = r.category ? r.category.split('|').map(s => s.trim()).filter(Boolean) : [];
      }
      try { attributes = JSON.parse(r.attributes || '{}'); } catch { attributes = {}; }
      return {
        external_id: r.external_id,
        name: r.name,
        price: parseFloat(r.price) || 0,
        description: r.description || '',
        image_url: r.image_url || '',
        category,
        attributes,
      };
    });

  let result = emptyResult();
  for (const ch of chunkArray(items, 1000)) {
    const resp = await api.post('/products/batch', { items: ch });
    result = mergeResults(result, resp.data);
  }
  return result;
}

// ---- Customers ----

export async function uploadCustomers(file: File): Promise<BatchResult> {
  const text = await file.text();
  const rows = parseCSV(text);
  const items = rows
    .filter(r => r.customer_id && r.name)
    .map(r => ({
      customer_id: r.customer_id,
      customer_add_id: r.customer_add_id || null,
      name: r.name,
      document: r.document || null,
      customer_type: r.customer_type || null,
    }));
  return sendChunked('/customers/batch', items);
}

// ---- Prices ----

export async function uploadPrices(file: File): Promise<BatchResult> {
  const text = await file.text();
  const rows = parseCSV(text);
  const items = rows
    .filter(r => r.product_external_id && r.channel_id && r.store_id)
    .map(r => ({
      product_external_id: r.product_external_id,
      channel_id: r.channel_id,
      store_id: r.store_id,
      price: parseFloat(r.price) || 0,
    }));
  return sendChunked('/prices/batch', items);
}

// ---- Orders ----

export async function uploadOrders(file: File): Promise<BatchResult> {
  const text = await file.text();
  const rows = parseCSV(text);
  const items = rows
    .filter(r => r.order_id && r.customer_ref && r.product_external_id && r.ordered_at)
    .map(r => ({
      order_id: r.order_id,
      customer_ref: r.customer_ref,
      channel_id: r.channel_id || null,
      store_id: r.store_id || null,
      status: r.status || 'delivered',
      ordered_at: r.ordered_at,
      gross_value: parseFloat(r.gross_value) || 0,
      discount_value: parseFloat(r.discount_value) || 0,
      tax_value: parseFloat(r.tax_value) || 0,
      net_value: parseFloat(r.net_value) || 0,
      product_external_id: r.product_external_id,
      quantity: parseInt(r.quantity) || 1,
      unit_price: parseFloat(r.unit_price) || 0,
      discount_amount: parseFloat(r.discount_amount) || 0,
      tax_amount: parseFloat(r.tax_amount) || 0,
      net_price: parseFloat(r.net_price) || 0,
      is_promo: ['true', 'True', '1'].includes(r.is_promo),
    }));

  let result = emptyResult();
  for (const chunk of chunkArray(items, 1000)) {
    const resp = await api.post('/orders/batch', chunk);
    const d = resp.data;
    result = {
      created: result.created + (d.orders_created ?? 0),
      updated: result.updated + (d.orders_updated ?? 0),
      unchanged: result.unchanged,
      errors: [...result.errors, ...(d.errors ?? [])],
    };
  }
  return result;
}

// ---- Offers ----

export async function uploadOffers(file: File): Promise<BatchResult> {
  const text = await file.text();
  const rows = parseCSV(text);

  const items = rows
    .filter(r => r.offer_id && r.name && r.type && r.end_at)
    .map(r => {
      let mechanic_params: Record<string, any> = {};
      let trigger_products: string[] = [];
      let reward_products: string[] = [];
      let channel_ids: string[] = [];
      let store_ids: string[] = [];
      let audience_value: string[] = [];

      try { mechanic_params = JSON.parse(r.mechanic_params || '{}'); } catch { mechanic_params = {}; }
      trigger_products = r.trigger_products ? r.trigger_products.split('|').map(s => s.trim()).filter(Boolean) : [];
      reward_products = r.reward_products ? r.reward_products.split('|').map(s => s.trim()).filter(Boolean) : [];
      channel_ids = r.channel_ids ? r.channel_ids.split('|').map(s => s.trim()).filter(Boolean) : [];
      store_ids = r.store_ids ? r.store_ids.split('|').map(s => s.trim()).filter(Boolean) : [];
      audience_value = r.audience_value ? r.audience_value.split('|').map(s => s.trim()).filter(Boolean) : [];

      return {
        offer_id: r.offer_id,
        name: r.name,
        type: r.type,
        mechanic_params,
        trigger_products,
        reward_products,
        start_at: r.start_at || new Date().toISOString(),
        end_at: r.end_at,
        channel_ids,
        store_ids,
        audience_type: r.audience_type || 'ALL',
        audience_value,
        priority: parseInt(r.priority) || 0,
      };
    });

  if (items.length === 0) {
    return { created: 0, updated: 0, unchanged: 0, errors: ['Nenhuma oferta válida encontrada no CSV.'] };
  }

  // Ofertas: POST único (full replace) — sem chunking
  const resp = await api.post('/offers/batch', items);
  const data = resp.data;
  return {
    created: data.inserted ?? 0,
    updated: 0,
    unchanged: 0,
    errors: data.errors ?? [],
  };
}

// ---- Stock ----

export async function uploadStock(file: File): Promise<BatchResult> {
  const text = await file.text();
  const rows = parseCSV(text);
  const items = rows
    .filter(r => r.product_external_id && r.channel_id && r.store_id)
    .map(r => ({
      product_external_id: r.product_external_id,
      channel_id: r.channel_id,
      store_id: r.store_id,
      quantity: parseInt(r.quantity) || 0,
      available: ['true', 'True', '1'].includes(r.available),
    }));
  return sendChunked('/stock/batch', items);
}
