import { NextResponse } from 'next/server';
import type { FearGreedData } from '@/types';

const CNN_URL = 'https://production.dataviz.cnn.io/index/fearandgreed/graphdata';

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const days = parseInt(searchParams.get('days') ?? '180', 10);

  try {
    const res = await fetch(`${CNN_URL}?start=0&end=${days}`, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        Accept: 'application/json',
        Referer: 'https://edition.cnn.com/',
      },
      next: { revalidate: 600 },
    });

    if (!res.ok) throw new Error(`CNN API ${res.status}`);

    const data = await res.json();

    const currentValue: number = data?.fear_and_greed?.score ?? 50;
    const currentLabel: string = data?.fear_and_greed?.rating ?? 'Neutral';

    const histRaw: { x: number; y: number }[] =
      data?.fear_and_greed_historical?.data ?? [];

    const history = histRaw.map((pt) => ({
      date: new Date(pt.x).toISOString().slice(0, 10),
      value: pt.y,
    }));

    const result: FearGreedData = {
      current: currentValue,
      label: currentLabel,
      history,
    };

    return NextResponse.json(result);
  } catch (err) {
    console.error('[fear-greed]', err);
    return NextResponse.json(
      { current: 50, label: 'Neutral', history: [] } satisfies FearGreedData,
      { status: 200 },
    );
  }
}
