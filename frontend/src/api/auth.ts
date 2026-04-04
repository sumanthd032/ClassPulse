import api from "./client";
import type { TokenResponse, User } from "@/types";

export const authApi = {
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    role: string;
  }) => api.post<TokenResponse>("/auth/register", data).then((r) => r.data),

  login: (email: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { email, password }).then((r) => r.data),

  refresh: (refresh_token: string) =>
    api
      .post<TokenResponse>("/auth/refresh", { refresh_token })
      .then((r) => r.data),

  me: () => api.get<User>("/auth/me").then((r) => r.data),
};
