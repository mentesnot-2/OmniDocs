"use client";

import { useEffect, useMemo, useState } from "react";
import { getJson, patchJson } from "@/lib/api";

type Me = {
  id: number;
  email: string;
  is_admin: boolean;
};

type AdminUser = {
  id: number;
  email: string;
  is_verified: boolean;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
};

type Ticket = {
  id: number;
  user_id: number;
  subject: string;
  message: string;
  status: "open" | "in_progress" | "resolved";
  created_at: string | null;
};

type AuditLog = {
  id: number;
  admin_user_id: number;
  action: string;
  target_type: string;
  target_id: string;
  metadata_json: string | null;
  created_at: string | null;
};

export default function AdminPage() {
  const [loading, setLoading] = useState(true);
  const [forbidden, setForbidden] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [ticketFilter, setTicketFilter] = useState<"all" | Ticket["status"]>("all");

  async function loadAll() {
    setError(null);
    try {
      const [usersRes, ticketsRes, logsRes] = await Promise.all([
        getJson<{ users: AdminUser[] }>("/admin/users"),
        getJson<{ tickets: Ticket[] }>("/admin/support/tickets"),
        getJson<{ logs: AuditLog[] }>("/admin/audit-logs"),
      ]);
      setUsers(usersRes.users || []);
      setTickets(ticketsRes.tickets || []);
      setAuditLogs(logsRes.logs || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load admin data";
      if (msg.includes("Admin only") || msg.includes("403")) {
        setForbidden(true);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    getJson<Me>("/auth/me")
      .then((me) => {
        if (me.is_admin === false) {
          setForbidden(true);
          setLoading(false);
          return;
        }
        return loadAll();
      })
      .catch(() => {
        setForbidden(true);
        setLoading(false);
      });
  }, []);

  const filteredTickets = useMemo(() => {
    if (ticketFilter === "all") return tickets;
    return tickets.filter((t) => t.status === ticketFilter);
  }, [tickets, ticketFilter]);

  async function toggleActive(user: AdminUser) {
    const nextActive = !user.is_active;
    const label = nextActive ? "activate" : "deactivate";
    if (!confirm(`${label} user ${user.email}?`)) return;

    try {
      await patchJson<{ is_active: boolean }, { id: number; is_active: boolean }>(
        `/admin/users/${user.id}/active`,
        { is_active: nextActive }
      );
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, is_active: nextActive } : u))
      );
      const logsRes = await getJson<{ logs: AuditLog[] }>("/admin/audit-logs");
      setAuditLogs(logsRes.logs || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update user");
    }
  }

  async function updateTicketStatus(ticket: Ticket, status: Ticket["status"]) {
    try {
      await patchJson<{ status: string }, { id: number; status: string }>(
        `/admin/support/tickets/${ticket.id}`,
        { status }
      );
      setTickets((prev) => prev.map((t) => (t.id === ticket.id ? { ...t, status } : t)));
      const logsRes = await getJson<{ logs: AuditLog[] }>("/admin/audit-logs");
      setAuditLogs(logsRes.logs || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update ticket");
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
        <p>Loading admin panel...</p>
      </div>
    );
  }

  if (forbidden) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
        <h1 className="text-2xl font-semibold mb-2">403</h1>
        <p className="text-slate-400">Admin access required</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-8">
      <h1 className="text-2xl font-semibold">Admin Panel</h1>
      {error && (
        <p className="text-sm text-red-400 bg-red-950/40 border border-red-700 rounded-md px-3 py-2">
          {error}
        </p>
      )}

      <section className="space-y-6">
        <h2 className="text-xl font-medium">Users</h2>
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900">
              <tr>
                <th className="text-left px-3 py-2">ID</th>
                <th className="text-left px-3 py-2">Email</th>
                <th className="text-left px-3 py-2">Verified</th>
                <th className="text-left px-3 py-2">Admin</th>
                <th className="text-left px-3 py-2">Active</th>
                <th className="text-left px-3 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-slate-800">
                  <td className="px-3 py-2">{u.id}</td>
                  <td className="px-3 py-2">{u.email}</td>
                  <td className="px-3 py-2">{u.is_verified ? "Yes" : "No"}</td>
                  <td className="px-3 py-2">{u.is_admin ? "Yes" : "No"}</td>
                  <td className="px-3 py-2">{u.is_active ? "Yes" : "No"}</td>
                  <td className="px-3 py-2">
                    <button
                      className="rounded bg-slate-800 hover:bg-slate-700 px-3 py-1"
                      onClick={() => toggleActive(u)}
                    >
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Support Tickets</h2>
          <select
            value={ticketFilter}
            onChange={(e) => setTicketFilter(e.target.value as typeof ticketFilter)}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm"
          >
            <option value="all">All</option>
            <option value="open">open</option>
            <option value="in_progress">in_progress</option>
            <option value="resolved">resolved</option>
          </select>
        </div>
        <div className="space-y-2">
          {filteredTickets.map((t) => (
            <div key={t.id} className="rounded-lg border border-slate-800 p-4 bg-slate-900/40">
              <div className="flex items-center justify-between">
                <p className="font-medium">
                  #{t.id} • User {t.user_id} • {t.subject}
                </p>
                <select
                  value={t.status}
                  onChange={(e) => updateTicketStatus(t, e.target.value as Ticket["status"])}
                  className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm"
                >
                  <option value="open">open</option>
                  <option value="in_progress">in_progress</option>
                  <option value="resolved">resolved</option>
                </select>
              </div>
              <p className="text-slate-300 mt-2">{t.message}</p>
            </div>
          ))}
          {filteredTickets.length === 0 && (
            <p className="text-slate-400">No tickets match this filter.</p>
          )}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Audit Log</h2>
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900">
              <tr>
                <th className="text-left px-3 py-2">Time</th>
                <th className="text-left px-3 py-2">Admin</th>
                <th className="text-left px-3 py-2">Action</th>
                <th className="text-left px-3 py-2">Target</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id} className="border-t border-slate-800">
                  <td className="px-3 py-2">{log.created_at}</td>
                  <td className="px-3 py-2">{log.admin_user_id}</td>
                  <td className="px-3 py-2">{log.action}</td>
                  <td className="px-3 py-2">
                    {log.target_type}:{log.target_id}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
