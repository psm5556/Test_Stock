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
      // ── 1. 종목 목록 + 회사명 가져오기
      let symbols: string[] = [];
      let sheetNames: Record<string, string> = {};

      if (market === 'GOOGLE_SHEETS') {
        // Google Sheets에서 종목 가져오기
        // sheetId가 비어있으면 파라미터 자체를 생략 → 서버가 환경변수 사용
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
        // 기존 시장별 종목
        const symRes = await fetch(`/api/symbols?market=${market}`);
        if (!symRes.ok) throw new Error('종목 목록 조회 실패');
        const data: { symbols: string[] } = await symRes.json();
        symbols = data.symbols;
        if (!symbols.length) throw new Error('종목 목록이 비어있습니다');
      }

      setStatusMsg(`총 ${symbols.length}개 종목 분석 시작...`);

      // ── 2. 병렬 배치 분석
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

              // Google Sheets의 기업명 우선, 없으면 Yahoo Finance 기업명
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
          ? `📊 Google Sheets 분석 완료! ${accumulated.length}개 종목`
          : `완료! 총 ${accumulated.length}개 종목 분석됨`,
      );
    } catch (err) {
      console.error('[analyze]', err);
      setStatusMsg(`오류: ${String(err)}`);
    } finally {
      setIsAnalyzing(false);
    }
  }, [isAnalyzing, market, period, sheetConfig, fetchFearGreed]);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
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

      {/* Main content */}
      <main className="flex-1 overflow-hidden flex flex-col gap-3 p-4">
        {/* Top bar */}
        <header className="flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-lg font-bold text-gray-900 leading-tight">
              📈 주식 기술적 분석 종목 추천
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              이동평균선 · 골든크로스 · 추세 분석 기반 | Google Sheets 연동 포함
            </p>
          </div>
          {statusMsg && (
            <span className={`text-xs border rounded-lg px-3 py-1.5 ${
              sheetError
                ? 'text-red-600 bg-red-50 border-red-200'
                : 'text-gray-500 bg-white border-gray-200'
            }`}>
              {statusMsg}
            </span>
          )}
        </header>

        {/* Google Sheets 오류 배너 */}
        {sheetError && (
          <div className="shrink-0 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
            <strong>스프레드시트 오류:</strong> {sheetError}
          </div>
        )}

        {/* Fear & Greed */}
        <div className="shrink-0">
          <FearGreedWidget data={fearGreed} loading={fearGreedLoading} />
        </div>

        {/* Results + Detail split view */}
        {selectedResult ? (
          <div className="flex flex-col lg:flex-row gap-3 flex-1 min-h-0 overflow-hidden">
            <div className="lg:w-80 lg:shrink-0 flex flex-col min-h-[200px] lg:min-h-0 overflow-hidden">
              <ResultsTable
                results={results}
                selectedSymbol={selectedResult.symbol}
                onSelect={setSelectedResult}
                progress={progress}
                isAnalyzing={isAnalyzing}
              />
            </div>
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

        <footer className="text-center text-xs text-gray-400 pb-1 shrink-0">
          📈 주식 기술적 분석 종목 추천 시스템 ·{' '}
          <span className="text-gray-500">⚠️ 투자 결정은 본인의 판단과 책임 하에 하시기 바랍니다.</span>
        </footer>
      </main>
    </div>
  );
}
