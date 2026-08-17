"use client";

import { useState } from "react";
import useSWR from "swr";
import api from "@/lib/api";
import { formatRelative, formatDate } from "@/lib/utils";
import { useToast } from "@/components/ui/Toaster";
import { RefreshCw, CheckCircle, XCircle, Clock, Loader2, Play } from "lucide-react";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

interface ScrapeSource {
  id: string;
  dispensary_name: string;
  platform: string;
  is_active: boolean;
  last_scrape_at: string | null;
  next_scrape_at: string | null;
}

interface ScrapeJob {
  id: string;
  dispensary_name: string;
  platform: string;
  status: string;
  deals_found: number;
  items_found: number;
  started_at: string | null;
  completed_at: string | null;
  errors: unknown;
}

function StatusBadge({ status }: { status: string }) {
  const cls = {
    completed: "bg-green-100 text-green-700",
    running: "bg-blue-100 text-blue-700",
    failed: "bg-red-100 text-red-700",
    pending: "bg-gray-100 text-gray-600",
  }[status] || "bg-gray-100 text-gray-600";

  const Icon = {
    completed: CheckCircle,
    running: RefreshCw,
    failed: XCircle,
    pending: Clock,
  }[status] || Clock;

  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>
      <Icon className="w-3 h-3" />
      {status}
    </span>
  );
}

export default function AdminPage() {
  const { toast } = useToast();
  const { data: stats } = useSWR("/admin/stats", fetcher);
  const { data: scrapers, mutate: mutateSources } = useSWR("/admin/scrapers", fetcher);
  const { data: jobs, mutate: mutateJobs } = useSWR("/admin/scrape-jobs?per_page=20", fetcher, { refreshInterval: 15000 });
  const [triggering, setTriggering] = useState<string | null>(null);

  const triggerScrape = async (sourceId: string, name: string) => {
    setTriggering(sourceId);
    try {
      await api.post(`/admin/scrapers/${sourceId}/run`);
      toast(`Scrape triggered for ${name}`, "success");
      setTimeout(() => mutateJobs(), 2000);
    } catch {
      toast("Failed to trigger scrape", "error");
    } finally {
      setTriggering(null);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        <p className="text-sm text-gray-500 mt-1">Platform stats, scraper health, and job history</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { label: "Dispensaries", value: stats.dispensaries },
            { label: "Active Deals", value: stats.active_deals },
            { label: "Total Deals", value: stats.total_deals_ever },
            { label: "Users", value: stats.users },
            { label: "Scrape Sources", value: stats.scrape_sources },
            { label: "Last Scrape", value: stats.last_scrape ? formatRelative(stats.last_scrape) : "Never" },
          ].map((s) => (
            <div key={s.label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <p className="text-xl font-bold text-gray-900">{s.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Scrape Sources */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Scrape Sources</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Dispensary</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Platform</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Last Scrape</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Next</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(scrapers || []).map((s: ScrapeSource) => (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-medium text-gray-900">{s.dispensary_name}</td>
                  <td className="px-5 py-3">
                    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">{s.platform}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${s.is_active ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                      {s.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-gray-500">{s.last_scrape_at ? formatRelative(s.last_scrape_at) : "Never"}</td>
                  <td className="px-5 py-3 text-gray-500">{s.next_scrape_at ? formatRelative(s.next_scrape_at) : "—"}</td>
                  <td className="px-5 py-3">
                    <button
                      onClick={() => triggerScrape(s.id, s.dispensary_name)}
                      disabled={triggering === s.id}
                      className="flex items-center gap-1.5 text-xs text-brand-700 hover:text-brand-900 font-medium disabled:opacity-50"
                    >
                      {triggering === s.id
                        ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        : <Play className="w-3.5 h-3.5" />
                      }
                      Run
                    </button>
                  </td>
                </tr>
              ))}
              {!scrapers?.length && (
                <tr><td colSpan={6} className="px-5 py-8 text-center text-sm text-gray-400">No scrape sources configured</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Job History */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Recent Jobs</h2>
          <button onClick={() => mutateJobs()} className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1">
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Dispensary</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Platform</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Deals</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Items</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Started</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Duration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(jobs?.data || []).map((job: ScrapeJob) => {
                const dur = job.started_at && job.completed_at
                  ? Math.round((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000)
                  : null;
                return (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3 font-medium text-gray-900 truncate max-w-[160px]">{job.dispensary_name}</td>
                    <td className="px-5 py-3">
                      <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">{job.platform}</span>
                    </td>
                    <td className="px-5 py-3"><StatusBadge status={job.status} /></td>
                    <td className="px-5 py-3 text-gray-600">{job.deals_found || 0}</td>
                    <td className="px-5 py-3 text-gray-600">{job.items_found || 0}</td>
                    <td className="px-5 py-3 text-gray-500">{job.started_at ? formatRelative(job.started_at) : "—"}</td>
                    <td className="px-5 py-3 text-gray-500">{dur != null ? `${dur}s` : "—"}</td>
                  </tr>
                );
              })}
              {!jobs?.data?.length && (
                <tr><td colSpan={7} className="px-5 py-8 text-center text-sm text-gray-400">No jobs yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
