"use client";

import { useState, useCallback } from "react";
import useSWR from "swr";
import api from "@/lib/api";
import { MapPin, List, SlidersHorizontal } from "lucide-react";
import { NJ_COUNTIES } from "@/lib/utils";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

interface Dispensary {
  id: string;
  name: string;
  address: string;
  city: string;
  county: string;
  latitude: number | null;
  longitude: number | null;
  active_deal_count: number;
  status: string;
}

function DispensaryList({ dispensaries, onSelect }: {
  dispensaries: Dispensary[];
  onSelect: (d: Dispensary) => void;
}) {
  return (
    <div className="overflow-y-auto flex-1">
      {dispensaries.map((d) => (
        <button
          key={d.id}
          onClick={() => onSelect(d)}
          className="w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-green-50 transition-colors"
        >
          <p className="font-medium text-sm text-gray-900 truncate">{d.name}</p>
          <p className="text-xs text-gray-500 mt-0.5">{d.city}, {d.county}</p>
          <div className="flex items-center gap-2 mt-1">
            {d.active_deal_count > 0 && (
              <span className="text-[10px] font-bold bg-green-100 text-green-800 px-1.5 py-0.5 rounded-full">
                {d.active_deal_count} deal{d.active_deal_count !== 1 ? "s" : ""}
              </span>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}

export default function MapPage() {
  const [county, setCounty] = useState("");
  const [view, setView] = useState<"map" | "list">("list");
  const [selected, setSelected] = useState<Dispensary | null>(null);

  const buildUrl = () => {
    const params = new URLSearchParams({ per_page: "200" });
    if (county) params.set("county", county);
    return `/dispensaries/?${params}`;
  };

  const { data } = useSWR(buildUrl(), fetcher);
  const dispensaries: Dispensary[] = data?.data || [];

  const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-72 bg-white border-r border-gray-100 flex flex-col h-full shrink-0">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-gray-900">Dispensaries</h2>
            <span className="text-xs text-gray-400">{dispensaries.length} total</span>
          </div>
          <select
            value={county}
            onChange={(e) => setCounty(e.target.value)}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-700 bg-white"
          >
            <option value="">All Counties</option>
            {NJ_COUNTIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <DispensaryList dispensaries={dispensaries} onSelect={setSelected} />
      </div>

      {/* Map area */}
      <div className="flex-1 bg-gray-200 flex items-center justify-center relative">
        {MAPBOX_TOKEN ? (
          <div className="absolute inset-0 bg-gray-300 flex items-center justify-center text-gray-500">
            <p className="text-sm">Map renders here with Mapbox GL JS (token configured)</p>
          </div>
        ) : (
          <div className="text-center text-gray-500">
            <MapPin className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">Mapbox token required</p>
            <p className="text-sm mt-1">Set NEXT_PUBLIC_MAPBOX_TOKEN in .env.local</p>
          </div>
        )}

        {selected && (
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white rounded-xl shadow-xl border border-gray-100 p-4 w-72 z-10">
            <button
              onClick={() => setSelected(null)}
              className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 text-lg leading-none"
            >
              ×
            </button>
            <p className="font-bold text-gray-900 pr-6">{selected.name}</p>
            <p className="text-sm text-gray-500 mt-1">{selected.address}</p>
            <p className="text-sm text-gray-500">{selected.city}, NJ</p>
            {selected.active_deal_count > 0 && (
              <div className="mt-2 text-sm font-medium text-green-700">
                {selected.active_deal_count} active deal{selected.active_deal_count !== 1 ? "s" : ""}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
