import type { NextConfig } from "next";

// When NEXT_PUBLIC_BASE_PATH is set (e.g. GitHub Pages build), we do a full
// static export at that sub-path.  For Vercel / localhost the default is "".
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  ...(basePath ? { basePath, assetPrefix: basePath } : {}),
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
