import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { VideoData } from "./scraper";

export interface AnalysisRecord {
  id: string;
  url: string;
  data: VideoData;
  analyzedAt: number;
}

interface AnalysisStore {
  currentResult: VideoData | null;
  currentUrl: string;
  isLoading: boolean;
  error: string | null;
  history: AnalysisRecord[];
  setCurrentResult: (result: VideoData, url: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addToHistory: (url: string, data: VideoData) => void;
  loadFromHistory: (record: AnalysisRecord) => void;
  clearHistory: () => void;
  reset: () => void;
}

export const useAnalysisStore = create<AnalysisStore>()(
  persist(
    (set) => ({
      currentResult: null,
      currentUrl: "",
      isLoading: false,
      error: null,
      history: [],

      setCurrentResult: (result, url) =>
        set({ currentResult: result, currentUrl: url, isLoading: false, error: null }),

      setLoading: (loading) => set({ isLoading: loading, error: null }),

      setError: (error) => set({ error, isLoading: false }),

      addToHistory: (url, data) =>
        set((state) => {
          const record: AnalysisRecord = {
            id: data.id,
            url,
            data,
            analyzedAt: Date.now(),
          };
          const filtered = state.history.filter((h) => h.id !== data.id);
          return { history: [record, ...filtered].slice(0, 10) };
        }),

      loadFromHistory: (record) =>
        set({ currentResult: record.data, currentUrl: record.url, error: null }),

      clearHistory: () => set({ history: [] }),

      reset: () => set({ currentResult: null, currentUrl: "", error: null }),
    }),
    {
      name: "tiktok-pulse-history",
      partialize: (state) => ({ history: state.history }),
    }
  )
);
