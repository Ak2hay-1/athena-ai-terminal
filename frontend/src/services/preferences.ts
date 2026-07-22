import { apiFetch } from "@/services/api-client";

export type UserPreferences = {
  user_id: number;
  timezone: string;
  language: string;
  trading_style: string;
  risk_profile: string;
  preferred_channel: string;
  notification_frequency: string;
  quiet_hours_start: string;
  quiet_hours_end: string;
  preferred_sessions: string[];
  preferred_timeframes: string[];
  preferred_strategies: string[];
  ignored_symbols: string[];
  favorite_assets: string[];
  preferred_rr: number | null;
  telegram_chat_id: string | null;
  discord_webhook_url: string | null;
  email_override: string | null;
  auto_trade_enabled: boolean;
  auto_trade_symbols: string[];
  auto_trade_timeframes: string[];
  auto_trade_min_confidence: number;
  auto_trade_min_confluence: number;
  auto_trade_min_rr: number;
  auto_trade_volume: number;
};

export type PreferencesUpdate = Partial<{
  timezone: string;
  language: string;
  trading_style: string;
  risk_profile: string;
  preferred_channel: string;
  notification_frequency: string;
  quiet_hours_start: string;
  quiet_hours_end: string;
  preferred_sessions: string[];
  preferred_timeframes: string[];
  preferred_strategies: string[];
  ignored_symbols: string[];
  favorite_assets: string[];
  preferred_rr: number | null;
  telegram_chat_id: string | null;
  discord_webhook_url: string | null;
  email_override: string | null;
  auto_trade_enabled: boolean;
  auto_trade_symbols: string[];
  auto_trade_timeframes: string[];
  auto_trade_min_confidence: number;
  auto_trade_min_confluence: number;
  auto_trade_min_rr: number;
  auto_trade_volume: number;
}>;

export const PREFERENCES_QUERY_KEY = ["preferences"] as const;

export async function getPreferences(): Promise<UserPreferences> {
  return apiFetch<UserPreferences>("/preferences");
}

export async function updatePreferences(
  payload: PreferencesUpdate,
): Promise<UserPreferences> {
  return apiFetch<UserPreferences>("/preferences", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export type AutoTradeFilters = {
  auto_trade_enabled: boolean;
  auto_trade_symbols: string[];
  auto_trade_timeframes: string[];
  auto_trade_min_confidence: number;
  auto_trade_min_confluence: number;
  auto_trade_min_rr: number;
  auto_trade_volume: number;
};

export function autoTradeFromPreferences(
  prefs: UserPreferences,
): AutoTradeFilters {
  return {
    auto_trade_enabled: Boolean(prefs.auto_trade_enabled),
    auto_trade_symbols: [...(prefs.auto_trade_symbols ?? [])],
    auto_trade_timeframes: [...(prefs.auto_trade_timeframes ?? [])],
    auto_trade_min_confidence: prefs.auto_trade_min_confidence ?? 70,
    auto_trade_min_confluence: prefs.auto_trade_min_confluence ?? 0,
    auto_trade_min_rr: prefs.auto_trade_min_rr ?? 0,
    auto_trade_volume: prefs.auto_trade_volume ?? 0.01,
  };
}

export const DEFAULT_AUTO_TRADE: AutoTradeFilters = {
  auto_trade_enabled: false,
  auto_trade_symbols: [],
  auto_trade_timeframes: [],
  auto_trade_min_confidence: 70,
  auto_trade_min_confluence: 0,
  auto_trade_min_rr: 0,
  auto_trade_volume: 0.01,
};
