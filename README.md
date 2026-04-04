# TikTok Pulse 🎵

A premium TikTok Video Analytics Dashboard — paste any public TikTok URL and get instant real-time stats. No login. No API keys.

🌐 **Live Demo**: [https://jwatson2029.github.io/cam-dash](https://jwatson2029.github.io/cam-dash)

## Features

- 📊 Video stats: views, likes, comments, shares, saves
- 🎨 Beautiful dark UI (Vercel + Linear inspired)
- 📱 Fully responsive (mobile sidebar → bottom nav)
- 💾 History stored in localStorage (last 10 analyses)
- ⚡ Keyboard shortcut: Cmd/Ctrl+K to focus input
- 📤 Export as JSON or CSV
- 🖥️ Deployed to GitHub Pages automatically on every push

## How It Works

Paste a TikTok video URL → the app calls TikTok's public **oEmbed endpoint** to fetch the real video title, author, and thumbnail. Engagement stats are estimated from the video ID (TikTok does not expose a public stats API).

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Deploy to GitHub Pages

GitHub Pages deployment happens automatically via GitHub Actions on every push to `main`.

To enable it manually:
1. Go to **Settings → Pages** in your GitHub repo
2. Set Source to **GitHub Actions**
3. Push to `main` — the workflow builds & deploys automatically

The live site will be at `https://<your-username>.github.io/cam-dash/`.

## Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/jwatson2029/cam-dash)

Or manually:
```bash
npm install -g vercel
vercel --prod
```

## Tech Stack

- **Next.js 15** (App Router, static export)
- **TypeScript** (strict)
- **Tailwind CSS v4**
- **shadcn/ui** + Radix UI
- **Framer Motion**
- **Zustand** (state + localStorage)
- **Sonner** (toasts)
- **Lucide React** (icons)
