import { NextRequest, NextResponse } from "next/server";

const PUBLIC_ROUTES = ["/login", "/register", "/api/auth"];
const ONBOARDING_ROUTES = ["/onboarding"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get("access_token")?.value;

  // Allow public routes
  if (PUBLIC_ROUTES.some((route) => pathname.startsWith(route)) || pathname === "/") {
    return NextResponse.next();
  }

  // Protected app routes
  if (pathname.startsWith("/app") || ONBOARDING_ROUTES.some((r) => pathname.startsWith(r))) {
    if (!accessToken) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*", "/onboarding/:path*", "/login", "/register"],
};