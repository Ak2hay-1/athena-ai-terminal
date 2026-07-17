import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number, digits = 0) {
  return `${value.toFixed(digits)}%`;
}

export function formatPrice(value: number, digits = 2) {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function applyQuoteToCandle<T extends {
  open: number;
  high: number;
  low: number;
  close: number;
}>(candle: T, mid: number): T {
  if (!mid) return candle;
  return {
    ...candle,
    close: mid,
    high: Math.max(candle.high, mid),
    low: Math.min(candle.low, mid),
  };
}

export function greetingForHour(hour = new Date().getHours()) {
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}
