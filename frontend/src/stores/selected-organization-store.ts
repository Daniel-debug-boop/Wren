import { create } from "zustand";

interface SelectedOrganizationState {
  organizationId: string | null;
  setOrganizationId: (id: string | null) => void;
}

export const useSelectedOrganizationStore = create<SelectedOrganizationState>(
  (set) => ({
    organizationId: null,
    setOrganizationId: (organizationId) => set({ organizationId }),
  }),
);
