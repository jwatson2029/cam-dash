import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "TikTok Pulse — Real-Time Video Analytics",
  description: "Paste any public TikTok video URL and instantly get real-time analytics. Views, likes, comments, shares — no login required.",
  keywords: ["tiktok analytics", "tiktok views", "tiktok stats", "video analytics"],
  openGraph: {
    title: "TikTok Pulse — Real-Time Video Analytics",
    description: "Instant TikTok video analytics. No login required.",
    type: "website",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "TikTok Pulse",
    description: "Real-time TikTok video analytics dashboard",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-950 text-slate-50 antialiased">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Toaster
          theme="dark"
          position="bottom-right"
          toastOptions={{
            style: {
              background: "rgb(15 23 42)",
              border: "1px solid rgb(30 41 59)",
              color: "rgb(248 250 252)",
            },
          }}
        />
      </body>
    </html>
  );
}
