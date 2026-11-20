import { apiClient } from "@/lib/axios";
import type { AuthResponse, LoginPayload, RegisterPayload, User } from "@/types/auth";

/**
 * Thin wrapper around the backend's auth endpoints. Components/hooks
 * should call these functions rather than using apiClient directly, so
 * the request/response shapes are defined in exactly one place.
 */
export const authService = {
  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const { data } = await apiClient.post<AuthResponse>("/auth/register", payload);
    return data;
  },

  async login(payload: LoginPayload): Promise<AuthResponse> {
    const { data } = await apiClient.post<AuthResponse>("/auth/login", payload);
    return data;
  },

  async getCurrentUser(): Promise<User> {
    const { data } = await apiClient.get<User>("/users/me");
    return data;
  },
};
