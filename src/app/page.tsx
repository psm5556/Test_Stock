'use client';

import { useState, useCallback, useRef } from 'react';
import { Menu } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import FearGreedWidget from '@/components/FearGreedWidget';
import ResultsTable from '@/components/ResultsTable';
import StockDetail from '@/components/StockDetail';
import type {
  MarketKey,
  PeriodKey,
  AnalysisResult,
  FearGreedData,
  SheetConfig,
  OHLCVBar,
} from '@/types';
import { PERIOD_DAYS } from '@/types';
import { analyzeStock } from '@/lib/analysis';

const CONCURRENCY = 8;

async function fetchWithRetry(url: string, retries = 2): Promise<Response> {
  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url);
      if (res.ok || res.status === 404) return res;
      if (i < retries) await new Promise((r) => setTimeout(r, 500 * (i + 1)));
    } catch {
      if (i === retries) throw new Error(`fetch failed: ${url}`);
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
    }
  }
  throw new Error(`fetch failed after retries: ${url}`);
}

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [market, setMarket] = useState<MarketKey>('FUTURE_LEADERS');
  const [period, setPeriod] = useState<PeriodKey>('6mo');
  const [sheetConfig, setSheetConfig] = useState<SheetConfig>({ sheetId: '', sheetName: '' });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [fearGreed, setFearGreed] = useState<FearGreedData | null>(null);
  const [fearGreedLoading, setFearGreedLoading] = useState(false);
  const [selectedResult, setSelectedResult] = useState<AnalysisResult | null>(null);
  const [statusMsg, setStatusMsg] = useState('');
  const [sheetError, setSheetError] = useState('');
  const abortRef = useRef(false);

  const fetchFearGreed = useCallback(async (p: PeriodKey) => {
    setFearGreedLoading(true);
    try {
      const days = PERIOD_DAYS[p];
      const res = await fetch(`/api/fear-greed?days=${days}`);
      if (res.ok) setFearGreed(await res.json());
    } catch (e) {
      console.error('[fearGreed]', e);
    } finally {
      setFearGreedLoading(false);
    }
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (isAnalyzing) return;
    abortRef.current = false;
    setIsAnalyzing(true);
    setProgress(0);
    setResults([]);
    setSelectedResult(null);
    setSheetError('');
    setStatusMsg('종목 목록 가져오는 중...');

    fetchFearGreed(period);

    try {
      let symbols: string[] = [];
      let sheetNames: Record<string, string> = {};

      if (market === 'GOOGLE_SHEETS') {
        const params = new URLSearchParams();
        if (sheetConfig.sheetId.trim()) params.set('sheetId', sheetConfig.sheetId.trim());
        if (sheetConfig.sheetName.trim()) params.set('sheetName', sheetConfig.sheetName.trim());

        const sheetRes = await fetch(`/api/sheets?${params}`);
        const sheetData = await sheetRes.json();

        if (!sheetRes.ok || sheetData.error) {
          const msg = sheetData.error ?? '스프레드시트 조회 실패';
          setSheetError(msg);
          setStatusMsg(`오류: ${msg}`);
          return;
        }

        symbols = sheetData.symbols ?? [];
        sheetNames = sheetData.names ?? {};

        if (symbols.length === 0) {
          setSheetError('스프레드시트에서 종목을 찾을 수 없습니다. 티커 컬럼을 확인하세요.');
          setStatusMsg('오류: 종목 없음');
          return;
        }

        setStatusMsg(`📊 Google Sheets에서 ${symbols.length}개 종목 로드됨`);
      } else {
        const symRes = await fetch(`/api/symbols?market=${market}`);
        if (!symRes.ok) throw new Error('종목 목록 조회 실패');
        const data: { symbols: string[] } = await symRes.json();
        symbols = data.symbols;
        if (!symbols.length) throw new Error('종목 목록이 비어있습니다');
      }

      setStatusMsg(`총 ${symbols.length}개 종목 분석 시작...`);

      const accumulated: AnalysisResult[] = [];
      let done = 0;

      for (let i = 0; i < symbols.length; i += CONCURRENCY) {
        if (abortRef.current) break;
        const batch = symbols.slice(i, i + CONCURRENCY);

        const batchResults = await Promise.allSettled(
          batch.map(async (sym) => {
            try {
              const res = await fetchWithRetry(
                `/api/stock-data?symbol=${encodeURIComponent(sym)}&period=${period}`,
              );
              if (!res.ok) return null;
              const data: { symbol: string; companyName: string; bars: OHLCVBar[] } =
                await res.json();
              if (!data.bars || data.bars.length < 20) return null;
              const companyName = sheetNames[sym] || data.companyName;
              return analyzeStock(sym, data.bars, period, companyName);
            } catch {
              return null;
            }
          }),
        );

        batchResults.forEach((r) => {
          if (r.status === 'fulfilled' && r.value) accumulated.push(r.value);
        });

        done += batch.length;
        setProgress(Math.min(99, (done / symbols.length) * 100));
        setStatusMsg(`분석 중... ${done}/${symbols.length} (성공: ${accumulated.length}개)`);
        setResults([...accumulated].sort((a, b) => b.score - a.score));
      }

      setProgress(100);
      setStatusMsg(
        market === 'GOOGLE_SHEETS'
          ? `📊 완료! ${accumulated.length}개 종목`
          : `완료! 총 ${accumulated.length}개 종목`,
      );
    } catch (err) {
      console.error('[analyze]', err);
      setStatusMsg(`오류: ${String(err)}`);
    } finally {
      setIsAnalyzing(false);
    }
  }, [isAnalyzing, market, period, sheetConfig, fetchFearGreed]);

  return (
    // min-h-screen: 높이 제한 없이 콘텐츠 길이만큼 늘어남 (스크롤 허용)
    <div className="flex min-h-screen bg-slate-50">

      {/* ── Sidebar: sticky로 스크롤해도 좌측에 고정 */}
      <div
        className={`shrink-0 overflow-hidden transition-all duration-300 ease-in-out sticky top-0 h-screen ${
          sidebarOpen ? 'w-72' : 'w-0'
        }`}
      >
        <Sidebar
          market={market}
          period={period}
          sheetConfig={sheetConfig}
          isAnalyzing={isAnalyzing}
          onMarketChange={(m) => { setMarket(m); setSheetError(''); }}
          onPeriodChange={setPeriod}
          onSheetConfigChange={setSheetConfig}
          onAnalyze={handleAnalyze}
        />
      </div>

      {/* ── Main: 스크롤 허용 */}
      <main className="flex-1 min-w-0 flex flex-col">

        {/* 헤더 */}
        <header className="flex items-center gap-3 px-4 pt-3 pb-2 sticky top-0 bg-slate-50 z-10 border-b border-slate-100">
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="shrink-0 p-1.5 rounded-lg text-gray-500 hover:text-gray-800 hover:bg-gray-200 transition-colors"
            title={sidebarOpen ? '사이드바 닫기' : '사이드바 열기'}
          >
            <Menu size={20} />
          </button>

          <div className="flex-1 min-w-0">
            <h1 className="text-base font-bold text-gray-900 leading-tight truncate">
              📈 주식 기술적 분석 종목 추천
            </h1>
            <p className="text-xs text-gray-400">
              MA · 골든크로스 · 추세 분석 | Google Sheets 연동
            </p>
          </div>

          {statusMsg && (
            <span className={`shrink-0 text-xs border rounded-lg px-2.5 py-1 ${
              sheetError
                ? 'text-red-600 bg-red-50 border-red-200'
                : 'text-gray-500 bg-white border-gray-200'
            }`}>
              {statusMsg}
            </span>
          )}
        </header>

        {/* 오류 배너 */}
        {sheetError && (
          <div className="mx-4 mt-2 bg-red-50 border border-red-200 rounded-xl px-4 py-2 text-sm text-red-700">
            <strong>스프레드시트 오류:</strong> {sheetError}
          </div>
        )}

        {/* Fear & Greed */}
        <div className="px-4 pt-2 pb-1">
          <FearGreedWidget data={fearGreed} loading={fearGreedLoading} />
        </div>

        {/* ── 콘텐츠 영역: 종목 선택 여부에 따라 레이아웃 전환 */}
        <div className="flex-1 px-4 pb-4 pt-2">
          {selectedResult ? (
            // 종목 선택 시: 좌(테이블) + 우(차트) 분할
            // 모바일에서는 위아래로 쌓임 (스크롤)
            <div className="flex flex-col xl:flex-row gap-3">

              {/* 테이블 – 고정 높이로 스크롤 가능 */}
              <div className="xl:w-[480px] shrink-0" style={{ height: '420px' }}>
                <ResultsTable
                  results={results}
                  selectedSymbol={selectedResult?.symbol ?? null}
                  onSelect={setSelectedResult}
                  progress={progress}
                  isAnalyzing={isAnalyzing}
                />
              </div>

              {/* 차트 – 고정 픽셀 높이로 항상 렌더링 보장 */}
              <div className="flex-1" style={{ height: '520px', minWidth: 0 }}>
                <StockDetail
                  result={selectedResult}
                  onClose={() => setSelectedResult(null)}
                />
              </div>

            </div>
          ) : (
            // 종목 미선택 시: 테이블 전체 너비
            <div style={{ minHeight: '400px' }}>
              <ResultsTable
                results={results}
                selectedSymbol={null}
                onSelect={setSelectedResult}
                progress={progress}
                isAnalyzing={isAnalyzing}
              />
            </div>
          )}
        </div>

      </main>
    </div>
  );
}
