'use client';

import { useEffect, useState } from 'react';
import { BarChart2, Clock, Play, Info, Table2, ExternalLink, CheckCircle2 } from 'lucide-react';
import type { MarketKey, PeriodKey, SheetConfig } from '@/types';
import { MARKET_LABELS, PERIOD_LABELS } from '@/types';

const MARKET_OPTIONS: MarketKey[] = [
  'GOOGLE_SHEETS',
  'FUTURE_LEADERS',
  'MEGA_CAP_LEADERS',
  'SP500',
  'NASDAQ',
  'ALL',
  'KOSPI',
  'KOSDAQ',
  'AEROSPACE',
  'QUANTUM',
  'LONGEVITY',
  'SYNTHETIC_BIO',
  'STABLECOIN',
  'DATACENTER_SEMI',
  'BCI',
  'DATA_CENTER_ENERGY',
  'DATA_CENTER_INFRASTRUCTURE',
  'CYBERSECURITY',
  'SATELLITE_COMMUNICATIONS',
  'SUBSEA_CABLES',
  'OCEAN_PLASTICS',
];

const PERIOD_OPTIONS: PeriodKey[] = ['1mo', '3mo', '6mo', '1y', '2y', '5y'];

const MARKET_WARNINGS: Partial<Record<MarketKey, string>> = {
  SP500: 'S&P 500 전체 분석은 5분 이상 소요될 수 있습니다.',
  NASDAQ: 'NASDAQ 전체 분석은 5분 이상 소요될 수 있습니다.',
  ALL: '전체 시장 분석은 10분 이상 소요될 수 있습니다.',
};

interface SidebarProps {
  market: MarketKey;
  period: PeriodKey;
  sheetConfig: SheetConfig;
  isAnalyzing: boolean;
  onMarketChange: (m: MarketKey) => void;
  onPeriodChange: (p: PeriodKey) => void;
  onSheetConfigChange: (cfg: SheetConfig) => void;
  onAnalyze: () => void;
}

function extractSheetId(input: string): string {
  const match = input.match(/\/spreadsheets\/d\/([a-zA-Z0-9_-]+)/);
  return match ? match[1] : input.trim();
}

export default function Sidebar({
  market,
  period,
  sheetConfig,
  isAnalyzing,
  onMarketChange,
  onPeriodChange,
  onSheetConfigChange,
  onAnalyze,
}: SidebarProps) {
  const isSheets = market === 'GOOGLE_SHEETS';
  const warning = MARKET_WARNINGS[market];

  // 서버 환경변수 설정 여부 확인
  const [envSheetId, setEnvSheetId] = useState(false);
  const [envSheetName, setEnvSheetName] = useState('');

  useEffect(() => {
    fetch('/api/config')
      .then((r) => r.json())
      .then((d) => {
        setEnvSheetId(d.hasGoogleSheetId ?? false);
        setEnvSheetName(d.googleSheetName ?? '');
      })
      .catch(() => {});
  }, []);

  // 분석 가능 조건: Google Sheets 선택 시 (환경변수 있거나 직접 입력)
  const sheetReady = sheetConfig.sheetId.trim().length > 0 || envSheetId;
  const canAnalyze = !isAnalyzing && (!isSheets || sheetReady);

  // 환경변수 설정된 경우 시트 이름 기본값 자동 적용
  useEffect(() => {
    if (isSheets && envSheetId && !sheetConfig.sheetId && !sheetConfig.sheetName && envSheetName) {
      onSheetConfigChange({ sheetId: '', sheetName: envSheetName });
    }
  }, [isSheets, envSheetId, envSheetName, sheetConfig, onSheetConfigChange]);

  return (
    <aside className="w-72 shrink-0 bg-white border-r border-gray-200 flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="p-5 border-b border-gray-100">
        <div className="flex items-center gap-2 mb-1">
          <BarChart2 className="text-blue-600" size={22} />
          <h2 className="font-bold text-gray-800 text-lg leading-tight">분석 설정</h2>
        </div>
        <p className="text-xs text-gray-500">시장·섹터와 기간을 선택하세요</p>
      </div>

      <div className="flex-1 p-4 space-y-5">
        {/* Market Selector */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
            시장 / 섹터
          </label>
          <div className="space-y-0.5 max-h-64 overflow-y-auto pr-1">
            {MARKET_OPTIONS.map((m) => (
              <button
                key={m}
                onClick={() => onMarketChange(m)}
                className={`w-full text-left px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  market === m
                    ? m === 'GOOGLE_SHEETS'
                      ? 'bg-emerald-600 text-white font-semibold shadow-sm'
                      : 'bg-blue-600 text-white font-semibold shadow-sm'
                    : m === 'GOOGLE_SHEETS'
                      ? 'text-emerald-700 hover:bg-emerald-50 font-medium'
                      : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {MARKET_LABELS[m]}
              </button>
            ))}
          </div>
        </div>

        {/* Google Sheets Config */}
        {isSheets && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 space-y-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
              <Table2 size={13} />
              Google Sheets 연동
            </div>

            {/* 환경변수 설정된 경우 배지 표시 */}
            {envSheetId && (
              <div className="flex items-center gap-1.5 bg-emerald-100 border border-emerald-300 rounded-lg px-2.5 py-1.5">
                <CheckCircle2 size={13} className="text-emerald-600 shrink-0" />
                <span className="text-xs text-emerald-700 font-medium">
                  서버 환경변수에 Sheet ID 설정됨
                  {envSheetName && ` (시트: ${envSheetName})`}
                </span>
              </div>
            )}

            {/* Sheet ID 입력 – 환경변수 있어도 직접 입력으로 덮어쓸 수 있음 */}
            <div>
              <label className="block text-xs text-emerald-700 mb-1 font-medium">
                스프레드시트 ID 또는 URL
                {envSheetId && (
                  <span className="ml-1 text-emerald-500 font-normal">(비워두면 환경변수 사용)</span>
                )}
              </label>
              <input
                type="text"
                value={sheetConfig.sheetId}
                onChange={(e) =>
                  onSheetConfigChange({
                    ...sheetConfig,
                    sheetId: extractSheetId(e.target.value),
                  })
                }
                placeholder={envSheetId ? '환경변수에서 자동 로드됩니다' : '스프레드시트 ID 또는 URL 붙여넣기'}
                className="w-full text-xs px-2.5 py-1.5 border border-emerald-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-emerald-400 placeholder-gray-400"
              />
              {!envSheetId && (
                <p className="text-[10px] text-emerald-600 mt-1">
                  URL 전체를 붙여넣으면 ID를 자동 추출합니다
                </p>
              )}
            </div>

            {/* Sheet 탭 이름 */}
            <div>
              <label className="block text-xs text-emerald-700 mb-1 font-medium">
                시트 탭 이름 <span className="text-emerald-500 font-normal">(선택)</span>
              </label>
              <input
                type="text"
                value={sheetConfig.sheetName}
                onChange={(e) =>
                  onSheetConfigChange({ ...sheetConfig, sheetName: e.target.value })
                }
                placeholder={envSheetName || 'Sheet1'}
                className="w-full text-xs px-2.5 py-1.5 border border-emerald-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-emerald-400 placeholder-gray-400"
              />
            </div>

            {/* 시트 형식 안내 */}
            <div className="text-[10px] text-emerald-700 space-y-0.5 border-t border-emerald-200 pt-2">
              <p className="font-semibold">시트 필수 컬럼</p>
              <p>• <strong>티커</strong>: 종목 심볼 (AAPL, 005930.KS 등)</p>
              <p>• <strong>기업명</strong>: 회사명 (선택)</p>
              <p className="mt-1">공유 설정: <strong>링크 있는 모든 사용자 – 뷰어</strong></p>
              <a
                href="https://docs.google.com/spreadsheets"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-emerald-600 hover:underline mt-1"
              >
                Google Sheets 열기 <ExternalLink size={9} />
              </a>
            </div>
          </div>
        )}

        {/* Period Selector */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2 flex items-center gap-1">
            <Clock size={12} /> 조회 기간
          </label>
          <div className="grid grid-cols-3 gap-1">
            {PERIOD_OPTIONS.map((p) => (
              <button
                key={p}
                onClick={() => onPeriodChange(p)}
                className={`py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  period === p
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {PERIOD_LABELS[p]}
              </button>
            ))}
          </div>
        </div>

        {/* Warning */}
        {warning && !isSheets && (
          <div className="flex gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700">
            <Info size={13} className="shrink-0 mt-0.5" />
            <span>{warning}</span>
          </div>
        )}

        {/* Analyze Button */}
        <button
          onClick={onAnalyze}
          disabled={!canAnalyze}
          title={isSheets && !sheetReady ? '스프레드시트 ID를 입력하세요' : ''}
          className={`w-full flex items-center justify-center gap-2 font-semibold py-3 rounded-xl text-sm transition-colors shadow-sm text-white ${
            isSheets
              ? 'bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300'
              : 'bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400'
          }`}
        >
          <Play size={15} />
          {isAnalyzing ? '분석 중...' : '분석 시작'}
        </button>
      </div>

      {/* Footer Guide */}
      <div className="p-4 border-t border-gray-100 text-xs text-gray-500 space-y-0.5">
        <p className="font-semibold text-gray-600 mb-1.5">점수 기준 (0~100점)</p>
        <p>🌟 골든크로스 발생: +25점</p>
        <p>📈 현재가 이평선 위: +25점</p>
        <p>🛡️ 125일선 지지: +25점</p>
        <p>📊 추세 안정: +25점</p>
        <p className="mt-2 text-gray-400">⚠️ 투자 결정은 본인 판단과 책임 하에 하시기 바랍니다.</p>
      </div>
    </aside>
  );
}
