"use client";

import { useEffect, useState } from "react";
import { getJson, postJson } from "@/lib/api";


type Me = {
    id: number;
    email: string;
    is_admin?: boolean;
}

type AdminUser = {
    id: number;
    email: string;
    is_verified: boolean;
    is_admin: boolean;
    is_active: boolean;
    created_at: string;
}

type Ticket = {
    id: number;
    user_id: number;
    subject: string;
    message: string;
    status: "open" | "in_progress" | "resolved";
    created_at: string | null;
};



export default function AdminPage() {
    const [loading, setLoading] = useState(true);
    const [forbidden, setForbidden] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [users, setUsers] = useState<AdminUser[]>([]);
    const [tickets, setTickets] = useState<Ticket[]>([]);

    async function loadAll() {
        setError(null);
        try {
            const [usersRes, ticketsRes] = await Promise.all([
                getJson<{users:AdminUser[]}>("/admin/users"),
                getJson<{tickets:Ticket[]}>("/admin/support/tickets"),
            ]);
            setUsers(usersRes.users || []);
            setTickets(ticketsRes.tickets || []);

        } catch (err:any) {
            const msg = err?.message || "Failed to load admin data";
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

    async function toggleActive(user: AdminUser) {
        try {
            await postJson<{is_active:boolean}, {id:number,is_active:boolean}>(
                `/admin/users/${user.id}/active`,
                {is_active: !user.is_active}
            );
            setUsers((prev) => prev.map((u) => (u.id === user.id ? {...u, is_active: !u.is_active}:u))
        );

        } catch(err:any) {
            setError(err?.message || "Failed to update user")
        }
    }
}