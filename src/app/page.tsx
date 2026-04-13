'use client';

import { useState, useCallback, useRef } from 'react';
import Sidebar from '@/components/Sidebar';
import FearGreedWidget from '@/components/FearGreedWidget';
import ResultsTable from '@/components/ResultsTable';
import StockDetail from '@/components/StockDetail';
import type {
  MarketKey,
  PeriodKey,
  AnalysisResult,
  FearGreedData,
} from '@/types';
import { PERIOD_DAYS } from '@/types';
import { analyzeStock } from '@/lib/analysis';

const CONCURRENCY = 8; // parallel stock fetches

/** Fetch with simple retry on network error */
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
  const [market, setMarket] = useState<MarketKey>('FUTURE_LEADERS');
  const [period, setPeriod] = useState<PeriodKey>('6mo');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [fearGreed, setFearGreed] = useState<FearGreedData | null>(null);
  const [fearGreedLoading, setFearGreedLoading] = useState(false);
  const [selectedResult, setSelectedResult] = useState<AnalysisResult | null>(null);
  const [statusMsg, setStatusMsg] = useState('');
  const abortRef = useRef(false);

  const fetchFearGreed = useCallback(async (p: PeriodKey) => {
    setFearGreedLoading(true);
    try {
      const days = PERIOD_DAYS[p];
      const res = await fetch(`/api/fear-greed?days=${days}`);
      if (res.ok) {
        const data: FearGreedData = await res.json();
        setFearGreed(data);
      }
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
    setStatusMsg('종목 목록 가져오는 중...');

    // Fetch fear & greed concurrently
    fetchFearGreed(period);

    try {
      // 1. Get symbol list
      const symRes = await fetch(`/api/symbols?market=${market}`);
      if (!symRes.ok) throw new Error('종목 목록 조회 실패');
      const { symbols }: { symbols: string[] } = await symRes.json();
      if (!symbols.length) throw new Error('종목 목록이 비어있습니다');

      setStatusMsg(`총 ${symbols.length}개 종목 분석 시작...`);

      // 2. Analyze in batches
      const accumulated: AnalysisResult[] = [];
      let done = 0;

      for (let i = 0; i < symbols.length; i += CONCURRENCY) {
        if (abortRef.current) break;
        const batch = symbols.slice(i, i + CONCURRENCY);

        const batchResults = await Promise.allSettled(
          batch.map(async (sym) => {
            try {
              const res = await fetchWithRetry(`/api/stock-data?symbol=${encodeURIComponent(sym)}&period=${period}`);
              if (!res.ok) return null;
              const data: { symbol: string; companyName: string; bars: import('@/types').OHLCVBar[] } =
                await res.json();
              if (!data.bars || data.bars.length < 20) return null;
              return analyzeStock(sym, data.bars, period, data.companyName);
            } catch {
              return null;
            }
          }),
        );

        batchResults.forEach((r) => {
          if (r.status === 'fulfilled' && r.value) accumulated.push(r.value);
        });

        done += batch.length;
        const pct = Math.min(99, (done / symbols.length) * 100);
        setProgress(pct);
        setStatusMsg(`분석 중... ${done}/${symbols.length}`);

        // Update results incrementally (sorted by score)
        const sorted = [...accumulated].sort((a, b) => b.score - a.score);
        setResults(sorted);
      }

      setProgress(100);
      setStatusMsg(`완료! 총 ${accumulated.length}개 종목 분석됨`);
    } catch (err) {
      console.error('[analyze]', err);
      setStatusMsg(`오류: ${String(err)}`);
    } finally {
      setIsAnalyzing(false);
    }
  }, [isAnalyzing, market, period, fetchFearGreed]);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <Sidebar
        market={market}
        period={period}
        isAnalyzing={isAnalyzing}
        onMarketChange={setMarket}
        onPeriodChange={setPeriod}
        onAnalyze={handleAnalyze}
      />

      {/* Main content */}
      <main className="flex-1 overflow-hidden flex flex-col gap-3 p-4">
        {/* Top bar */}
        <header className="flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-lg font-bold text-gray-900 leading-tight">
              📈 주식 기술적 분석 종목 추천
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              이동평균선 · 골든크로스 · 추세 분석 기반 | 미래 대장주 엄선 포함
            </p>
          </div>
          {statusMsg && (
            <span className="text-xs text-gray-500 bg-white border border-gray-200 rounded-lg px-3 py-1.5">
              {statusMsg}
            </span>
          )}
        </header>

        {/* Fear & Greed – 높이 1/2로 축소 */}
        <div className="shrink-0">
          <FearGreedWidget data={fearGreed} loading={fearGreedLoading} />
        </div>

        {/* Results + Detail split view */}
        {selectedResult ? (
          <div className="flex flex-col lg:flex-row gap-3 flex-1 min-h-0 overflow-hidden">
            {/* Left: compact table */}
            <div className="lg:w-80 lg:shrink-0 flex flex-col min-h-[200px] lg:min-h-0 overflow-hidden">
              <ResultsTable
                results={results}
                selectedSymbol={selectedResult.symbol}
                onSelect={setSelectedResult}
                progress={progress}
                isAnalyzing={isAnalyzing}
              />
            </div>
            {/* Right: stock detail – 차트 충분한 높이 확보 */}
            <div className="flex-1 min-h-0 overflow-hidden">
              <StockDetail
                result={selectedResult}
                onClose={() => setSelectedResult(null)}
              />
            </div>
          </div>
        ) : (
          <div className="flex-1 min-h-0 overflow-hidden">
            <ResultsTable
              results={results}
              selectedSymbol={null}
              onSelect={setSelectedResult}
              progress={progress}
              isAnalyzing={isAnalyzing}
            />
          </div>
        )}

        {/* Footer */}
        <footer className="text-center text-xs text-gray-400 pb-2">
          📈 주식 기술적 분석 종목 추천 시스템 · 미래 대장주 엄선 포함 ·{' '}
          <span className="text-gray-500">⚠️ 투자 결정은 본인의 판단과 책임 하에 하시기 바랍니다.</span>
        </footer>
      </main>
    </div>
  );
}
