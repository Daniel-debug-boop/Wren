import axios, { type AxiosInstance } from "axios";

const BASE_URL = "/api/v1";

const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
  },
});

export default apiClient;
