'use client';

import { useState, useMemo } from 'react';
import { TrendingUp, Filter, ChevronUp, ChevronDown } from 'lucide-react';
import type { AnalysisResult } from '@/types';

type FilterKey = 'all' | 'high' | 'medium' | 'golden' | 'trend';
type SortKey = 'score' | 'symbol' | 'price' | 'goldenCross' | 'aboveMALines' | 'ma125Support' | 'trendStable';

interface ResultsTableProps {
  results: AnalysisResult[];
  selectedSymbol: string | null;
  onSelect: (result: AnalysisResult) => void;
  progress?: number;
  isAnalyzing: boolean;
}

const FILTER_OPTIONS: { key: FilterKey; label: string }[] = [
  { key: 'all', label: '전체' },
  { key: 'high', label: '🔥 75+' },
  { key: 'medium', label: '👍 50+' },
  { key: 'golden', label: '🌟 골든크로스' },
  { key: 'trend', label: '📈 추세 안정' },
];

interface ColDef {
  key: SortKey;
  label: string;
  title: string;
  align: 'left' | 'right' | 'center';
}

const COLUMNS: ColDef[] = [
  { key: 'symbol',       label: '종목',  title: '종목명',           align: 'left'   },
  { key: 'price',        label: '가격',  title: '현재가',           align: 'right'  },
  { key: 'goldenCross',  label: 'GC',    title: '골든크로스',       align: 'center' },
  { key: 'aboveMALines', label: 'MA',    title: '이평선 위',        align: 'center' },
  { key: 'ma125Support', label: '125',   title: '125일선 지지',     align: 'center' },
  { key: 'trendStable',  label: '추세',  title: '추세 안정',        align: 'center' },
  { key: 'score',        label: '점수',  title: '종합 점수',        align: 'right'  },
];

function boolVal(v: boolean) { return v ? 1 : 0; }

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
    if (filter === 'high')   arr = arr.filter((r) => r.score >= 75);
    if (filter === 'medium') arr = arr.filter((r) => r.score >= 50);
    if (filter === 'golden') arr = arr.filter((r) => r.goldenCross);
    if (filter === 'trend')  arr = arr.filter((r) => r.trendStable);

    arr.sort((a, b) => {
      let diff = 0;
      switch (sort) {
        case 'symbol':       diff = a.symbol.localeCompare(b.symbol); break;
        case 'price':        diff = a.currentPrice - b.currentPrice; break;
        case 'goldenCross':  diff = boolVal(a.goldenCross)  - boolVal(b.goldenCross);  break;
        case 'aboveMALines': diff = boolVal(a.aboveMALines) - boolVal(b.aboveMALines); break;
        case 'ma125Support': diff = boolVal(a.ma125Support) - boolVal(b.ma125Support); break;
        case 'trendStable':  diff = boolVal(a.trendStable)  - boolVal(b.trendStable);  break;
        case 'score':
        default:             diff = a.score - b.score; break;
      }
      return sortDir === 'asc' ? diff : -diff;
    });

    return arr;
  }, [results, filter, sort, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sort === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSort(key); setSortDir('desc'); }
  };

  const SortIcon = ({ k }: { k: SortKey }) =>
    sort === k
      ? sortDir === 'desc'
        ? <ChevronDown size={11} className="inline ml-0.5" />
        : <ChevronUp   size={11} className="inline ml-0.5" />
      : <span className="inline-block w-3" />;

  const stats = {
    total:  results.length,
    high:   results.filter((r) => r.score >= 75).length,
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
    <div className="bg-white rounded-2xl border border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-100 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2 text-sm">
            <TrendingUp size={15} className="text-blue-600" /> 분석 결과
          </h3>
          {results.length > 0 && (
            <div className="flex gap-2 text-xs text-gray-500">
              <span>총 <strong className="text-gray-700">{stats.total}</strong></span>
              <span>🔥 <strong className="text-red-600">{stats.high}</strong></span>
              <span>👍 <strong className="text-orange-500">{stats.medium}</strong></span>
              <span>🌟 <strong className="text-yellow-600">{stats.golden}</strong></span>
            </div>
          )}
        </div>

        {/* Progress bar */}
        {isAnalyzing && (
          <div className="mb-2">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>분석 진행 중...</span>
              <span>{progress.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-1.5">
              <div
                className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-1 flex-wrap items-center">
          {FILTER_OPTIONS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-2 py-0.5 rounded-lg text-xs font-medium transition-colors ${
                filter === f.key ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.label}
            </button>
          ))}
          <span className="ml-auto text-xs text-gray-400 flex items-center gap-1">
            <Filter size={10} />{filtered.length}개
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-auto flex-1">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-gray-50 text-xs text-gray-500 border-b border-gray-100">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  title={col.title}
                  onClick={() => toggleSort(col.key)}
                  className={`py-2 px-2 cursor-pointer hover:text-gray-800 hover:bg-gray-100 select-none whitespace-nowrap uppercase tracking-wide ${
                    col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
                  } ${sort === col.key ? 'text-blue-600 bg-blue-50' : ''}`}
                >
                  {col.label}<SortIcon k={col.key} />
                </th>
              ))}
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
                    isSelected ? 'bg-blue-50 border-l-2 border-blue-500' : 'hover:bg-gray-50'
                  }`}
                >
                  <td className="py-2 px-2">
                    <div className="font-semibold text-gray-800 text-xs">{r.symbol}</div>
                    <div className="text-gray-400 truncate max-w-[100px] text-[10px]">{r.companyName}</div>
                  </td>
                  <td className="py-2 px-2 text-right text-gray-700 tabular-nums text-xs">
                    {r.currentPrice < 10 ? r.currentPrice.toFixed(3) : r.currentPrice.toFixed(2)}
                  </td>
                  <td className="py-2 px-2 text-center text-sm">{r.goldenCross  ? '✅' : '❌'}</td>
                  <td className="py-2 px-2 text-center text-sm">{r.aboveMALines ? '✅' : '❌'}</td>
                  <td className="py-2 px-2 text-center text-sm">{r.ma125Support ? '✅' : '❌'}</td>
                  <td className="py-2 px-2 text-center text-sm">{r.trendStable  ? '✅' : '❌'}</td>
                  <td className={`py-2 px-2 text-right tabular-nums text-xs ${scoreColor}`}>{r.score}</td>
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
