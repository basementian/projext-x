// === Health ===
export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

// === Listings ===
export interface ListingCreate {
  sku: string;
  title: string;
  purchase_price: number;
  list_price: number;
  shipping_cost?: number;
  brand?: string;
  model?: string;
  description?: string;
}

export interface ListingResponse {
  id: number;
  sku: string;
  title: string;
  title_sanitized: string | null;
  status: string;
  purchase_price: number;
  list_price: number;
  days_active: number;
  total_views: number;
  zombie_cycle_count: number;
}

export interface ListingCreateResponse {
  id: number;
  sku: string;
  title_sanitized: string;
  title_changes: string[];
  profit: {
    net_profit: number;
    meets_floor: boolean;
    minimum_viable_price: number;
  };
}

// === Queue ===
export interface QueueEntry {
  id: number;
  listing_id: number;
  sku: string;
  title: string;
  priority: number;
  scheduled_window: string;
  status: string;
  scheduled_at: string;
  released_at: string | null;
  error_message: string | null;
}

export interface QueueStatusResponse {
  pending: number;
  released_today: number;
  failed: number;
  total: number;
  surge_window_active: boolean;
  next_surge_window: string | null;
  entries: QueueEntry[];
}

export interface EnqueueRequest {
  listing_id: number;
  priority?: number;
  window?: string;
}

export interface EnqueueResponse {
  id: number;
  listing_id: number;
  status: string;
}

export interface ReleaseBatchResponse {
  released: number;
  dry_run: boolean;
  surge_window_active: boolean;
}

// === Zombies ===
export interface ZombieReport {
  listing_id: number;
  sku: string;
  title: string;
  ebay_item_id: string | null;
  days_active: number;
  total_views: number;
  watchers: number;
  zombie_cycle_count: number;
  should_purgatory: boolean;
  current_price: number | null;
}

export interface ZombieScanResult {
  total_scanned: number;
  zombies_found: number;
  purgatory_candidates: number;
  zombies: ZombieReport[];
}

export interface ResurrectionResult {
  listing_id: number;
  sku: string;
  old_item_id: string | null;
  new_item_id: string | null;
  new_offer_id: string | null;
  cycle_number: number;
  success: boolean;
  error: string | null;
  resurrected_at: string | null;
}

// === Repricer ===
export interface RepriceDetail {
  listing_id: number;
  sku: string;
  step: number;
  percent_off: number;
  old_price: number;
  new_price: number;
  min_viable_price: number;
  reason: string;
}

export interface RepricerResult {
  total_scanned: number;
  repriced: number;
  skipped: number;
  ebay_errors: number;
  details: RepriceDetail[];
}

// === Relister ===
export interface RelisterCandidate {
  listing_id: number;
  sku: string;
  title: string;
  days_active: number;
  total_views: number;
  current_price: number;
}

export interface RelisterDetail {
  listing_id: number;
  sku: string;
  old_item_id: string | null;
  new_item_id: string | null;
}

export interface RelisterResult {
  total_scanned: number;
  relisted: number;
  skipped: number;
  errors: number;
  details: RelisterDetail[];
}

// === Offers ===
export interface IncomingOfferRequest {
  buyer_id: string;
  offer_id: string;
  offer_amount: number;
}

export interface OfferDetail {
  listing_id: number;
  sku: string;
  buyer_id: string;
  original_price: number;
  offer_price: number;
  discount_percent: number;
  days_active: number;
}

export interface OfferScanResult {
  listings_checked: number;
  offers_sent: number;
  errors: number;
  details: OfferDetail[];
}

export interface OfferHandleResult {
  success: boolean;
  listing_id?: number;
  action?: string;
  offer_amount?: number;
  current_price?: number;
  ratio?: number;
  counter_amount?: number | null;
  error?: string;
}
