"use client";

import useSWR from "swr";
import api from "@/lib/api";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from "recharts";
import { formatDate, DEAL_TYPE_LABELS, CATEGORY_LABELS } from "@/lib/utils";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

const COLORS = ["#15502A", "#2f9a23", "#53b83f", "#86d470", "#bbeba7", "#dcf4e2"];

export default function ReportsPage() {
  const { data: deals } = useSWR("/deals/?per_page=500&active_only=true", fetcher);
  const { data: priceChanges } = useSWR("/deals/prices/changes", fetcher);
  const { data: newDealsWeek } = useSWR("/deals/new?hours=168", fetcher);

  const dealsByType: Record<string, number> = {};
  const dealsByCounty: Record<string, number> = {};
  const dealsByCategory: Record<string, number> = {};

  for (const deal of deals?.data || []) {
    dealsByType[deal.deal_type] = (dealsByType[deal.deal_type] || 0) + 1;
    const county = deal.dispensary_county || "Unknown";
    dealsByCounty[county] = (dealsByCounty[county] || 0) + 1;
    for (const cat of deal.applicable_categories || []) {
      dealsByCategory[cat] = (dealsByCategory[cat] || 0) + 1;
    }
  }

  const typeData = Object.entries(dealsByType)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([k, v]) => ({ name: DEAL_TYPE_LABELS[k] || k, value: v }));

  const countyData = Object.entries(dealsByCounty)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12)
    .map(([k, v]) => ({ name: k, value: v }));

  const categoryData = Object.entries(dealsByCategory)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([k, v]) => ({ name: CATEGORY_LABELS[k] || k, value: v }));

  const priceData = (priceChanges?.data || []).slice(0, 20).map((pc: {
    detected_at: string;
    old_price: number;
    new_price: number;
    change_pct: number;
  }) => ({
    date: formatDate(pc.detected_at),
    old: Number(pc.old_price),
    new: Number(pc.new_price),
    pct: Number(pc.change_pct),
  }));

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="text-sm text-gray-500 mt-1">Historical trends and market analysis for NJ cannabis</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Active Deals", value: deals?.total || 0, color: "text-brand-700" },
          { label: "New This Week", value: newDealsWeek?.data?.length || 0, color: "text-blue-600" },
          { label: "Price Changes (recent)", value: priceChanges?.data?.length || 0, color: "text-amber-600" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-sm text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Deals by County */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Active Deals by County</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={countyData} layout="vertical" margin={{ left: 30 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} />
              <Tooltip />
              <Bar dataKey="value" fill="#15502A" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Deals by Type */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Deals by Type</h2>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={typeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                {typeData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Deals by Category */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Deals by Category</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={categoryData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#2f9a23" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Price Changes */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Recent Price Changes</h2>
          {priceData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={priceData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="old" stroke="#9ca3af" name="Old Price" dot={false} />
                <Line type="monotone" dataKey="new" stroke="#15502A" name="New Price" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-sm text-gray-400">
              No price changes recorded yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
