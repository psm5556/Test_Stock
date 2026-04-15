'use client';

import { useEffect, useRef } from 'react';
import type { AnalysisResult } from '@/types';

interface StockChartProps {
  result: AnalysisResult;
}

// MA 설정 – MA200·240·365 표시 제외
const MA_CONFIG = [
  { key: 'ma20'  as const, label: 'MA20',  color: '#ef4444', width: 1.5 },
  { key: 'ma60'  as const, label: 'MA60',  color: '#22c55e', width: 1.5 },
  { key: 'ma125' as const, label: 'MA125', color: '#3b82f6', width: 2   },
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
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      type LineSeries = any;

      const chart = createChart(container, {
        width: container.clientWidth || 300,
        height: container.clientHeight || 300,
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
      // MA20 시리즈 참조를 별도로 저장 (골든크로스 마커 부착용)
      let ma20Series: LineSeries = null;

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

        if (ma.key === 'ma20') ma20Series = lineSeries;
      }

      // ── 골든크로스 마커
      // MA20 라인 시리즈에 position: 'inBar' 로 붙여서
      // 마커가 MA20 값(≈ 교차점 가격)에 정확히 위치하도록 함.
      // candleSeries 에 붙이면 캔들 저가 아래(belowBar)에 표시되어 위치가 틀림.
      if (result.goldenCross && result.crossDate && ma20Series) {
        ma20Series.setMarkers([
          {
            time:     result.crossDate as Time,
            position: 'inBar',   // 라인 시리즈의 해당 값 위치(= MA20값 = 교차점)
            color:    '#f59e0b',
            shape:    'circle',  // 교차점을 원으로 강조
            text:     '🌟 골든크로스',
            size:     1.5,
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

  return <div ref={containerRef} className="w-full h-full" style={{ minHeight: '200px' }} />;
}
