'use client';

import { useEffect, useRef } from 'react';
import type { FearGreedData } from '@/types';

interface FearGreedWidgetProps {
  data: FearGreedData | null;
  loading: boolean;
}

function getColor(value: number) {
  if (value >= 75) return { bg: 'bg-red-500', text: 'text-red-600', border: 'border-red-400', label: '극도의 탐욕', hex: '#ef4444' };
  if (value >= 55) return { bg: 'bg-orange-400', text: 'text-orange-500', border: 'border-orange-400', label: '탐욕', hex: '#f97316' };
  if (value >= 45) return { bg: 'bg-gray-400', text: 'text-gray-500', border: 'border-gray-400', label: '중립', hex: '#6b7280' };
  if (value >= 25) return { bg: 'bg-blue-500', text: 'text-blue-600', border: 'border-blue-400', label: '공포', hex: '#3b82f6' };
  return { bg: 'bg-indigo-700', text: 'text-indigo-700', border: 'border-indigo-500', label: '극도의 공포', hex: '#4338ca' };
}

function MiniLineChart({ data }: { data: { date: string; value: number }[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || data.length === 0) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const pad = { top: 12, bottom: 20, left: 8, right: 8 };

    ctx.clearRect(0, 0, w, h);

    const values = data.map((d) => d.value);
    const minV = Math.min(...values);
    const maxV = Math.max(...values);
    const range = maxV - minV || 1;

    const toX = (i: number) => pad.left + (i / (data.length - 1)) * (w - pad.left - pad.right);
    const toY = (v: number) => pad.top + (1 - (v - minV) / range) * (h - pad.top - pad.bottom);

    // Zone fills
    const zones = [
      { lo: 75, hi: 100, color: 'rgba(239,68,68,0.08)' },
      { lo: 55, hi: 75, color: 'rgba(249,115,22,0.08)' },
      { lo: 45, hi: 55, color: 'rgba(107,114,128,0.06)' },
      { lo: 25, hi: 45, color: 'rgba(59,130,246,0.08)' },
      { lo: 0, hi: 25, color: 'rgba(67,56,202,0.10)' },
    ];
    zones.forEach(({ lo, hi, color }) => {
      ctx.fillStyle = color;
      ctx.fillRect(pad.left, toY(hi), w - pad.left - pad.right, toY(lo) - toY(hi));
    });

    // Horizontal guide lines
    [25, 45, 55, 75].forEach((level) => {
      const y = toY(level);
      ctx.save();
      ctx.strokeStyle = 'rgba(0,0,0,0.1)';
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(w - pad.right, y);
      ctx.stroke();
      ctx.restore();
    });

    // Gradient fill under the line
    const gradient = ctx.createLinearGradient(0, pad.top, 0, h - pad.bottom);
    gradient.addColorStop(0, 'rgba(99,102,241,0.25)');
    gradient.addColorStop(1, 'rgba(99,102,241,0)');
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(values[0]));
    for (let i = 1; i < data.length; i++) ctx.lineTo(toX(i), toY(values[i]));
    ctx.lineTo(toX(data.length - 1), h - pad.bottom);
    ctx.lineTo(toX(0), h - pad.bottom);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(values[0]));
    for (let i = 1; i < data.length; i++) ctx.lineTo(toX(i), toY(values[i]));
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.setLineDash([]);
    ctx.stroke();

    // Current dot
    const lastX = toX(data.length - 1);
    const lastY = toY(values[values.length - 1]);
    const c = getColor(values[values.length - 1]);
    ctx.beginPath();
    ctx.arc(lastX, lastY, 5, 0, Math.PI * 2);
    ctx.fillStyle = c.hex;
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Date labels
    ctx.fillStyle = 'rgba(0,0,0,0.4)';
    ctx.font = '9px system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(data[0].date.slice(0, 7), pad.left, h - 4);
    ctx.textAlign = 'right';
    ctx.fillText(data[data.length - 1].date.slice(0, 7), w - pad.right, h - 4);
  }, [data]);

  return <canvas ref={canvasRef} className="w-full h-full" />;
}

export default function FearGreedWidget({ data, loading }: FearGreedWidgetProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-200 p-5 flex items-center justify-center h-40">
        <div className="text-sm text-gray-400 animate-pulse">공포 탐욕 지수 로딩 중...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-2xl border border-gray-200 p-5 flex items-center justify-center h-40 text-sm text-gray-400">
        분석을 시작하면 공포 탐욕 지수가 표시됩니다.
      </div>
    );
  }

  const c = getColor(data.current);

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
        😨 CNN 공포 &amp; 탐욕 지수
      </h3>
      <div className="flex items-stretch gap-5">
        {/* Score card */}
        <div className={`shrink-0 flex flex-col items-center justify-center border-2 ${c.border} rounded-xl px-6 py-4 min-w-[110px]`}>
          <span className={`text-5xl font-black ${c.text}`}>{data.current.toFixed(0)}</span>
          <span className={`text-sm font-bold mt-1 ${c.text}`}>{c.label}</span>
          <span className="text-xs text-gray-400 mt-1">{data.label}</span>
          {/* Mini gauge bar */}
          <div className="w-full bg-gray-100 rounded-full h-2 mt-3">
            <div
              className={`${c.bg} h-2 rounded-full transition-all`}
              style={{ width: `${data.current}%` }}
            />
          </div>
        </div>

        {/* History chart */}
        <div className="flex-1 min-h-[120px]">
          {data.history.length > 0 ? (
            <MiniLineChart data={data.history} />
          ) : (
            <div className="flex items-center justify-center h-full text-xs text-gray-400">
              히스토리 데이터 없음
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
