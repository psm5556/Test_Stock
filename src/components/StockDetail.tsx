'use client';

import dynamic from 'next/dynamic';
import type { AnalysisResult } from '@/types';
import { X, Star, TrendingUp, Shield, BarChart2 } from 'lucide-react';

const StockChart = dynamic(() => import('./StockChart'), { ssr: false });

interface StockDetailProps {
  result: AnalysisResult;
  onClose: () => void;
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 75 ? 'bg-red-100 text-red-700 border-red-300' :
    score >= 50 ? 'bg-orange-100 text-orange-700 border-orange-300' :
    score >= 25 ? 'bg-yellow-100 text-yellow-700 border-yellow-300' :
    'bg-gray-100 text-gray-500 border-gray-200';
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-base font-bold border ${color}`}>
      {score}점
    </span>
  );
}

function MetricCard({
  label, value, icon, detail,
}: {
  label: string; value: boolean; icon: React.ReactNode; detail?: string;
}) {
  return (
    <div className={`rounded-xl p-2.5 border flex items-start gap-2 ${
      value ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
    }`}>
      <div className={`mt-0.5 shrink-0 ${value ? 'text-green-600' : 'text-gray-400'}`}>{icon}</div>
      <div>
        <div className="text-xs font-semibold text-gray-600">{label}</div>
        <div className={`text-xs font-bold ${value ? 'text-green-700' : 'text-gray-500'}`}>
          {value ? '✅ 충족' : '❌ 미충족'}
        </div>
        {detail && <div className="text-[10px] text-gray-400 mt-0.5 leading-tight">{detail}</div>}
      </div>
    </div>
  );
}

// MA 범례 – MA200·240·365 제외
const MA_LEGEND = [
  { label: 'MA20',  color: '#ef4444' },
  { label: 'MA60',  color: '#22c55e' },
  { label: 'MA125', color: '#3b82f6' },
];

export default function StockDetail({ result, onClose }: StockDetailProps) {
  const isKorea = result.symbol.includes('.KS');
  const currency = isKorea ? '₩' : '$';
  const priceStr = result.currentPrice < 10
    ? result.currentPrice.toFixed(3)
    : result.currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="bg-white rounded-2xl border border-gray-200 flex flex-col" style={{ height: '100%' }}>
      {/* ── 헤더 */}
      <div className="flex items-start justify-between px-5 py-3 border-b border-gray-100 shrink-0">
        <div className="flex items-center gap-3 flex-wrap">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-lg font-bold text-gray-900">{result.symbol}</h2>
              <ScoreBadge score={result.score} />
              <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{result.periodLabel}</span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">{result.companyName}</p>
          </div>
          <p className="text-xl font-bold text-gray-800 ml-2">
            {currency}{priceStr}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors shrink-0"
        >
          <X size={18} />
        </button>
      </div>

      {/* ── 분석 지표 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 px-4 py-2 border-b border-gray-100 shrink-0">
        <MetricCard label="골든크로스"   value={result.goldenCross}  icon={<Star size={14} />}       detail={result.crossDate ? `발생일: ${result.crossDate}` : undefined} />
        <MetricCard label="이평선 위"    value={result.aboveMALines} icon={<TrendingUp size={14} />}  detail="현재가 > MA20, MA60" />
        <MetricCard label="125일선 지지" value={result.ma125Support} icon={<Shield size={14} />}      detail={`최근 ${result.supportCount}개 캔들 지지`} />
        <MetricCard label="추세 안정"    value={result.trendStable}  icon={<BarChart2 size={14} />}   detail="MA20·MA60 상승 추세" />
      </div>

      {/* ── MA 범례 */}
      <div className="flex items-center gap-3 px-4 py-1.5 border-b border-gray-100 flex-wrap shrink-0">
        {MA_LEGEND.map((m) => (
          <span key={m.label} className="flex items-center gap-1 text-xs text-gray-600">
            <span className="inline-block w-5 h-0.5 rounded" style={{ backgroundColor: m.color }} />
            {m.label}
          </span>
        ))}
        {result.goldenCross && (
          <span className="flex items-center gap-1 text-xs text-amber-600 ml-2">
            🌟 골든크로스
          </span>
        )}
        {result.aboveMALines && (
          <span className="flex items-center gap-1 text-xs text-green-600">
            - - 현재가 ▲MA20·60
          </span>
        )}
      </div>

      {/* ── 캔들스틱 차트 (lightweight-charts) */}
      <div className="flex-1 min-h-0 p-2">
        <StockChart result={result} />
      </div>
    </div>
  );
}
