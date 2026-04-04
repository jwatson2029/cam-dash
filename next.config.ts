import type { NextConfig } from "next";

// When NEXT_PUBLIC_BASE_PATH is set (e.g. GitHub Pages build), we do a full
// static export at that sub-path.  For Vercel / localhost the default is "".
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  // Only do a static export when building for GitHub Pages (basePath set).
  // On Vercel / localhost we keep server-side rendering so API routes work.
  ...(basePath
    ? { output: "export" as const, trailingSlash: true, basePath, assetPrefix: basePath }
    : {}),
  images: {
    // next/image optimisation is not available in static exports
    unoptimized: true,
    remotePatterns: [
      { protocol: "https", hostname: "**.tiktokcdn.com" },
      { protocol: "https", hostname: "**.tiktokcdn-us.com" },
      { protocol: "https", hostname: "picsum.photos" },
      { protocol: "https", hostname: "api.dicebear.com" },
    ],
  },
};

export default nextConfig;
