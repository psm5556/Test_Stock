export interface OHLCVBar {
  time: string; // 'YYYY-MM-DD'
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MALines {
  ma20: (number | null)[];
  ma60: (number | null)[];
  ma125: (number | null)[];
  ma200: (number | null)[];
  ma240: (number | null)[];
  ma365: (number | null)[];
}

export interface AnalysisResult {
  symbol: string;
  companyName: string;
  currentPrice: number;
  goldenCross: boolean;
  crossDate: string | null;
  aboveMALines: boolean;
  ma125Support: boolean;
  supportCount: number;
  trendStable: boolean;
  score: number;
  period: string;
  periodLabel: string;
  bars: OHLCVBar[];
  maLines: MALines;
}

export interface FearGreedPoint {
  date: string;
  value: number;
}

export interface FearGreedData {
  current: number;
  label: string;
  history: FearGreedPoint[];
}

export interface SheetConfig {
  sheetId: string;
  sheetName: string;
}

export type MarketKey =
  | 'GOOGLE_SHEETS'
  | 'SP500' | 'NASDAQ' | 'ALL' | 'KOSPI' | 'KOSDAQ'
  | 'FUTURE_LEADERS' | 'AEROSPACE' | 'QUANTUM' | 'LONGEVITY'
  | 'SYNTHETIC_BIO' | 'STABLECOIN' | 'DATACENTER_SEMI' | 'BCI'
  | 'DATA_CENTER_ENERGY' | 'DATA_CENTER_INFRASTRUCTURE'
  | 'MEGA_CAP_LEADERS' | 'CYBERSECURITY' | 'SATELLITE_COMMUNICATIONS'
  | 'SUBSEA_CABLES' | 'OCEAN_PLASTICS';

export type PeriodKey = '1mo' | '3mo' | '6mo' | '1y' | '2y' | '5y';

export const MARKET_LABELS: Record<MarketKey, string> = {
  GOOGLE_SHEETS: '📊 Google Sheets 종목',
  SP500: 'S&P 500 (전체 500개)',
  NASDAQ: 'NASDAQ (전체 주요 기술주)',
  ALL: '미국 전체 (S&P500 + NASDAQ)',
  KOSPI: 'KOSPI (200개)',
  KOSDAQ: 'KOSDAQ (50개)',
  FUTURE_LEADERS: '🌟 미래 대장주 엄선',
  AEROSPACE: '🚀 우주항공 섹터',
  QUANTUM: '⚛️ 양자컴퓨터 섹터',
  LONGEVITY: '🧬 노화역전/장수 섹터',
  SYNTHETIC_BIO: '🔬 합성생물학 섹터',
  STABLECOIN: '💰 스테이블코인/암호화폐',
  DATACENTER_SEMI: '❄️ 데이터센터 반도체 섹터',
  BCI: '🧠 뇌-컴퓨터 인터페이스 섹터',
  DATA_CENTER_ENERGY: '🔋 데이터센터 에너지 섹터',
  DATA_CENTER_INFRASTRUCTURE: '🏗️ 데이터센터 인프라 섹터',
  MEGA_CAP_LEADERS: '🏆 초우량 글로벌 빅테크',
  CYBERSECURITY: '🛡️ 사이버보안 섹터',
  SATELLITE_COMMUNICATIONS: '🛰️ 위성통신 섹터',
  SUBSEA_CABLES: '🌊 해저케이블 섹터',
  OCEAN_PLASTICS: '♻️ 해양플라스틱 섹터',
};

export const PERIOD_LABELS: Record<PeriodKey, string> = {
  '1mo': '1개월',
  '3mo': '3개월',
  '6mo': '6개월',
  '1y': '1년',
  '2y': '2년',
  '5y': '5년',
};

export const PERIOD_DAYS: Record<PeriodKey, number> = {
  '1mo': 30,
  '3mo': 90,
  '6mo': 180,
  '1y': 365,
  '2y': 730,
  '5y': 1825,
};
