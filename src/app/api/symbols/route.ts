import { NextResponse } from 'next/server';
import { SECTOR_SYMBOLS } from '@/lib/sectors';

/** Fetch S&P 500 symbol list from DataHub.io */
async function getSP500Symbols(): Promise<string[]> {
  try {
    const res = await fetch(
      'https://datahub.io/core/s-and-p-500-companies-financials/r/constituents.csv',
      { next: { revalidate: 86400 } },
    );
    const text = await res.text();
    const lines = text.split('\n').slice(1); // skip header
    return lines
      .map((l) => l.split(',')[0]?.trim())
      .filter(Boolean) as string[];
  } catch {
    return ['AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','AVGO','JPM','V'];
  }
}

/** Fetch NASDAQ symbol list from DataHub.io */
async function getNasdaqSymbols(): Promise<string[]> {
  try {
    const res = await fetch(
      'https://datahub.io/core/nasdaq-listings/r/nasdaq-listed.csv',
      { next: { revalidate: 86400 } },
    );
    const text = await res.text();
    const lines = text.split('\n').slice(1);
    return lines
      .map((l) => l.split(',')[0]?.trim())
      .filter(Boolean) as string[];
  } catch {
    return ['AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','AVGO','NFLX','COST'];
  }
}

/** Fetch KOSPI/KOSDAQ symbols from Naver Finance */
async function getKoreaSymbols(market: 'KOSPI' | 'KOSDAQ'): Promise<string[]> {
  const allCodes: string[] = [];
  const baseUrl =
    market === 'KOSPI'
      ? 'https://finance.naver.com/sise/sise_market_sum.nhn'
      : 'https://finance.naver.com/sise/sise_market_sum.nhn?sosok=1';

  for (let page = 1; page <= 4; page++) {
    try {
      const url = `${baseUrl}&page=${page}`;
      const res = await fetch(url, {
        headers: {
          'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
      });
      const html = await res.text();
      const matches = html.match(/\/item\/main\.naver\?code=(\d{6})/g) ?? [];
      matches.forEach((m) => {
        const code = m.match(/code=(\d{6})/)?.[1];
        if (code && !allCodes.includes(code)) allCodes.push(code);
      });
    } catch {
      break;
    }
  }

  return allCodes.slice(0, 200).map((c) => `${c}.KS`);
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const market = searchParams.get('market') ?? 'SP500';

  try {
    let symbols: string[] = [];

    if (market === 'SP500') {
      symbols = await getSP500Symbols();
    } else if (market === 'NASDAQ') {
      symbols = await getNasdaqSymbols();
    } else if (market === 'ALL') {
      const [sp, nd] = await Promise.all([getSP500Symbols(), getNasdaqSymbols()]);
      symbols = Array.from(new Set([...sp, ...nd]));
    } else if (market === 'KOSPI') {
      symbols = await getKoreaSymbols('KOSPI');
    } else if (market === 'KOSDAQ') {
      symbols = await getKoreaSymbols('KOSDAQ');
    } else if (SECTOR_SYMBOLS[market]) {
      symbols = SECTOR_SYMBOLS[market];
    } else {
      symbols = await getSP500Symbols();
    }

    return NextResponse.json({ symbols });
  } catch (err) {
    console.error('[symbols]', err);
    return NextResponse.json({ symbols: [] }, { status: 500 });
  }
}
