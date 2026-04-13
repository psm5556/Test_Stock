'use client';

import { BarChart2, Clock, Play, Info } from 'lucide-react';
import type { MarketKey, PeriodKey } from '@/types';
import { MARKET_LABELS, PERIOD_LABELS } from '@/types';

const MARKET_OPTIONS: MarketKey[] = [
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
  isAnalyzing: boolean;
  onMarketChange: (m: MarketKey) => void;
  onPeriodChange: (p: PeriodKey) => void;
  onAnalyze: () => void;
}

export default function Sidebar({
  market,
  period,
  isAnalyzing,
  onMarketChange,
  onPeriodChange,
  onAnalyze,
}: SidebarProps) {
  const warning = MARKET_WARNINGS[market];

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

      <div className="flex-1 p-4 space-y-6">
        {/* Market Selector */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
            시장 / 섹터
          </label>
          <div className="space-y-1 max-h-72 overflow-y-auto pr-1">
            {MARKET_OPTIONS.map((m) => (
              <button
                key={m}
                onClick={() => onMarketChange(m)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  market === m
                    ? 'bg-blue-600 text-white font-semibold shadow-sm'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {MARKET_LABELS[m]}
              </button>
            ))}
          </div>
        </div>

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
                className={`py-2 rounded-lg text-sm font-medium transition-colors ${
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
        {warning && (
          <div className="flex gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700">
            <Info size={14} className="shrink-0 mt-0.5" />
            <span>{warning}</span>
          </div>
        )}

        {/* Analyze Button */}
        <button
          onClick={onAnalyze}
          disabled={isAnalyzing}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 rounded-xl text-sm transition-colors shadow-sm"
        >
          <Play size={16} />
          {isAnalyzing ? '분석 중...' : '분석 시작'}
        </button>
      </div>

      {/* Footer Guide */}
      <div className="p-4 border-t border-gray-100 text-xs text-gray-500 space-y-1">
        <p className="font-semibold text-gray-600 mb-2">점수 기준 (0~100점)</p>
        <p>🌟 골든크로스 발생: +25점</p>
        <p>📈 현재가 이평선 위: +25점</p>
        <p>🛡️ 125일선 지지: +25점</p>
        <p>📊 추세 안정: +25점</p>
        <p className="mt-2 text-gray-400">⚠️ 투자 결정은 본인 판단과 책임 하에 하시기 바랍니다.</p>
      </div>
    </aside>
  );
}
