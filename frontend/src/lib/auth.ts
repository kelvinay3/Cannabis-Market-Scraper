import api from "./api";

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  org_id: string;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

export async function login(email: string, password: string): Promise<{ user: User; access_token: string }> {
  const { data } = await api.post("/auth/login", { email, password });
  localStorage.setItem("access_token", data.access_token);
  return data;
}

export async function logout() {
  try {
    await api.post("/auth/logout");
  } finally {
    localStorage.removeItem("access_token");
  }
}

export async function getMe(): Promise<User> {
  const { data } = await api.get("/auth/me");
  return data;
}

export function isAdmin(user: User) {
  return ["super_admin", "admin"].includes(user.role);
}

export function isSuperAdmin(user: User) {
  return user.role === "super_admin";
}
