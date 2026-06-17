import { create } from 'zustand';
import { apiClient } from '../api/apiClient';

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  display_name: string;
  city: string;
  country: string;
  privacy_level: 'public' | 'friends' | 'anonymous';
  onboarding_complete: boolean;
}

export interface AppState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoadingUser: boolean;
  activeTab: string;
  toast: { message: string; type: 'success' | 'error' | 'info' } | null;
  
  // Actions
  setUser: (user: UserProfile | null) => void;
  setIsAuthenticated: (auth: boolean) => void;
  setLoadingUser: (loading: boolean) => void;
  setActiveTab: (tab: string) => void;
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
  clearToast: () => void;
  fetchUser: () => Promise<UserProfile | null>;
  logout: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoadingUser: false,
  activeTab: 'dashboard',
  toast: null,

  setUser: (user) => set({ user }),
  setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
  setLoadingUser: (isLoadingUser) => set({ isLoadingUser }),
  setActiveTab: (activeTab) => set({ activeTab }),
  showToast: (message, type = 'success') => {
    set({ toast: { message, type } });
    setTimeout(() => {
      if (get().toast?.message === message) {
        set({ toast: null });
      }
    }, 4000);
  },
  clearToast: () => set({ toast: null }),

  fetchUser: async () => {
    set({ isLoadingUser: true });
    try {
      const profile = await apiClient.request<UserProfile>('/accounts/profile/');
      set({ user: profile, isAuthenticated: true });
      // If onboarding is incomplete, switch to calculator
      if (!profile.onboarding_complete) {
        set({ activeTab: 'calculator' });
      }
      return profile;
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      set({ user: null, isAuthenticated: false });
      apiClient.clearTokens();
      return null;
    } finally {
      set({ isLoadingUser: false });
    }
  },

  logout: async () => {
    try {
      const { refreshToken } = apiClient.getTokens();
      if (refreshToken) {
        await apiClient.request('/accounts/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh: refreshToken }),
        });
      }
    } catch (err) {
      console.warn('Logout request failed, cleaning tokens locally anyway.', err);
    } finally {
      apiClient.clearTokens();
      set({ user: null, isAuthenticated: false, activeTab: 'dashboard' });
      get().showToast('Logged out successfully', 'info');
    }
  },
}));
