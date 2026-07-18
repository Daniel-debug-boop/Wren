import { create } from "zustand";

interface UIState {
  leftOpen: boolean;
  rightOpen: boolean;
  bottomOpen: boolean;
  paletteOpen: boolean;
  leftWidth: number;
  rightWidth: number;
  bottomHeight: number;
  toggleLeft: () => void;
  toggleRight: () => void;
  toggleBottom: () => void;
  setPalette: (v: boolean) => void;
  setLeftWidth: (w: number) => void;
  setRightWidth: (w: number) => void;
  setBottomHeight: (h: number) => void;
}

export const useUIStore = create<UIState>((set) => ({
  leftOpen: true,
  rightOpen: true,
  bottomOpen: false,
  paletteOpen: false,
  leftWidth: 288,
  rightWidth: 360,
  bottomHeight: 260,
  toggleLeft: () => set((s) => ({ leftOpen: !s.leftOpen })),
  toggleRight: () => set((s) => ({ rightOpen: !s.rightOpen })),
  toggleBottom: () => set((s) => ({ bottomOpen: !s.bottomOpen })),
  setPalette: (v) => set({ paletteOpen: v }),
  setLeftWidth: (w) => set({ leftWidth: Math.max(200, Math.min(480, w)) }),
  setRightWidth: (w) => set({ rightWidth: Math.max(280, Math.min(560, w)) }),
  setBottomHeight: (h) =>
    set({ bottomHeight: Math.max(160, Math.min(520, h)) }),
}));
