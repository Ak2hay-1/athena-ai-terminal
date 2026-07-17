import { create } from "zustand";

type RightPanelMode = "assistant" | "hidden";

interface UiState {
  sidebarCollapsed: boolean;
  mobileNavOpen: boolean;
  rightPanel: RightPanelMode;
  notificationsOpen: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (value: boolean) => void;
  setMobileNavOpen: (value: boolean) => void;
  setRightPanel: (value: RightPanelMode) => void;
  toggleRightPanel: () => void;
  setNotificationsOpen: (value: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  mobileNavOpen: false,
  rightPanel: "assistant",
  notificationsOpen: false,
  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
  setMobileNavOpen: (mobileNavOpen) => set({ mobileNavOpen }),
  setRightPanel: (rightPanel) => set({ rightPanel }),
  toggleRightPanel: () =>
    set((state) => ({
      rightPanel: state.rightPanel === "assistant" ? "hidden" : "assistant",
    })),
  setNotificationsOpen: (notificationsOpen) => set({ notificationsOpen }),
}));
