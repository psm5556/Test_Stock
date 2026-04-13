import type { OHLCVBar, MALines, AnalysisResult } from '@/types';
import { PERIOD_LABELS, PERIOD_DAYS } from '@/types';
import { COMPANY_NAMES } from './sectors';

/** Calculate a simple moving average over the closes array. Returns null for insufficient data. */
function calcMA(closes: number[], window: number): (number | null)[] {
  return closes.map((_, i) => {
    if (i < window - 1) return null;
    const slice = closes.slice(i - window + 1, i + 1);
    return slice.reduce((a, b) => a + b, 0) / window;
  });
}

/** Compute all MA lines */
export function computeMALines(closes: number[]): MALines {
  return {
    ma20: calcMA(closes, 20),
    ma60: calcMA(closes, 60),
    ma125: calcMA(closes, 125),
    ma200: calcMA(closes, 200),
    ma240: calcMA(closes, 240),
    ma365: calcMA(closes, 365),
  };
}

/** Golden cross: MA20 crosses above MA60 (both below MA125) within last 10 bars. */
function checkGoldenCross(
  ma20: (number | null)[],
  ma60: (number | null)[],
  ma125: (number | null)[],
  dates: string[],
): { detected: boolean; date: string | null } {
  const len = ma20.length;
  const lookback = Math.min(10, len - 1);

  for (let i = len - lookback; i < len; i++) {
    const p20 = ma20[i - 1], c20 = ma20[i];
    const p60 = ma60[i - 1], c60 = ma60[i];
    const c125 = ma125[i];
    if (p20 == null || c20 == null || p60 == null || c60 == null || c125 == null) continue;

    const golden =
      p20 <= p60 &&   // before: MA20 ≤ MA60
      c20 > c60 &&    // after:  MA20 > MA60
      c20 < c125 &&   // MA20 still below MA125
      c60 < c125;     // MA60 still below MA125

    if (golden) return { detected: true, date: dates[i] ?? null };
  }
  return { detected: false, date: null };
}

/** Current price above MA20 and MA60. */
function checkAboveMALines(closes: number[], ma20: (number | null)[], ma60: (number | null)[]): boolean {
  const last = closes.length - 1;
  const price = closes[last];
  const m20 = ma20[last];
  const m60 = ma60[last];
  if (m20 == null || m60 == null) return false;
  return price > m20 && price > m60;
}

/** At least 2 of the last 5 candle bodies sit above MA125. */
function checkMA125Support(bars: OHLCVBar[], ma125: (number | null)[]): { supported: boolean; count: number } {
  const recent = bars.slice(-5);
  const recentMa = ma125.slice(-5);
  let count = 0;
  for (let i = 0; i < recent.length; i++) {
    const ma = recentMa[i];
    if (ma == null) continue;
    const bodyLow = Math.min(recent[i].open, recent[i].close);
    if (bodyLow > ma) count++;
  }
  return { supported: count >= 2, count };
}

/** MA20 and MA60 both trending up over last 10 bars, and MA20 > MA60. */
function checkTrendStability(ma20: (number | null)[], ma60: (number | null)[]): boolean {
  const r20 = ma20.slice(-10).filter((v): v is number => v != null);
  const r60 = ma60.slice(-10).filter((v): v is number => v != null);
  if (r20.length < 2 || r60.length < 2) return false;
  const slope20 = r20[r20.length - 1] - r20[0];
  const slope60 = r60[r60.length - 1] - r60[0];
  return slope20 > 0 && slope60 > 0 && r20[r20.length - 1] > r60[r60.length - 1];
}

/** Full analysis for one symbol given its OHLCV bars. */
export function analyzeStock(
  symbol: string,
  allBars: OHLCVBar[],
  period: string,
  companyName?: string,
): AnalysisResult | null {
  if (!allBars || allBars.length < 20) return null;

  const closes = allBars.map((b) => b.close);
  const maLines = computeMALines(closes);

  // Slice display bars by period
  const days = PERIOD_DAYS[period as keyof typeof PERIOD_DAYS] ?? 180;
  const displayBars = allBars.slice(-days);
  const displayCloses = displayBars.map((b) => b.close);
  const displayDates = displayBars.map((b) => b.time);

  // Compute MAs on full data, then take the same tail slice
  const sliceMA = (arr: (number | null)[]) => arr.slice(-displayBars.length);
  const displayMA = {
    ma20: sliceMA(maLines.ma20),
    ma60: sliceMA(maLines.ma60),
    ma125: sliceMA(maLines.ma125),
    ma200: sliceMA(maLines.ma200),
    ma240: sliceMA(maLines.ma240),
    ma365: sliceMA(maLines.ma365),
  };

  const { detected: goldenCross, date: crossDate } = checkGoldenCross(
    displayMA.ma20, displayMA.ma60, displayMA.ma125, displayDates,
  );
  const aboveMALines = checkAboveMALines(displayCloses, displayMA.ma20, displayMA.ma60);
  const { supported: ma125Support, count: supportCount } = checkMA125Support(displayBars, displayMA.ma125);
  const trendStable = checkTrendStability(displayMA.ma20, displayMA.ma60);

  const score =
    (goldenCross ? 25 : 0) +
    (aboveMALines ? 25 : 0) +
    (ma125Support ? 25 : 0) +
    (trendStable ? 25 : 0);

  return {
    symbol,
    companyName: companyName ?? COMPANY_NAMES[symbol] ?? symbol,
    currentPrice: displayCloses[displayCloses.length - 1],
    goldenCross,
    crossDate,
    aboveMALines,
    ma125Support,
    supportCount,
    trendStable,
    score,
    period,
    periodLabel: PERIOD_LABELS[period as keyof typeof PERIOD_LABELS] ?? period,
    bars: displayBars,
    maLines: displayMA,
  };
}
