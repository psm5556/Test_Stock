import { NextResponse } from 'next/server';

/** Simple CSV line parser that handles quoted fields */
function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      // Handle escaped double-quote ("")
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}

/** Strip surrounding quotes from a cell value */
function stripQuotes(s: string): string {
  return s.replace(/^"+|"+$/g, '').trim();
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);

  // sheetId: from query param or env var
  // || 사용: 빈 문자열('')도 환경변수로 폴백되도록 (??는 null/undefined만 처리)
  const sheetId = searchParams.get('sheetId')?.trim() || process.env.GOOGLE_SHEET_ID || '';
  // sheetName: from query param or env var (default: Sheet1)
  const sheetName = searchParams.get('sheetName')?.trim() || process.env.GOOGLE_SHEET_NAME || '';

  if (!sheetId) {
    return NextResponse.json({ error: 'sheetId가 필요합니다.' }, { status: 400 });
  }

  // Google Sheets Visualization API (CSV export) – no auth required for public sheets
  const gvizUrl =
    `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:csv` +
    (sheetName ? `&sheet=${encodeURIComponent(sheetName)}` : '');

  try {
    const res = await fetch(gvizUrl, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
      },
      cache: 'no-store',
    });

    if (!res.ok) {
      throw new Error(`Google Sheets API 응답 오류: ${res.status}`);
    }

    const csv = await res.text();
    const lines = csv
      .split('\n')
      .map((l) => l.trimEnd())
      .filter(Boolean);

    if (lines.length < 2) {
      return NextResponse.json({ symbols: [], names: {} });
    }

    // Parse header row
    const headers = parseCSVLine(lines[0]).map(stripQuotes);

    // Find ticker and company name column indices
    // Accepts: '티커', 'ticker', 'symbol', 'Ticker', 'Symbol'
    const tickerIdx = headers.findIndex((h) =>
      ['티커', 'ticker', 'symbol', 'Ticker', 'Symbol', 'TICKER', 'SYMBOL'].includes(h),
    );
    // Accepts: '기업명', '회사명', 'name', 'company', 'Name', 'Company'
    const nameIdx = headers.findIndex((h) =>
      ['기업명', '회사명', '종목명', 'name', 'company', 'Name', 'Company', 'NAME', 'COMPANY'].includes(h),
    );

    if (tickerIdx === -1) {
      return NextResponse.json(
        {
          error: `'티커' 컬럼을 찾을 수 없습니다. 현재 헤더: ${headers.join(', ')}`,
        },
        { status: 400 },
      );
    }

    const symbols: string[] = [];
    const names: Record<string, string> = {};

    for (let i = 1; i < lines.length; i++) {
      const cols = parseCSVLine(lines[i]).map(stripQuotes);
      const ticker = cols[tickerIdx] ?? '';
      if (!ticker) continue;

      symbols.push(ticker);
      if (nameIdx !== -1 && cols[nameIdx]) {
        names[ticker] = cols[nameIdx];
      }
    }

    return NextResponse.json({ symbols, names, total: symbols.length });
  } catch (err) {
    console.error('[sheets]', err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
