import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface OnboardingStatus {
  should_complete_onboarding: boolean;
}

class OnboardingService {
  async getStatus(): Promise<OnboardingStatus> {
    const { data } = await api.get<OnboardingStatus>("/onboarding/status");
    return data;
  }
}

export const onboardingService = new OnboardingService();
