"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/components/ui/Toaster";
import { Loader2, User, Lock, Save } from "lucide-react";

const profileSchema = z.object({
  name: z.string().min(2, "At least 2 characters"),
  email: z.string().email("Valid email required"),
});

const passwordSchema = z.object({
  current_password: z.string().min(1, "Enter current password"),
  new_password: z.string().min(8, "At least 8 characters"),
  confirm: z.string(),
}).refine((d) => d.new_password === d.confirm, {
  message: "Passwords don't match",
  path: ["confirm"],
});

type ProfileForm = z.infer<typeof profileSchema>;
type PasswordForm = z.infer<typeof passwordSchema>;

function ProfileSection() {
  const { user, refresh } = useAuth();
  const { toast } = useToast();

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: { name: user?.name || "", email: user?.email || "" },
  });

  const onSubmit = async (data: ProfileForm) => {
    try {
      await api.patch("/users/me", data);
      await refresh();
      toast("Profile updated!", "success");
    } catch {
      toast("Failed to update profile", "error");
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-5">
        <User className="w-5 h-5 text-brand-700" />
        <h2 className="font-semibold text-gray-900">Profile</h2>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-md">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            type="text"
            {...register("name")}
            className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700"
          />
          {errors.name && <p className="text-xs text-red-600 mt-1">{errors.name.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            {...register("email")}
            className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700"
          />
          {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email.message}</p>}
        </div>
        <div className="pt-1">
          <p className="text-xs text-gray-400">Role: <span className="font-medium text-gray-600">{user?.role}</span></p>
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex items-center gap-2 bg-brand-950 text-white rounded-lg px-4 py-2.5 text-sm font-semibold hover:bg-brand-900 disabled:opacity-60"
        >
          {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Save changes
        </button>
      </form>
    </div>
  );
}

function PasswordSection() {
  const { toast } = useToast();

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  });

  const onSubmit = async (data: PasswordForm) => {
    try {
      await api.post("/auth/change-password", {
        current_password: data.current_password,
        new_password: data.new_password,
      });
      toast("Password changed!", "success");
      reset();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast(msg || "Failed to change password", "error");
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-5">
        <Lock className="w-5 h-5 text-brand-700" />
        <h2 className="font-semibold text-gray-900">Change Password</h2>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-md">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Current password</label>
          <input
            type="password"
            {...register("current_password")}
            className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700"
          />
          {errors.current_password && <p className="text-xs text-red-600 mt-1">{errors.current_password.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">New password</label>
          <input
            type="password"
            {...register("new_password")}
            className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700"
          />
          {errors.new_password && <p className="text-xs text-red-600 mt-1">{errors.new_password.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Confirm new password</label>
          <input
            type="password"
            {...register("confirm")}
            className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700"
          />
          {errors.confirm && <p className="text-xs text-red-600 mt-1">{errors.confirm.message}</p>}
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex items-center gap-2 bg-brand-950 text-white rounded-lg px-4 py-2.5 text-sm font-semibold hover:bg-brand-900 disabled:opacity-60"
        >
          {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
          Update password
        </button>
      </form>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your account and preferences</p>
      </div>
      <ProfileSection />
      <PasswordSection />
    </div>
  );
}
