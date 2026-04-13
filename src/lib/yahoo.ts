import type { OHLCVBar } from '@/types';

const YAHOO_BASE = 'https://query1.finance.yahoo.com';

/** Map period key → Yahoo Finance range string */
const PERIOD_TO_RANGE: Record<string, string> = {
  '1mo': '3mo',   // fetch extra for MA calculation
  '3mo': '1y',
  '6mo': '2y',
  '1y': '3y',
  '2y': '5y',
  '5y': 'max',
};

/** Fetch OHLCV data for a symbol from Yahoo Finance (server-side only). */
export async function fetchYahooOHLCV(symbol: string, period: string): Promise<OHLCVBar[]> {
  const range = PERIOD_TO_RANGE[period] ?? '2y';
  const url = `${YAHOO_BASE}/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=${range}`;

  const res = await fetch(url, {
    headers: {
      'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      Accept: 'application/json',
    },
    next: { revalidate: 300 }, // cache 5 min
  });

  if (!res.ok) throw new Error(`Yahoo Finance returned ${res.status} for ${symbol}`);

  const json = await res.json();
  const result = json?.chart?.result?.[0];
  if (!result) throw new Error(`No data for ${symbol}`);

  const timestamps: number[] = result.timestamp ?? [];
  const quote = result.indicators?.quote?.[0] ?? {};
  const opens: number[] = quote.open ?? [];
  const highs: number[] = quote.high ?? [];
  const lows: number[] = quote.low ?? [];
  const closes: number[] = quote.close ?? [];
  const volumes: number[] = quote.volume ?? [];

  const bars: OHLCVBar[] = [];
  for (let i = 0; i < timestamps.length; i++) {
    const o = opens[i], h = highs[i], l = lows[i], c = closes[i], v = volumes[i];
    if (o == null || h == null || l == null || c == null) continue;
    const date = new Date(timestamps[i] * 1000);
    bars.push({
      time: date.toISOString().slice(0, 10),
      open: o,
      high: h,
      low: l,
      close: c,
      volume: v ?? 0,
    });
  }

  return bars;
}

/** Fetch company long name from Yahoo Finance info endpoint. */
export async function fetchCompanyName(symbol: string): Promise<string> {
  try {
    const url = `${YAHOO_BASE}/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      next: { revalidate: 3600 },
    });
    const json = await res.json();
    const meta = json?.chart?.result?.[0]?.meta;
    return meta?.longName ?? meta?.shortName ?? symbol;
  } catch {
    return symbol;
  }
}
