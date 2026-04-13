'use client';

import dynamic from 'next/dynamic';
import type { AnalysisResult } from '@/types';
import { X, Star, TrendingUp, Shield, BarChart2 } from 'lucide-react';

const TradingViewChart = dynamic(() => import('./TradingViewChart'), { ssr: false });

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
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-lg font-bold border ${color}`}>
      {score}점
    </span>
  );
}

function MetricCard({
  label,
  value,
  icon,
  detail,
}: {
  label: string;
  value: boolean;
  icon: React.ReactNode;
  detail?: string;
}) {
  return (
    <div className={`rounded-xl p-3 border flex items-start gap-3 ${
      value ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
    }`}>
      <div className={`mt-0.5 ${value ? 'text-green-600' : 'text-gray-400'}`}>{icon}</div>
      <div>
        <div className="text-xs font-semibold text-gray-600">{label}</div>
        <div className={`text-sm font-bold ${value ? 'text-green-700' : 'text-gray-500'}`}>
          {value ? '✅ 충족' : '❌ 미충족'}
        </div>
        {detail && <div className="text-xs text-gray-400 mt-0.5">{detail}</div>}
      </div>
    </div>
  );
}

export default function StockDetail({ result, onClose }: StockDetailProps) {
  const priceStr = result.currentPrice < 10
    ? result.currentPrice.toFixed(3)
    : result.currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const isKorea = result.symbol.includes('.KS');
  const currency = isKorea ? '₩' : '$';

  return (
    <div className="bg-white rounded-2xl border border-gray-200 flex flex-col">
      {/* Title bar */}
      <div className="flex items-start justify-between p-5 border-b border-gray-100">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-xl font-bold text-gray-900">{result.symbol}</h2>
            <ScoreBadge score={result.score} />
            <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
              {result.periodLabel}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-0.5">{result.companyName}</p>
          <p className="text-2xl font-bold text-gray-800 mt-1">
            {currency}{priceStr}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 border-b border-gray-100">
        <MetricCard
          label="골든크로스"
          value={result.goldenCross}
          icon={<Star size={16} />}
          detail={result.crossDate ? `발생일: ${result.crossDate}` : undefined}
        />
        <MetricCard
          label="이평선 위"
          value={result.aboveMALines}
          icon={<TrendingUp size={16} />}
          detail="현재가 > MA20, MA60"
        />
        <MetricCard
          label="125일선 지지"
          value={result.ma125Support}
          icon={<Shield size={16} />}
          detail={`최근 ${result.supportCount}개 캔들 지지`}
        />
        <MetricCard
          label="추세 안정"
          value={result.trendStable}
          icon={<BarChart2 size={16} />}
          detail="MA20, MA60 상승 추세"
        />
      </div>

      {/* TradingView Chart */}
      <div className="flex-1 p-0 overflow-hidden rounded-b-2xl" style={{ minHeight: '500px' }}>
        <TradingViewChart symbol={result.symbol} />
      </div>
    </div>
  );
}
