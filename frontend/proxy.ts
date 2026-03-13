import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const AUTH_COOKIE = "omnidocs_token";

const PROTECTED_PATHS = ["/dashboard"];
const AUTH_PATHS = ["/login", "/signup"];

function isProtected(pathname: string): boolean {
  return PROTECTED_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"));
}

function isAuthPage(pathname: string): boolean {
  return AUTH_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"));
}

export function proxy(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE)?.value;
  const { pathname } = request.nextUrl;

  if (isProtected(pathname) && !token) {
    const url = new URL("/login", request.url);
    url.searchParams.set("from", pathname);
    return NextResponse.redirect(url);
  }

  if (isAuthPage(pathname) && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login", "/signup"],
};
