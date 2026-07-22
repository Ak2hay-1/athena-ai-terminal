export type MarketHoursStatus = {
  open: boolean;
  reason: string;
  nextOpen?: string;
};

/** FX / metals: Sun 22:00 UTC → Fri 22:00 UTC. */
export function getMarketHours(
  _symbol: string,
  date = new Date(),
): MarketHoursStatus {
  const day = date.getUTCDay(); // 0 Sun … 6 Sat
  const hour = date.getUTCHours();
  const minute = date.getUTCMinutes();
  const minutesUtc = hour * 60 + minute;

  const fridayClose = 22 * 60;
  const sundayOpen = 22 * 60;

  if (day === 6) {
    return {
      open: false,
      reason: "Weekend — FX/metals closed",
      nextOpen: "Sun 22:00 UTC",
    };
  }

  if (day === 0 && minutesUtc < sundayOpen) {
    return {
      open: false,
      reason: "Weekend — FX/metals closed",
      nextOpen: "Sun 22:00 UTC",
    };
  }

  if (day === 5 && minutesUtc >= fridayClose) {
    return {
      open: false,
      reason: "Weekend — FX/metals closed",
      nextOpen: "Sun 22:00 UTC",
    };
  }

  return { open: true, reason: "FX/metals session open" };
}

export function isMarketOpen(symbol: string, date = new Date()): boolean {
  return getMarketHours(symbol, date).open;
}
