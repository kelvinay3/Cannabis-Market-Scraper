"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { formatRelative, formatDiscount, DEAL_TYPE_LABELS } from "@/lib/utils";
import { Tag, Store, TrendingDown, Bell, Clock, ArrowRight } from "lucide-react";
import Link from "next/link";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ label, value, icon, color }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: adminStats } = useSWR(
    user?.role && ["admin", "super_admin", "manager"].includes(user.role) ? "/admin/stats" : null,
    fetcher
  );
  const { data: newDeals } = useSWR("/deals/new?hours=24", fetcher);
  const { data: expiringDeals } = useSWR("/deals/expiring?hours=48", fetcher);

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {greeting()}, {user?.name?.split(" ")[0] || "there"} 👋
        </h1>
        <p className="text-sm text-gray-500 mt-1">Here's what's happening in the NJ cannabis market today.</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Deals"
          value={adminStats?.active_deals ?? "—"}
          icon={<Tag className="w-5 h-5 text-white" />}
          color="bg-brand-700"
        />
        <StatCard
          label="NJ Dispensaries"
          value={adminStats?.dispensaries ?? "—"}
          icon={<Store className="w-5 h-5 text-white" />}
          color="bg-blue-600"
        />
        <StatCard
          label="New Deals (24h)"
          value={newDeals?.data?.length ?? "—"}
          icon={<TrendingDown className="w-5 h-5 text-white" />}
          color="bg-amber-500"
        />
        <StatCard
          label="Expiring Soon"
          value={expiringDeals?.data?.length ?? "—"}
          icon={<Clock className="w-5 h-5 text-white" />}
          color="bg-red-500"
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* New Deals */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">New Deals (24h)</h2>
            <Link href="/dashboard/deals?filter=new" className="text-xs text-brand-700 hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-gray-50">
            {(newDeals?.data || []).slice(0, 5).map((deal: {
              id: string;
              title: string;
              deal_type: string;
              discount_value: number;
              discount_unit: string;
              dispensary_name?: string;
              first_seen_at: string;
            }) => (
              <div key={deal.id} className="px-5 py-3.5 flex items-center gap-3">
                <div className="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center shrink-0">
                  <Tag className="w-3.5 h-3.5 text-green-700" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{deal.title}</p>
                  <p className="text-xs text-gray-500 truncate">
                    {deal.dispensary_name} · {DEAL_TYPE_LABELS[deal.deal_type] || deal.deal_type}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-semibold text-green-700">
                    {formatDiscount(deal.deal_type, deal.discount_value, deal.discount_unit)}
                  </p>
                  <p className="text-xs text-gray-400">{formatRelative(deal.first_seen_at)}</p>
                </div>
              </div>
            ))}
            {(!newDeals?.data || newDeals.data.length === 0) && (
              <div className="px-5 py-8 text-center text-sm text-gray-400">No new deals in the last 24h</div>
            )}
          </div>
        </div>

        {/* Expiring Soon */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Expiring Soon (48h)</h2>
            <Link href="/dashboard/deals?filter=expiring" className="text-xs text-amber-600 hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-gray-50">
            {(expiringDeals?.data || []).slice(0, 5).map((deal: {
              id: string;
              title: string;
              deal_type: string;
              discount_value: number;
              discount_unit: string;
              dispensary_name?: string;
              ends_at: string;
            }) => (
              <div key={deal.id} className="px-5 py-3.5 flex items-center gap-3">
                <div className="w-8 h-8 bg-amber-50 rounded-lg flex items-center justify-center shrink-0">
                  <Clock className="w-3.5 h-3.5 text-amber-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{deal.title}</p>
                  <p className="text-xs text-gray-500 truncate">{deal.dispensary_name}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-semibold text-amber-700">
                    {formatDiscount(deal.deal_type, deal.discount_value, deal.discount_unit)}
                  </p>
                  <p className="text-xs text-gray-400">Ends {formatRelative(deal.ends_at)}</p>
                </div>
              </div>
            ))}
            {(!expiringDeals?.data || expiringDeals.data.length === 0) && (
              <div className="px-5 py-8 text-center text-sm text-gray-400">No deals expiring soon</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
