"use client";

import { useState } from "react";
import useSWR from "swr";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { isSuperAdmin } from "@/lib/auth";
import { useToast } from "@/components/ui/Toaster";
import { formatDate, formatRelative } from "@/lib/utils";
import { UserPlus, Trash2, ChevronDown, Loader2, Mail, X } from "lucide-react";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

const ROLES = ["viewer", "analyst", "manager", "admin", "super_admin"];

function InviteModal({ onClose, onSent }: { onClose: () => void; onSent: () => void }) {
  const { toast } = useToast();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("analyst");
  const [sending, setSending] = useState(false);
  const [inviteLink, setInviteLink] = useState("");

  const handleSend = async () => {
    if (!email.trim()) { toast("Enter an email", "error"); return; }
    setSending(true);
    try {
      const { data } = await api.post("/users/invite", { email: email.trim(), role });
      if (data.invite_link) {
        setInviteLink(data.invite_link);
      } else {
        toast("Invite sent!", "success");
        onSent();
        onClose();
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast(msg || "Failed to send invite", "error");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-gray-900">Invite User</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>

        {inviteLink ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">Email invite sent! Share this link as a backup:</p>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs break-all text-gray-700 font-mono">
              {inviteLink}
            </div>
            <button
              onClick={() => { navigator.clipboard.writeText(inviteLink); toast("Link copied!", "success"); }}
              className="w-full bg-brand-950 text-white rounded-lg py-2.5 text-sm font-semibold"
            >
              Copy link
            </button>
            <button onClick={onClose} className="w-full border border-gray-200 text-gray-600 rounded-lg py-2.5 text-sm">
              Done
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="colleague@company.com"
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700 bg-white"
              >
                {ROLES.map((r) => <option key={r} value={r}>{r.replace("_", " ")}</option>)}
              </select>
            </div>
            <div className="flex gap-3 mt-2">
              <button onClick={onClose} className="flex-1 border border-gray-200 text-gray-600 rounded-lg py-2.5 text-sm">
                Cancel
              </button>
              <button
                onClick={handleSend}
                disabled={sending}
                className="flex-1 bg-brand-950 text-white rounded-lg py-2.5 text-sm font-semibold disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                Send invite
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const { toast } = useToast();
  const [showInvite, setShowInvite] = useState(false);
  const [page, setPage] = useState(1);

  const { data, mutate } = useSWR(`/users/?page=${page}&per_page=20`, fetcher);
  const users: User[] = data?.data || [];
  const total = data?.total || 0;
  const pages = data?.pages || 1;

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await api.patch(`/users/${userId}/role`, { role: newRole });
      mutate();
      toast("Role updated", "success");
    } catch {
      toast("Failed to update role", "error");
    }
  };

  const handleDelete = async (userId: string, name: string) => {
    if (!confirm(`Deactivate ${name}?`)) return;
    try {
      await api.delete(`/users/${userId}`);
      mutate();
      toast("User deactivated", "success");
    } catch {
      toast("Failed to deactivate user", "error");
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Users</h1>
          <p className="text-sm text-gray-500 mt-1">{total} total users</p>
        </div>
        <button
          onClick={() => setShowInvite(true)}
          className="flex items-center gap-2 bg-brand-950 text-white rounded-xl px-4 py-2.5 text-sm font-semibold hover:bg-brand-900"
        >
          <UserPlus className="w-4 h-4" /> Invite User
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">User</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Role</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Last Login</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Joined</th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-5 py-3.5">
                  <div className="font-medium text-gray-900">{u.name}</div>
                  <div className="text-xs text-gray-500">{u.email}</div>
                </td>
                <td className="px-5 py-3.5">
                  {currentUser && isSuperAdmin(currentUser) && u.id !== currentUser.id ? (
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      className="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-brand-700 bg-white"
                    >
                      {ROLES.map((r) => <option key={r} value={r}>{r.replace("_", " ")}</option>)}
                    </select>
                  ) : (
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">{u.role.replace("_", " ")}</span>
                  )}
                </td>
                <td className="px-5 py-3.5">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${u.is_active ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"}`}>
                    {u.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-5 py-3.5 text-gray-500">{u.last_login ? formatRelative(u.last_login) : "Never"}</td>
                <td className="px-5 py-3.5 text-gray-500">{formatDate(u.created_at)}</td>
                <td className="px-5 py-3.5">
                  {u.id !== currentUser?.id && (
                    <button
                      onClick={() => handleDelete(u.id, u.name)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                      title="Deactivate"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr><td colSpan={6} className="px-5 py-8 text-center text-sm text-gray-400">No users found</td></tr>
            )}
          </tbody>
        </table>

        {pages > 1 && (
          <div className="flex items-center justify-center gap-2 border-t border-gray-100 p-4">
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

      {showInvite && (
        <InviteModal
          onClose={() => setShowInvite(false)}
          onSent={() => mutate()}
        />
      )}
    </div>
  );
}
