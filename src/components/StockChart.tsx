'use client';

import { useEffect, useRef } from 'react';
import type { AnalysisResult } from '@/types';

interface StockChartProps {
  result: AnalysisResult;
}

// MA 설정 (원래 Streamlit 코드와 동일한 색상)
const MA_CONFIG = [
  { key: 'ma20'  as const, label: 'MA20',  color: '#ef4444', width: 1.5 },
  { key: 'ma60'  as const, label: 'MA60',  color: '#22c55e', width: 1.5 },
  { key: 'ma125' as const, label: 'MA125', color: '#3b82f6', width: 2   },
  { key: 'ma200' as const, label: 'MA200', color: '#8b5cf6', width: 1.5 },
  { key: 'ma240' as const, label: 'MA240', color: '#f97316', width: 1.5 },
  { key: 'ma365' as const, label: 'MA365', color: '#9ca3af', width: 1.5 },
] as const;

export default function StockChart({ result }: StockChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    let cleanupFn = () => {};

    import('lightweight-charts').then(({ createChart, ColorType, CrosshairMode, LineStyle }) => {
      if (!container) return;
      container.innerHTML = '';

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      type Time = any;

      const chart = createChart(container, {
        width: container.clientWidth,
        height: container.clientHeight,
        layout: {
          background: { type: ColorType.Solid, color: '#ffffff' },
          textColor: '#374151',
          fontSize: 11,
        },
        grid: {
          vertLines: { color: '#f3f4f6' },
          horzLines: { color: '#f3f4f6' },
        },
        crosshair: { mode: CrosshairMode.Normal },
        rightPriceScale: {
          borderColor: '#e5e7eb',
          scaleMargins: { top: 0.08, bottom: 0.08 },
        },
        timeScale: {
          borderColor: '#e5e7eb',
          timeVisible: true,
          secondsVisible: false,
          rightOffset: 5,
        },
        handleScroll: true,
        handleScale: true,
      });

      // ── 캔들스틱 (양봉: 빨간색, 음봉: 파란색 – 국내 관행)
      const candleSeries = chart.addCandlestickSeries({
        upColor:         '#ef4444',
        downColor:       '#3b82f6',
        borderUpColor:   '#ef4444',
        borderDownColor: '#3b82f6',
        wickUpColor:     '#ef4444',
        wickDownColor:   '#3b82f6',
      });

      candleSeries.setData(
        result.bars.map((b) => ({
          time:  b.time as Time,
          open:  b.open,
          high:  b.high,
          low:   b.low,
          close: b.close,
        })),
      );

      // ── 이동평균선
      for (const ma of MA_CONFIG) {
        const maData = result.maLines[ma.key];
        const points: { time: Time; value: number }[] = [];
        result.bars.forEach((bar, i) => {
          const v = maData[i];
          if (v != null) points.push({ time: bar.time as Time, value: v });
        });
        if (points.length === 0) continue;

        const lineSeries = chart.addLineSeries({
          color: ma.color,
          lineWidth: ma.width as 1 | 2 | 3 | 4,
          title: ma.label,
          priceLineVisible: false,
          lastValueVisible: true,
        });
        lineSeries.setData(points);
      }

      // ── 골든크로스 마커
      if (result.goldenCross && result.crossDate) {
        candleSeries.setMarkers([
          {
            time:     result.crossDate as Time,
            position: 'belowBar',
            color:    '#f59e0b',
            shape:    'arrowUp',
            text:     '🌟 골든크로스',
            size:     2,
          },
        ]);
      }

      // ── "현재가 20,60일선 위" 수평 점선 주석
      if (result.aboveMALines) {
        candleSeries.createPriceLine({
          price:            result.currentPrice,
          color:            '#22c55e',
          lineWidth:        1,
          lineStyle:        LineStyle.Dashed,
          axisLabelVisible: true,
          title:            '▲ 현재가 20·60일선 위',
        });
      }

      // ── ResizeObserver
      const ro = new ResizeObserver(() => {
        if (container) chart.resize(container.clientWidth, container.clientHeight);
      });
      ro.observe(container);

      cleanupFn = () => {
        ro.disconnect();
        chart.remove();
      };
    });

    return () => cleanupFn();
  }, [result]);

  return <div ref={containerRef} className="w-full h-full" />;
}
