import { create } from 'zustand'

interface UIStore {
  commandPaletteOpen: boolean
  mobileSidebarOpen: boolean
  setCommandPaletteOpen: (open: boolean) => void
  setMobileSidebarOpen: (open: boolean) => void
  toggleCommandPalette: () => void
  toggleMobileSidebar: () => void
}

export const useUIStore = create<UIStore>((set) => ({
  commandPaletteOpen: false,
  mobileSidebarOpen: false,
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),
  toggleCommandPalette: () => set(s => ({ commandPaletteOpen: !s.commandPaletteOpen })),
  toggleMobileSidebar: () => set(s => ({ mobileSidebarOpen: !s.mobileSidebarOpen })),
}))
