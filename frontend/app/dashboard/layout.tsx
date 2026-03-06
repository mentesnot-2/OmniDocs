"use client";


import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    useEffect(() => {
        const token = localStorage.getItem("omnidocs_token");
        if (!token) {
            router.push("/login");
        }
    }, [router]);
    return <div>{children}</div>;
}