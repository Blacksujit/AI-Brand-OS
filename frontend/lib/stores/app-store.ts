import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PipelineRecord {
  pipelineId: string;
  topic: string;
  status: "running" | "complete" | "failed";
  startedAt: string;
}

interface AppState {
  sidebarCollapsed: boolean;
  activePipeline: PipelineRecord | null;
  pipelineHistory: PipelineRecord[];
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  setActivePipeline: (pipeline: PipelineRecord | null) => void;
  addPipelineHistory: (record: PipelineRecord) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      activePipeline: null,
      pipelineHistory: [],

      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }),

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setActivePipeline: (pipeline) =>
        set({ activePipeline: pipeline }),

      addPipelineHistory: (record) =>
        set((state) => ({
          pipelineHistory: [record, ...state.pipelineHistory].slice(0, 50),
        })),
    }),
    {
      name: "brandos-app-store",
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        pipelineHistory: state.pipelineHistory,
      }),
    },
  ),
);
