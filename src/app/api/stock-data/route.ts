import { NextResponse } from 'next/server';
import { fetchYahooOHLCV } from '@/lib/yahoo';
import { COMPANY_NAMES } from '@/lib/sectors';

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const symbol = searchParams.get('symbol');
  const period = searchParams.get('period') ?? '6mo';

  if (!symbol) {
    return NextResponse.json({ error: 'symbol required' }, { status: 400 });
  }

  try {
    const bars = await fetchYahooOHLCV(symbol, period);
    const companyName = COMPANY_NAMES[symbol] ?? symbol;
    return NextResponse.json({ symbol, companyName, bars });
  } catch (err) {
    console.error(`[stock-data] ${symbol}:`, err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
