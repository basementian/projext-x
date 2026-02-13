import { getApiUrl } from "./storage";
import type {
  HealthResponse,
  ListingCreate,
  ListingResponse,
  ListingCreateResponse,
  QueueStatusResponse,
  EnqueueRequest,
  EnqueueResponse,
  ReleaseBatchResponse,
  ZombieScanResult,
  ResurrectionResult,
  RepricerResult,
  RelisterCandidate,
  RelisterResult,
  IncomingOfferRequest,
  OfferScanResult,
  OfferHandleResult,
} from "./types";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const baseUrl = await getApiUrl();
  const url = `${baseUrl}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

// Health
export const checkHealth = () => request<HealthResponse>("/health");

// Listings
export const getListings = (status?: string) => {
  const qs = status ? `?status=${status}` : "";
  return request<ListingResponse[]>(`/listings${qs}`);
};
export const getListing = (id: number) =>
  request<ListingResponse>(`/listings/${id}`);
export const createListing = (data: ListingCreate) =>
  request<ListingCreateResponse>("/listings", {
    method: "POST",
    body: JSON.stringify(data),
  });

// Queue
export const getQueueStatus = () =>
  request<QueueStatusResponse>("/queue/status");
export const enqueue = (data: EnqueueRequest) =>
  request<EnqueueResponse>("/queue", {
    method: "POST",
    body: JSON.stringify(data),
  });
export const releaseBatch = (dryRun = false) =>
  request<ReleaseBatchResponse>(`/queue/release?dry_run=${dryRun}`, {
    method: "POST",
  });

// Zombies
export const scanZombies = () => request<ZombieScanResult>("/zombies");
export const resurrectZombie = (listingId: number) =>
  request<ResurrectionResult>(`/zombies/${listingId}/resurrect`, {
    method: "POST",
  });

// Repricer
export const previewRepricing = () =>
  request<RepricerResult>("/repricer/preview");
export const runRepricing = () =>
  request<RepricerResult>("/repricer/run", { method: "POST" });

// Relister
export const previewRelists = () =>
  request<RelisterCandidate[]>("/relister/preview");
export const runRelists = () =>
  request<RelisterResult>("/relister/run", { method: "POST" });

// Offers
export const scanOffers = () =>
  request<OfferScanResult>("/offers/scan", { method: "POST" });
export const handleOffer = (listingId: number, data: IncomingOfferRequest) =>
  request<OfferHandleResult>(`/offers/${listingId}/handle`, {
    method: "POST",
    body: JSON.stringify(data),
  });
