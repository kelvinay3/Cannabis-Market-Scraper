"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Leaf, Eye, EyeOff, Loader2 } from "lucide-react";

const schema = z.object({
  name: z.string().min(2, "Enter your name"),
  password: z.string().min(8, "At least 8 characters"),
  confirm: z.string(),
}).refine((d) => d.password === d.confirm, {
  message: "Passwords don't match",
  path: ["confirm"],
});

type FormData = z.infer<typeof schema>;

function InviteForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const { refresh } = useAuth();
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setError("");
    try {
      const { data: res } = await api.post("/users/accept-invite", {
        token,
        name: data.name,
        password: data.password,
      });
      localStorage.setItem("access_token", res.access_token);
      await refresh();
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Invite expired or invalid. Request a new one.");
    }
  };

  if (!token) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-red-600 font-medium">No invite token found in the URL.</p>
        <p className="text-xs text-gray-500 mt-2">Ask your admin to resend the invite.</p>
      </div>
    );
  }

  return (
    <>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Accept your invite</h1>
      <p className="text-sm text-gray-500 mb-6">Set up your account to get started.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Your name</label>
          <input
            type="text"
            autoComplete="name"
            {...register("name")}
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-950"
            placeholder="Jane Smith"
          />
          {errors.name && <p className="text-xs text-red-600 mt-1">{errors.name.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <div className="relative">
            <input
              type={showPw ? "text" : "password"}
              autoComplete="new-password"
              {...register("password")}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-950 pr-10"
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPw((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
            >
              {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Confirm password</label>
          <input
            type="password"
            autoComplete="new-password"
            {...register("confirm")}
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-950"
            placeholder="••••••••"
          />
          {errors.confirm && <p className="text-xs text-red-600 mt-1">{errors.confirm.message}</p>}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2.5 text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-brand-950 hover:bg-brand-900 text-white font-semibold rounded-lg py-2.5 text-sm transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
          Create account
        </button>
      </form>
    </>
  );
}

export default function InvitePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-950 to-green-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-10 h-10 bg-brand-950 rounded-xl flex items-center justify-center">
            <Leaf className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-gray-900 text-lg leading-none">NJ Cannabis Intel</div>
            <div className="text-xs text-gray-500 mt-0.5">You've been invited</div>
          </div>
        </div>
        <Suspense fallback={<div className="h-32 flex items-center justify-center"><div className="w-6 h-6 border-2 border-brand-950 border-t-transparent rounded-full animate-spin" /></div>}>
          <InviteForm />
        </Suspense>
      </div>
    </div>
  );
}
