'use client';

import { useState, useMemo } from 'react';
import { TrendingUp, Filter, ChevronUp, ChevronDown } from 'lucide-react';
import type { AnalysisResult } from '@/types';

type FilterKey = 'all' | 'high' | 'medium' | 'golden' | 'trend';
type SortKey = 'score' | 'symbol' | 'price';

interface ResultsTableProps {
  results: AnalysisResult[];
  selectedSymbol: string | null;
  onSelect: (result: AnalysisResult) => void;
  progress?: number; // 0-100
  isAnalyzing: boolean;
}

const FILTER_OPTIONS: { key: FilterKey; label: string }[] = [
  { key: 'all', label: '전체' },
  { key: 'high', label: '🔥 고득점 75+' },
  { key: 'medium', label: '👍 50점 이상' },
  { key: 'golden', label: '🌟 골든크로스' },
  { key: 'trend', label: '📈 추세 안정' },
];

export default function ResultsTable({
  results,
  selectedSymbol,
  onSelect,
  progress = 0,
  isAnalyzing,
}: ResultsTableProps) {
  const [filter, setFilter] = useState<FilterKey>('all');
  const [sort, setSort] = useState<SortKey>('score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const filtered = useMemo(() => {
    let arr = [...results];
    if (filter === 'high') arr = arr.filter((r) => r.score >= 75);
    else if (filter === 'medium') arr = arr.filter((r) => r.score >= 50);
    else if (filter === 'golden') arr = arr.filter((r) => r.goldenCross);
    else if (filter === 'trend') arr = arr.filter((r) => r.trendStable);

    arr.sort((a, b) => {
      let av = 0, bv = 0;
      if (sort === 'score') { av = a.score; bv = b.score; }
      else if (sort === 'symbol') { av = 0; bv = 0; return sortDir === 'asc' ? a.symbol.localeCompare(b.symbol) : b.symbol.localeCompare(a.symbol); }
      else if (sort === 'price') { av = a.currentPrice; bv = b.currentPrice; }
      return sortDir === 'asc' ? av - bv : bv - av;
    });

    return arr;
  }, [results, filter, sort, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sort === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSort(key); setSortDir('desc'); }
  };

  const SortIcon = ({ k }: { k: SortKey }) =>
    sort === k ? (sortDir === 'desc' ? <ChevronDown size={12} /> : <ChevronUp size={12} />) : null;

  const stats = {
    total: results.length,
    high: results.filter((r) => r.score >= 75).length,
    medium: results.filter((r) => r.score >= 50 && r.score < 75).length,
    golden: results.filter((r) => r.goldenCross).length,
  };

  if (results.length === 0 && !isAnalyzing) {
    return (
      <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center">
        <TrendingUp size={40} className="mx-auto text-gray-300 mb-3" />
        <p className="text-gray-500 text-sm">분석 결과가 여기에 표시됩니다.</p>
        <p className="text-gray-400 text-xs mt-1">왼쪽에서 설정 후 &quot;분석 시작&quot;을 클릭하세요.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <TrendingUp size={16} className="text-blue-600" />
            분석 결과
          </h3>
          {results.length > 0 && (
            <div className="flex gap-3 text-xs text-gray-500">
              <span>총 <strong className="text-gray-700">{stats.total}</strong></span>
              <span>🔥 <strong className="text-red-600">{stats.high}</strong></span>
              <span>👍 <strong className="text-orange-500">{stats.medium}</strong></span>
              <span>🌟 <strong className="text-yellow-600">{stats.golden}</strong></span>
            </div>
          )}
        </div>

        {/* Progress bar */}
        {isAnalyzing && (
          <div className="mb-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>분석 진행 중...</span>
              <span>{progress.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-1 flex-wrap">
          {FILTER_OPTIONS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                filter === f.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.label}
            </button>
          ))}
          <span className="ml-auto text-xs text-gray-400 self-center">
            <Filter size={10} className="inline mr-1" />{filtered.length}개
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-auto flex-1">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <th
                className="text-left py-2.5 px-3 cursor-pointer hover:text-gray-700 whitespace-nowrap"
                onClick={() => toggleSort('symbol')}
              >
                종목 <SortIcon k="symbol" />
              </th>
              <th className="text-right py-2.5 px-3 cursor-pointer hover:text-gray-700" onClick={() => toggleSort('price')}>
                가격 <SortIcon k="price" />
              </th>
              <th className="text-center py-2.5 px-1">GC</th>
              <th className="text-center py-2.5 px-1">MA</th>
              <th className="text-center py-2.5 px-1">125</th>
              <th className="text-center py-2.5 px-1">추세</th>
              <th
                className="text-right py-2.5 px-3 cursor-pointer hover:text-gray-700"
                onClick={() => toggleSort('score')}
              >
                점수 <SortIcon k="score" />
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.map((r) => {
              const isSelected = r.symbol === selectedSymbol;
              const scoreColor =
                r.score >= 75 ? 'text-red-600 font-bold' :
                r.score >= 50 ? 'text-orange-500 font-semibold' :
                r.score >= 25 ? 'text-gray-700' : 'text-gray-400';

              return (
                <tr
                  key={r.symbol}
                  onClick={() => onSelect(r)}
                  className={`cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-blue-50 border-l-2 border-blue-500'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <td className="py-2.5 px-3">
                    <div className="font-semibold text-gray-800">{r.symbol}</div>
                    <div className="text-xs text-gray-400 truncate max-w-[120px]">{r.companyName}</div>
                  </td>
                  <td className="py-2.5 px-3 text-right text-gray-700 tabular-nums">
                    {r.currentPrice < 10
                      ? r.currentPrice.toFixed(3)
                      : r.currentPrice.toFixed(2)}
                  </td>
                  <td className="py-2.5 px-1 text-center">{r.goldenCross ? '✅' : '❌'}</td>
                  <td className="py-2.5 px-1 text-center">{r.aboveMALines ? '✅' : '❌'}</td>
                  <td className="py-2.5 px-1 text-center">{r.ma125Support ? '✅' : '❌'}</td>
                  <td className="py-2.5 px-1 text-center">{r.trendStable ? '✅' : '❌'}</td>
                  <td className={`py-2.5 px-3 text-right tabular-nums ${scoreColor}`}>{r.score}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filtered.length === 0 && results.length > 0 && (
          <div className="text-center py-8 text-sm text-gray-400">
            현재 필터 조건에 해당하는 종목이 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}
