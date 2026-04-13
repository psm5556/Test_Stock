'use client';

import { useEffect, useRef, useId } from 'react';

interface TradingViewChartProps {
  symbol: string;
}

/** Convert Yahoo Finance symbol to TradingView format */
function toTVSymbol(symbol: string): string {
  if (symbol.endsWith('.KS')) {
    const code = symbol.replace('.KS', '');
    return `KRX:${code}`;
  }
  return symbol;
}

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    TradingView: any;
  }
}

export default function TradingViewChart({ symbol }: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<unknown>(null);
  const containerId = useId().replace(/:/g, '');
  const tvSymbol = toTVSymbol(symbol);

  useEffect(() => {
    // Remove previous widget if exists
    if (containerRef.current) {
      containerRef.current.innerHTML = '';
    }

    const scriptId = 'tradingview-script';
    const existingScript = document.getElementById(scriptId);

    const initWidget = () => {
      if (!containerRef.current) return;
      containerRef.current.innerHTML = `<div id="${containerId}" style="height:100%"></div>`;

      widgetRef.current = new window.TradingView.widget({
        container_id: containerId,
        autosize: true,
        symbol: tvSymbol,
        interval: 'D',
        timezone: 'Asia/Seoul',
        theme: 'light',
        style: '1',
        locale: 'kr',
        toolbar_bg: '#ffffff',
        enable_publishing: false,
        allow_symbol_change: false,
        hide_top_toolbar: false,
        hide_side_toolbar: false,
        studies: [
          'MASimple@tv-basicstudies',
        ],
        overrides: {
          'mainSeriesProperties.candleStyle.upColor': '#ef4444',
          'mainSeriesProperties.candleStyle.downColor': '#3b82f6',
          'mainSeriesProperties.candleStyle.borderUpColor': '#ef4444',
          'mainSeriesProperties.candleStyle.borderDownColor': '#3b82f6',
          'mainSeriesProperties.candleStyle.wickUpColor': '#ef4444',
          'mainSeriesProperties.candleStyle.wickDownColor': '#3b82f6',
        },
      });
    };

    if (!existingScript) {
      const script = document.createElement('script');
      script.id = scriptId;
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = initWidget;
      document.head.appendChild(script);
    } else if (window.TradingView) {
      initWidget();
    } else {
      existingScript.addEventListener('load', initWidget);
    }

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tvSymbol]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full"
      style={{ minHeight: '480px' }}
    />
  );
}
