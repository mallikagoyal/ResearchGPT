"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { TOKEN_STORAGE_KEY } from "@/lib/axios";
import { authService } from "@/services/auth-service";
import type { LoginPayload, RegisterPayload, User } from "@/types/auth";

interface AuthContextValue {
  user: User | null;
  /** True while the initial session check (or a login/register) is in flight. */
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const CURRENT_USER_QUERY_KEY = ["auth", "me"] as const;

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  // Tracks whether a token exists in localStorage at all, so we don't
  // fire GET /users/me for anonymous visitors on public pages.
  const [hasToken, setHasToken] = useState<boolean>(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHasToken(Boolean(window.localStorage.getItem(TOKEN_STORAGE_KEY)));
    setHydrated(true);
  }, []);

  const {
    data: user,
    isLoading: isUserLoading,
    isFetching,
  } = useQuery({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: authService.getCurrentUser,
    enabled: hydrated && hasToken,
    retry: false,
  });

  const persistSession = useCallback(
    (accessToken: string, loggedInUser: User) => {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
      setHasToken(true);
      queryClient.setQueryData(CURRENT_USER_QUERY_KEY, loggedInUser);
    },
    [queryClient]
  );

  const loginMutation = useMutation({
    mutationFn: authService.login,
    onSuccess: (data) => persistSession(data.access_token, data.user),
  });

  const registerMutation = useMutation({
    mutationFn: authService.register,
    onSuccess: (data) => persistSession(data.access_token, data.user),
  });

  const logout = useCallback(() => {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setHasToken(false);
    queryClient.setQueryData(CURRENT_USER_QUERY_KEY, null);
    queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
  }, [queryClient]);

  const login = useCallback(
    async (payload: LoginPayload) => {
      await loginMutation.mutateAsync(payload);
    },
    [loginMutation]
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      await registerMutation.mutateAsync(payload);
    },
    [registerMutation]
  );

  // Loading is "true" until we've both checked localStorage AND, if a
  // token existed, resolved whether it's still valid.
  const isLoading = !hydrated || (hasToken && isUserLoading && isFetching);

  const value: AuthContextValue = {
    user: user ?? null,
    isLoading,
    isAuthenticated: Boolean(user),
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
