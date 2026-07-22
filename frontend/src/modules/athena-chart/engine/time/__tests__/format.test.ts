import { describe, expect, it } from "vitest";
import {
  formatCrosshairTime,
  formatPriceLabel,
  formatTimeLabel,
} from "../../../utils/format";

describe("formatPriceLabel precision", () => {
  it("uses 5 decimals for EURUSD", () => {
    expect(formatPriceLabel(1.08425, "EURUSD")).toBe("1.08425");
  });

  it("uses 3 decimals for USDJPY", () => {
    expect(formatPriceLabel(149.123, "USDJPY")).toBe("149.123");
  });

  it("uses 2 decimals for XAUUSD", () => {
    expect(formatPriceLabel(2650.12, "XAUUSD")).toBe("2650.12");
  });
});

describe("formatTimeLabel adaptive", () => {
  const noon = Math.floor(Date.UTC(2026, 6, 21, 9, 30, 0) / 1000);

  it("shows HH:MM for short intraday spans", () => {
    const label = formatTimeLabel(noon, 3600);
    expect(label).toMatch(/^\d{2}:\d{2}$/);
  });

  it("shows month day for multi-day spans", () => {
    const label = formatTimeLabel(noon, 10 * 86_400);
    expect(label).toMatch(/^[A-Z][a-z]{2} \d{1,2}$/);
  });
});

describe("formatCrosshairTime", () => {
  it("returns local date and time with seconds", () => {
    const sec = Math.floor(Date.UTC(2026, 6, 18, 4, 13, 0) / 1000);
    const { date, time } = formatCrosshairTime(sec);
    expect(date).toMatch(/18 Jul 2026|17 Jul 2026|19 Jul 2026/); // TZ dependent
    expect(time).toMatch(/^\d{2}:\d{2}:\d{2}$/);
  });
});

describe("UTC construction vs local display", () => {
  it("bucket math uses UTC while labels use local", async () => {
    const { bucketStartUtcMs, isoFromUtcMs } = await import(
      "../../time/bucket"
    );
    const ms = Date.UTC(2026, 6, 21, 10, 7, 30);
    const start = bucketStartUtcMs(ms, "M5");
    expect(isoFromUtcMs(start)).toBe("2026-07-21T10:05:00.000Z");
    // Display formatter may shift by TZ but must not change the ISO bucket
    const label = formatTimeLabel(start / 1000, 3600);
    expect(label.length).toBeGreaterThan(0);
  });
});
