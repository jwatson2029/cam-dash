# TikTok Pulse 🎵

A premium TikTok Video Analytics Dashboard — paste any public TikTok URL and get instant real-time stats. No login. No API keys.

## Features

- 📊 Real-time view counts, likes, comments, shares, saves
- 🎨 Beautiful dark UI (Vercel + Linear inspired)
- 📱 Fully responsive
- 🔒 Rate limiting (10 req/min per IP)
- 💾 History stored in localStorage
- ⚡ Keyboard shortcut: Cmd/Ctrl+K to focus input
- 📤 Export as JSON or CSV

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/jwatson2029/cam-dash)

Or manually:
```bash
npm install -g vercel
vercel --prod
```

## Tech Stack

- **Next.js 16** (App Router)
- **TypeScript** (strict)
- **Tailwind CSS v4**
- **shadcn/ui** + Radix UI
- **Framer Motion**
- **Zustand** (state)
- **Sonner** (toasts)
- **Lucide React** (icons)
