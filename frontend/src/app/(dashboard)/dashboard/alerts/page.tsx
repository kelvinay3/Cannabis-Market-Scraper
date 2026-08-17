"use client";

import { useState } from "react";
import useSWR from "swr";
import api from "@/lib/api";
import { Bell, Plus, Trash2, Play, CheckCircle, Edit2, X, Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/Toaster";
import { NJ_COUNTIES, CATEGORY_LABELS, DEAL_TYPE_LABELS } from "@/lib/utils";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

interface Alert {
  id: string;
  name: string;
  trigger_type: string;
  filter_config: Record<string, unknown>;
  channels: string[];
  is_active: boolean;
  created_at: string;
}

const TRIGGER_TYPES = [
  { value: "new_deal", label: "New Deal" },
  { value: "price_drop", label: "Price Drop" },
  { value: "new_product", label: "New Product" },
  { value: "deal_change", label: "Deal Changed" },
  { value: "deal_expired", label: "Deal Expired" },
];

function AlertRow({ alert, onDelete, onTest, onToggle }: {
  alert: Alert;
  onDelete: (id: string) => void;
  onTest: (id: string) => void;
  onToggle: (id: string, active: boolean) => void;
}) {
  const { toast } = useToast();
  const [testing, setTesting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleTest = async () => {
    setTesting(true);
    try {
      await onTest(alert.id);
      toast("Test notification sent!", "success");
    } catch {
      toast("Test failed. Check email settings.", "error");
    } finally {
      setTesting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete alert "${alert.name}"?`)) return;
    setDeleting(true);
    await onDelete(alert.id);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-4">
      <div className={`w-2 h-10 rounded-full shrink-0 ${alert.is_active ? "bg-green-500" : "bg-gray-300"}`} />
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-gray-900 text-sm">{alert.name}</p>
        <p className="text-xs text-gray-500 mt-0.5">
          {TRIGGER_TYPES.find((t) => t.value === alert.trigger_type)?.label || alert.trigger_type}
          {" · "}
          {alert.channels?.join(", ") || "no channels"}
        </p>
        {alert.filter_config && Object.keys(alert.filter_config).length > 0 && (
          <p className="text-xs text-gray-400 mt-0.5 truncate">
            {JSON.stringify(alert.filter_config)}
          </p>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => onToggle(alert.id, !alert.is_active)}
          className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
            alert.is_active
              ? "bg-green-50 text-green-700 hover:bg-green-100"
              : "bg-gray-100 text-gray-500 hover:bg-gray-200"
          }`}
        >
          {alert.is_active ? "Active" : "Paused"}
        </button>
        <button
          onClick={handleTest}
          disabled={testing}
          title="Send test"
          className="p-1.5 rounded-lg text-gray-400 hover:text-brand-700 hover:bg-brand-50 transition-colors"
        >
          {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          title="Delete"
          className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
        >
          {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
}

function CreateAlertModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [triggerType, setTriggerType] = useState("new_deal");
  const [channels, setChannels] = useState<string[]>(["email"]);
  const [county, setCounty] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [minDiscount, setMinDiscount] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) { toast("Enter an alert name", "error"); return; }
    setSaving(true);
    try {
      const filterConfig: Record<string, unknown> = {};
      if (county) filterConfig.county = county;
      if (categories.length) filterConfig.categories = categories;
      if (minDiscount) filterConfig.min_discount = Number(minDiscount);

      await api.post("/alerts/", {
        name: name.trim(),
        trigger_type: triggerType,
        channels,
        filter_config: filterConfig,
      });
      toast("Alert created!", "success");
      onSaved();
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast(msg || "Failed to create alert", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-gray-900">New Alert</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Alert name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Flower Deals – Essex County"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Trigger type</label>
            <select
              value={triggerType}
              onChange={(e) => setTriggerType(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700 bg-white"
            >
              {TRIGGER_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by county</label>
            <select
              value={county}
              onChange={(e) => setCounty(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700 bg-white"
            >
              <option value="">All counties</option>
              {NJ_COUNTIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Minimum discount (%)</label>
            <input
              type="number"
              value={minDiscount}
              onChange={(e) => setMinDiscount(e.target.value)}
              placeholder="e.g. 20"
              min="0"
              max="100"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Channels</label>
            <div className="flex gap-3">
              {["email", "sms"].map((ch) => (
                <label key={ch} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={channels.includes(ch)}
                    onChange={(e) => {
                      if (e.target.checked) setChannels((prev) => [...prev, ch]);
                      else setChannels((prev) => prev.filter((c) => c !== ch));
                    }}
                    className="rounded"
                  />
                  {ch.toUpperCase()}
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-200 text-gray-700 rounded-lg py-2.5 text-sm font-medium hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 bg-brand-950 text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-brand-900 disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            Create Alert
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AlertsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const { data, mutate } = useSWR("/alerts/", fetcher);
  const alerts: Alert[] = data || [];

  const handleDelete = async (id: string) => {
    await api.delete(`/alerts/${id}`);
    mutate();
  };

  const handleTest = async (id: string) => {
    await api.post(`/alerts/${id}/test`);
  };

  const handleToggle = async (id: string, active: boolean) => {
    await api.patch(`/alerts/${id}`, { is_active: active });
    mutate();
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          <p className="text-sm text-gray-500 mt-1">Get notified when deals match your criteria</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-brand-950 text-white rounded-xl px-4 py-2.5 text-sm font-semibold hover:bg-brand-900"
        >
          <Plus className="w-4 h-4" /> New Alert
        </button>
      </div>

      <div className="space-y-3">
        {alerts.map((alert) => (
          <AlertRow
            key={alert.id}
            alert={alert}
            onDelete={handleDelete}
            onTest={handleTest}
            onToggle={handleToggle}
          />
        ))}
        {alerts.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <Bell className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No alerts yet</p>
            <p className="text-sm mt-1">Create an alert to get notified about deals</p>
          </div>
        )}
      </div>

      {showCreate && (
        <CreateAlertModal onClose={() => setShowCreate(false)} onSaved={() => mutate()} />
      )}
    </div>
  );
}
