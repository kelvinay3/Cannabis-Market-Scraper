"use client";

import { useState, useEffect, useRef } from "react";
import useSWR from "swr";
import api from "@/lib/api";
import { formatRelative, formatDiscount, DEAL_TYPE_LABELS, CATEGORY_LABELS, NJ_COUNTIES } from "@/lib/utils";
import { Search, Filter, Tag, ChevronDown, X, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

interface Deal {
  id: string;
  title: string;
  description: string;
  deal_type: string;
  discount_value: number | null;
  discount_unit: string;
  applicable_categories: string[];
  day_of_week: string[];
  starts_at: string | null;
  ends_at: string | null;
  first_seen_at: string;
  dispensary_name: string;
  dispensary_city: string;
  dispensary_county: string;
  source_platform: string;
}

const PLATFORMS = ["jane", "dutchie", "weedmaps", "leafly", "treez"];

function DealCard({ deal, isNew }: { deal: Deal; isNew?: boolean }) {
  return (
    <div className={cn(
      "bg-white rounded-xl border p-4 hover:shadow-md transition-all",
      isNew ? "border-green-300 shadow-green-50 shadow-md" : "border-gray-100 shadow-sm"
    )}>
      {isNew && (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-green-700 bg-green-50 px-2 py-0.5 rounded-full mb-2">
          <Zap className="w-2.5 h-2.5" /> New
        </span>
      )}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900 text-sm leading-snug">{deal.title}</p>
          {deal.description && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{deal.description}</p>
          )}
          <div className="flex flex-wrap gap-1.5 mt-2">
            {deal.applicable_categories.map((c) => (
              <span key={c} className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                {CATEGORY_LABELS[c] || c}
              </span>
            ))}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-lg font-bold text-green-700 leading-none">
            {formatDiscount(deal.deal_type, deal.discount_value, deal.discount_unit)}
          </div>
          <div className="text-[10px] text-gray-400 mt-0.5">{DEAL_TYPE_LABELS[deal.deal_type] || deal.deal_type}</div>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-gray-50 flex items-center justify-between text-xs text-gray-400">
        <span>
          <span className="font-medium text-gray-600">{deal.dispensary_name}</span>
          {" · "}
          {deal.dispensary_city}, {deal.dispensary_county}
        </span>
        <span>{formatRelative(deal.first_seen_at)}</span>
      </div>
    </div>
  );
}

export default function DealsPage() {
  const [search, setSearch] = useState("");
  const [county, setCounty] = useState("");
  const [category, setCategory] = useState("");
  const [dealType, setDealType] = useState("");
  const [platform, setPlatform] = useState("");
  const [page, setPage] = useState(1);
  const [newDealIds, setNewDealIds] = useState<Set<string>>(new Set());
  const wsRef = useRef<WebSocket | null>(null);

  const buildUrl = () => {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("per_page", "30");
    if (search) params.set("search", search);
    if (county) params.set("county", county);
    if (category) params.set("category", category);
    if (dealType) params.set("deal_type", dealType);
    if (platform) params.set("platform", platform);
    params.set("active_only", "true");
    return `/deals/?${params}`;
  };

  const { data, mutate } = useSWR(buildUrl(), fetcher, { refreshInterval: 60_000 });

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/deals`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === "new_deal" && msg.deal_id) {
          setNewDealIds((prev) => new Set([...prev, msg.deal_id]));
          mutate();
          setTimeout(() => {
            setNewDealIds((prev) => {
              const next = new Set(prev);
              next.delete(msg.deal_id);
              return next;
            });
          }, 30_000);
        }
      } catch { /* ignore */ }
    };

    return () => ws.close();
  }, [mutate]);

  const deals: Deal[] = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 1;

  const hasFilters = !!(search || county || category || dealType || platform);

  const clearFilters = () => {
    setSearch(""); setCounty(""); setCategory(""); setDealType(""); setPlatform(""); setPage(1);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Live Deals</h1>
        <p className="text-sm text-gray-500 mt-1">
          {total} active deals across NJ dispensaries · updates every 15 min
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-48">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search deals…"
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-700"
          />
        </div>

        <select
          value={county}
          onChange={(e) => { setCounty(e.target.value); setPage(1); }}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-700 bg-white"
        >
          <option value="">All Counties</option>
          {NJ_COUNTIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        <select
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-700 bg-white"
        >
          <option value="">All Categories</option>
          {Object.entries(CATEGORY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>

        <select
          value={dealType}
          onChange={(e) => { setDealType(e.target.value); setPage(1); }}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-700 bg-white"
        >
          <option value="">All Deal Types</option>
          {Object.entries(DEAL_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>

        <select
          value={platform}
          onChange={(e) => { setPlatform(e.target.value); setPage(1); }}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-700 bg-white"
        >
          <option value="">All Platforms</option>
          {PLATFORMS.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>

        {hasFilters && (
          <button onClick={clearFilters} className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-600 transition-colors">
            <X className="w-3.5 h-3.5" /> Clear
          </button>
        )}
      </div>

      {/* Deal Grid */}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {deals.map((deal) => (
          <DealCard key={deal.id} deal={deal} isNew={newDealIds.has(deal.id)} />
        ))}
      </div>

      {deals.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <Tag className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="font-medium">No deals found</p>
          <p className="text-sm mt-1">Try adjusting your filters</p>
        </div>
      )}

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page} of {pages}</span>
          <button
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
            disabled={page === pages}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
