import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value}%`;
}

export function formatDiscount(type: string, value: number | null, unit: string): string {
  if (!value) return type;
  if (unit === "percent") return `${value}% Off`;
  if (unit === "dollar") return `$${value} Off`;
  return type;
}

export function formatDate(date: string | null | undefined): string {
  if (!date) return "—";
  return new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function formatRelative(date: string | null | undefined): string {
  if (!date) return "—";
  const diff = Date.now() - new Date(date).getTime();
  const hours = Math.floor(diff / 3_600_000);
  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return formatDate(date);
}

export const DEAL_TYPE_LABELS: Record<string, string> = {
  percent_off: "% Off",
  dollar_off: "$ Off",
  bogo: "BOGO",
  bundle: "Bundle",
  first_time: "First-Time",
  daily: "Daily Deal",
  other: "Deal",
};

export const CATEGORY_LABELS: Record<string, string> = {
  flower: "Flower",
  preroll: "Pre-Rolls",
  edible: "Edibles",
  concentrate: "Concentrates",
  vape: "Vapes",
  tincture: "Tinctures",
  topical: "Topicals",
  accessories: "Accessories",
};

export const NJ_COUNTIES = [
  "Atlantic", "Bergen", "Burlington", "Camden", "Cape May",
  "Cumberland", "Essex", "Gloucester", "Hudson", "Hunterdon",
  "Mercer", "Middlesex", "Monmouth", "Morris", "Ocean",
  "Passaic", "Salem", "Somerset", "Sussex", "Union", "Warren",
];
