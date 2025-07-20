import streamlit as st
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
from fear_and_greed import get
import warnings
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

class StockAnalyzer:
    """주식 기술적 분석을 위한 클래스"""
    
    def __init__(self):
        """초기화"""
        self.fear_greed_current = None
        self.fear_greed_label = None
        self.fear_greed_history = None
        self.current_period = '6mo'  # 기본값
        
        # 기간별 라벨 매핑
        self.period_labels = {
            '1mo': '1개월',
            '3mo': '3개월', 
            '6mo': '6개월',
            '1y': '1년',
            '2y': '2년',
            '5y': '5년'
        }
        
        # 기간별 일수 매핑
        self.period_days = {
            '1mo': 30,
            '3mo': 90,
            '6mo': 180,
            '1y': 365,
            '2y': 730,
            '5y': 1825
        }
    
    def _get_sector_symbols(self, sector_type):
        """섹터별 주요 기업 심볼 가져오기"""
        sector_symbols = {
            'AEROSPACE': [
                # 우주항공 기업들
                'BA', 'LMT', 'RTX', 'NOC', 'GD', 'LHX', 'TDG', 'HWM', 'LDOS', 'KTOS',
                'AVAV', 'RKLB', 'SPCE', 'ASTR', 'BLDE', 'JOBY', 'EVTL', 'LILM', 'ACHR',
                'MAXR', 'SPIR', 'IRDM', 'VSAT', 'GSAT', 'ASTS', 'ORBC', 'GILT',
                'CAT', 'HON', 'TXT', 'PH', 'ITT', 'CW', 'MOG-A'
            ],
            'QUANTUM': [
                # 양자컴퓨터 관련 기업들
                'IBM', 'GOOGL', 'MSFT', 'NVDA', 'INTC', 'AMD', 'QCOM', 'MRVL',
                'IONQ', 'RGTI', 'QUBT', 'ARQQ', 'QTUM', 'DEFN', 'AMZN', 'CRM',
                'ORCL', 'CSCO', 'TSM', 'ASML', 'KLAC', 'LRCX', 'AMAT', 'TXN'
            ],
            'LONGEVITY': [
                # 노화역전/장수 기업들
                'GILD', 'AMGN', 'REGN', 'VRTX', 'BIIB', 'MRNA', 'NVAX', 'BNTX', 'ILMN',
                'TMO', 'DHR', 'A', 'DXCM', 'ISRG', 'VEEV', 'BSX', 'MDT', 'ABT',
                'JNJ', 'PFE', 'ABBV', 'LLY', 'BMY', 'MRK', 'GSK', 'NVO', 'AZN',
                'UNITY', 'SEER', 'TWST', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'VERV'
            ],
            'SYNTHETIC_BIO': [
                # 합성생물학 기업들
                'TWST', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'VERV', 'SEER', 'UNITY', 'FATE',
                'BLUE', 'GILD', 'MRNA', 'BNTX', 'NVAX', 'DNA', 'SYN', 'AMRS',
                'CODX', 'PACB', 'ILMN', 'TMO', 'DHR', 'A', 'LIFE', 'BIO', 'CDNA',
                'FOLD', 'RGNX', 'SGEN', 'HALO', 'EVGN', 'CYTK', 'ABUS', 'IMUX'
            ],
            'STABLECOIN': [
                # 스테이블코인/암호화폐 관련 기업들
                'COIN', 'MSTR', 'RIOT', 'MARA', 'CLSK', 'BITF', 'HUT', 'CAN', 'BTBT',
                'SQ', 'PYPL', 'MA', 'V', 'NVDA', 'AMD', 'TSLA', 'HOOD', 'SOFI',
                'AFRM', 'UPST', 'LC', 'GBTC', 'ETHE', 'LTCN', 'BITO', 'ARKK'
            ],
            'DATACENTER_COOLING': [
                # 데이터센터 냉각기술 기업들
                'NVDA', 'AMD', 'INTC', 'QCOM', 'MRVL', 'AMAT', 'LRCX', 'KLAC',
                'JCI', 'CARR', 'ITW', 'EMR', 'HON', 'DHR', 'TMO', 'WAT', 'XYL',
                'VLTO', 'CGNX', 'TER', 'KEYS', 'NOVT', 'NDSN', 'HUBB',
                'AAON', 'SMTC', 'EVTC', 'DLR', 'EQIX', 'AMT'
            ],
            'BCI': [
                # 뇌-컴퓨터 인터페이스(BCI) 기업들
                'NVDA', 'GOOGL', 'MSFT', 'META', 'AAPL', 'TSLA', 'NEGG', 'SNAP', 'MRNA',
                'ILMN', 'TMO', 'DHR', 'A', 'ISRG', 'VEEV', 'BSX', 'MDT', 'ABT',
                'JNJ', 'DXCM', 'CTRL', 'NURO', 'SYNC', 'LFMD', 'AXGN', 'PRTS',
                'GMED', 'KALA', 'INVA', 'PHVS', 'SENS', 'CRMD', 'KRYS', 'ATNF'
            ],
            'FUTURE_LEADERS': [
                # 미래 대장주 후보들 (각 섹터의 최고 유망주만 선별)
                # 🚀 우주항공 대장주
                'RKLB', 'SPCE', 'BA', 'LMT', 'RTX', 'NOC', 'MAXR', 'ASTS',
                # ⚛️ 양자컴퓨터 대장주  
                'IONQ', 'RGTI', 'QUBT', 'IBM', 'GOOGL', 'NVDA', 'MSFT',
                # 🧬 노화역전/장수 대장주
                'UNITY', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'VERV', 'TWST', 'GILD', 'MRNA',
                # 🔬 합성생물학 대장주
                'DNA', 'TWST', 'AMRS', 'CRSP', 'EDIT', 'FATE', 'BLUE', 'SYN',
                # 💰 스테이블코인/암호화폐 대장주
                'COIN', 'MSTR', 'RIOT', 'MARA', 'CLSK', 'SQ', 'PYPL', 'HOOD',
                # ❄️ 데이터센터 냉각 대장주
                'NVDA', 'AMD', 'JCI', 'CARR', 'XYL', 'SMTC', 'DLR', 'EQIX',
                # 🧠 BCI 대장주
                'NVDA', 'TSLA', 'META', 'GOOGL', 'ISRG', 'DXCM', 'BSX', 'SYNC',
                # 🤖 AI/로봇 대장주
                'NVDA', 'AMD', 'GOOGL', 'MSFT', 'TSLA', 'META', 'PLTR', 'C3AI'
            ]
        }
        
        return sector_symbols.get(sector_type, [])
        
    def _get_sp500_symbols_full(self):
        """S&P 500 전체 기업 리스트 (500개)"""
        return [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'BRK-B', 'LLY', 'AVGO', 
            'UNH', 'JPM', 'XOM', 'V', 'PG', 'JNJ', 'MA', 'HD', 'CVX', 'ABBV',
            'PFE', 'BAC', 'KO', 'COST', 'TMO', 'WMT', 'CSCO', 'DIS', 'ABT', 'DHR',
            'MRK', 'ADBE', 'CRM', 'NFLX', 'INTC', 'AMD', 'QCOM', 'IBM', 'GE', 'BA',
            'CAT', 'HON', 'RTX', 'GS', 'MS', 'VZ', 'CMCSA', 'NKE', 'ORCL', 'PEP',
            'TXN', 'PM', 'T', 'AMGN', 'COP', 'UNP', 'NEE', 'LOW', 'TMUS', 'AMAT',
            'ISRG', 'BKNG', 'VRTX', 'ADP', 'SBUX', 'GILD', 'ADI', 'LRCX', 'MDLZ', 'REGN',
            'PYPL', 'KLAC', 'MRVL', 'ORLY', 'CDNS', 'SNPS', 'NXPI', 'WDAY', 'ABNB', 'FTNT',
            'DDOG', 'TEAM', 'ZM', 'CRWD', 'ZS', 'OKTA', 'DOCU', 'NOW', 'PANW', 'MU',
            'ANET', 'LULU', 'ODFL', 'EXC', 'CTAS', 'ROST', 'TJX', 'MCD', 'YUM', 'CMG',
            'MMC', 'ACN', 'LIN', 'SPGI', 'TFC', 'BLK', 'AON', 'ICE', 'COF', 'FI',
            'BSX', 'SO', 'PLD', 'DUK', 'SCHW', 'CL', 'CB', 'USB', 'BMY', 'DE',
            'HCA', 'NSC', 'APH', 'SYK', 'ZTS', 'PNC', 'CI', 'WM', 'EQIX', 'CCI',
            'AMT', 'MCO', 'ITW', 'TGT', 'FISV', 'CSX', 'BDX', 'NOC', 'FCX', 'SHW',
            'GD', 'EMR', 'PGR', 'GM', 'MCK', 'AJG', 'TRV', 'PSA', 'WELL',
            'ECL', 'ROP', 'CARR', 'ALL', 'AEP', 'WMB', 'CME', 'DLR', 'O', 'PCAR',
            'OKE', 'KMI', 'TEL', 'AIG', 'HLT', 'PSX', 'SPG', 'CTSH', 'PAYX', 'SRE',
            'F', 'AZO', 'MSI', 'CNC', 'MSCI', 'CMI', 'PRU', 'AFL', 'FAST', 'GWW',
            'RSG', 'KR', 'OTIS', 'CBRE', 'VRSK', 'ADSK', 'EA', 'CTVA', 'HUM', 'IDXX',
            'EW', 'XEL', 'DD', 'COIN', 'HPQ', 'DXCM', 'GRMN', 'WEC', 'GEHC', 'GLW',
            'KHC', 'ED', 'WBA', 'NDAQ', 'RMD', 'BK', 'DOW', 'AWK', 'ANSS', 'A',
            'EXR', 'IRM', 'FANG', 'PPG', 'CPRT', 'ROK', 'URI', 'MNST', 'SBAC', 'STZ',
            'DVN', 'IT', 'VICI', 'KEYS', 'MLM', 'ACGL', 'VMC', 'CHTR', 'MPWR',
            'EFX', 'BIIB', 'CDW', 'TROW', 'EBAY', 'NTAP', 'TSN', 'CSGP', 'WAB', 'HUBB'
        ]
    
    def _get_nasdaq_symbols_full(self):
        """NASDAQ 전체 주요 기업 리스트 (주요 기술주 중심 400개+)"""
        return [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ADBE',
            'CRM', 'NFLX', 'INTC', 'AMD', 'QCOM', 'TMUS', 'AMAT', 'ISRG', 'BKNG', 'VRTX',
            'ADP', 'SBUX', 'GILD', 'ADI', 'LRCX', 'MDLZ', 'REGN', 'PYPL', 'KLAC', 'MRVL',
            'ORLY', 'CDNS', 'SNPS', 'NXPI', 'WDAY', 'ABNB', 'FTNT', 'DDOG', 'TEAM', 'ZM',
            'CRWD', 'ZS', 'OKTA', 'DOCU', 'NOW', 'PANW', 'MU', 'ANET', 'LULU', 'ODFL',
            'CPRT', 'CSCO', 'CTAS', 'FAST', 'VRSK', 'ADSK', 'EA', 'DXCM', 'GRMN', 'IDXX',
            'NDAQ', 'ANSS', 'MNST', 'MPWR', 'CDW', 'EBAY', 'NTAP', 'BIIB', 'CHTR', 'ALGN',
            'DLTR', 'SWKS', 'TTWO', 'SMCI', 'PODD', 'AKAM', 'FICO', 'ENPH', 'FSLR', 'JNPR',
            'MCHP', 'WDC', 'XRAY', 'CTXS', 'ULTA', 'FISV', 'PAYX', 'WBA', 'COST', 'FOX',
            'FOXA', 'MRNA', 'BMRN', 'TECH', 'ILMN', 'INCY', 'SIRI', 'PCTY', 'EXPD', 'MELI',
            'KDP', 'LCID', 'ROKU', 'HOOD', 'RIVN', 'SGEN', 'NTES', 'JD', 'PDD', 'BIDU',
            'SPLK', 'PTON', 'ZI', 'SHOP', 'SPOT', 'PLUG', 'FUBO', 'ZG',
            'UBER', 'LYFT', 'DASH', 'SNOW', 'RBLX', 'PLTR', 'COIN', 'SOFI', 'UPST',
            'AFRM', 'SQ', 'PINS', 'SNAP'
        ]
    
    def _get_us_market_cap_from_yahoo(self, market_type='SP500', limit=None):
        """미국 시가총액 상위 종목 가져오기 (전체 리스트 + 섹터별)"""
        try:
            print(f"[DEBUG] 미국 {market_type} 종목 조회")
            
            if market_type == 'SP500':
                symbols = self._get_sp500_symbols_full()
            elif market_type == 'NASDAQ':
                symbols = self._get_nasdaq_symbols_full()
            elif market_type == 'ALL':
                # SP500과 NASDAQ 합치기 (중복 제거)
                sp500 = self._get_sp500_symbols_full()
                nasdaq = self._get_nasdaq_symbols_full()
                symbols = list(set(sp500 + nasdaq))  # 중복 제거
            elif market_type in ['AEROSPACE', 'QUANTUM', 'LONGEVITY', 'SYNTHETIC_BIO', 'STABLECOIN', 'DATACENTER_COOLING', 'BCI', 'FUTURE_LEADERS']:
                # 섹터별 종목 가져오기
                symbols = self._get_sector_symbols(market_type)
            else:
                symbols = self._get_sp500_symbols_full()
            
            if limit:
                symbols = symbols[:limit]
                
            print(f"[DEBUG] {market_type} 총 종목 수: {len(symbols)}")
            return symbols
            
        except Exception as e:
            print(f"[WARNING] 미국 {market_type} 조회 실패: {e}")
            return None

    def get_top_companies_by_market_cap(self, market='SP500', limit=None):
        """시가총액 기준 상위 기업 가져오기 (전체 또는 제한 + 섹터별)"""
        print(f"[DEBUG] 시가총액 기업 조회 시작: market={market}, limit={limit}")
        
        try:
            companies = {}
            
            if market in ['SP500', 'NASDAQ', 'ALL', 'AEROSPACE', 'QUANTUM', 'LONGEVITY', 'SYNTHETIC_BIO', 'STABLECOIN', 'DATACENTER_COOLING', 'BCI', 'FUTURE_LEADERS']:
                # 미국 종목은 하드코딩된 회사명 사용
                us_symbols = self._get_us_market_cap_from_yahoo(market, limit)
                if us_symbols:
                    # 하드코딩된 회사명 매핑 사용
                    company_names = self._get_us_company_names()
                    # 섹터별 회사명 매핑 추가
                    sector_company_names = self._get_sector_company_names()
                    company_names.update(sector_company_names)
                    
                    for symbol in us_symbols:
                        companies[symbol] = company_names.get(symbol, symbol)
        
            elif market in ['KOSPI', 'KOSDAQ']:
                # 한국 종목은 병렬 처리로 회사명 가져오기
                korea_symbols = self._get_korea_market_cap_from_naver(market, limit or 50)
                if korea_symbols:
                    # 병렬 처리로 회사명 가져오기
                    companies = self._get_korea_company_names_parallel(korea_symbols)
            
            print(f"[DEBUG] 최종 종목 수: {len(companies)}개")
            return companies
            
        except Exception as e:
            print(f"[ERROR] 시가총액 조회 중 오류: {e}")
            return {}
    
    def _get_korea_market_cap_from_naver(self, market_type='KOSPI', limit=50):
        """네이버 금융에서 한국 시가총액 순위 가져오기"""
        try:
            print(f"[DEBUG] 네이버 금융에서 {market_type} 시가총액 순위 조회 시도")
            
            all_codes = []
            page = 1
            
            # KOSPI와 KOSDAQ URL 구분
            if market_type == 'KOSPI':
                base_url = "https://finance.naver.com/sise/sise_market_sum.nhn"
            elif market_type == 'KOSDAQ':
                base_url = "https://finance.naver.com/sise/sise_market_sum.nhn?sosok=1"
            else:
                base_url = "https://finance.naver.com/sise/sise_market_sum.nhn"
            
            while len(all_codes) < limit and page <= 2:  # 페이지 수 줄임
                url = f"{base_url}?&page={page}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # 정규표현식으로 직접 종목코드 추출
                pattern = r'/item/main\.naver\?code=(\d{6})'
                matches = re.findall(pattern, response.text)
                
                # 중복 제거하면서 추가
                all_codes.extend(matches)
                all_codes = list(dict.fromkeys(all_codes))  # 순서 유지하면서 중복 제거
                page += 1
            
            # limit 개수만큼 선택하고 .KS 붙이기
            symbols = [f"{code}.KS" for code in all_codes[:limit]]
            
            print(f"[DEBUG] 네이버에서 {len(symbols)}개 {market_type} 종목 추출 성공")
            return symbols
            
        except Exception as e:
            print(f"[WARNING] 네이버 금융 {market_type} 조회 실패: {e}")
            return None
        
    def get_period_days(self, period):
        """기간을 일수로 변환"""
        return self.period_days.get(period, 180)
    
    def _get_extended_period_for_ma(self, period):
        """125일 이동평균선을 위한 확장된 기간 계산"""
        extended_periods = {
            '1mo': '1y',    # 1개월 표시 → 1년 데이터 가져오기
            '3mo': '1y',    # 3개월 표시 → 1년 데이터 가져오기  
            '6mo': '2y',    # 6개월 표시 → 2년 데이터 가져오기
            '1y': '3y',     # 1년 표시 → 3년 데이터 가져오기
            '2y': '5y',     # 2년 표시 → 5년 데이터 가져오기
            '5y': 'max'     # 5년 표시 → 최대 데이터 가져오기
        }
        return extended_periods.get(period, '2y')
        
    def get_fear_greed_index(self, period='6mo'):
        """CNN Fear & Greed Index 가져오기"""
        try:
            self.current_period = period  # 현재 기간 저장
            
            # 현재 공포 & 탐욕 지수
            fear_greed_data = get()
            self.fear_greed_current = fear_greed_data.value
            self.fear_greed_label = fear_greed_data.description
            
            print(f"[DEBUG] 공포탐욕지수 수신 성공: {self.fear_greed_current}")
            
        except Exception as e:
            print(f"Fear & Greed Index 가져오기 실패: {e}")
            self.fear_greed_current = 50.0
            self.fear_greed_label = "Neutral"
        
        try:
            # CNN에서 실제 과거 데이터 가져오기
            self.fear_greed_history = self._get_real_fear_greed_history(period)
            if self.fear_greed_history is not None:
                print(f"[DEBUG] 공포탐욕지수 히스토리 생성 완료: {len(self.fear_greed_history)}개 데이터")
            else:
                print("[WARNING] CNN 히스토리 데이터 가져오기 실패")
                
        except Exception as e:
            print(f"공포탐욕지수 히스토리 생성 실패: {e}")
            self.fear_greed_history = None
                
        return self.fear_greed_current
    
    def _get_real_fear_greed_history(self, period='6mo'):
        """실제 CNN Fear & Greed Index 과거 데이터 가져오기"""
        try:
            # CNN Fear & Greed Index API 엔드포인트
            days = self.get_period_days(period)
            url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata?start=0&end={days}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'fear_and_greed_historical' in data:
                scores = data['fear_and_greed_historical']
                
                # 데이터프레임으로 변환
                df = pd.DataFrame(scores['data'])
                df['x'] = pd.to_datetime(df['x'], unit='ms')
                df = df.rename(columns={'x': 'Date', 'y': 'Value'})
                df = df[['Date', 'Value']]
                
                return df
                
        except Exception as e:
            print(f"[WARNING] CNN API 데이터 가져오기 실패: {e}")
            return None
    
    def get_fear_greed_chart(self):
        """공포 & 탐욕 지수 차트 생성"""
        period = getattr(self, 'current_period', '6mo')  # 현재 설정된 기간 사용
        
        if self.fear_greed_history is None:
            return go.Figure()
        
        fig = go.Figure()
        
        # 공포 & 탐욕 지수 라인
        fig.add_trace(go.Scatter(
            x=self.fear_greed_history['Date'],
            y=self.fear_greed_history['Value'],
            mode='lines',
            name='Fear & Greed Index',
            line=dict(color='purple', width=2),
            fill='tonexty'
        ))
        
        # 구간별 색상 영역 추가
        fig.add_hline(y=75, line=dict(color="red", width=1, dash="dash"), 
                      annotation_text="극도의 탐욕")
        fig.add_hline(y=55, line=dict(color="orange", width=1, dash="dash"), 
                      annotation_text="탐욕")
        fig.add_hline(y=45, line=dict(color="gray", width=1, dash="dash"), 
                      annotation_text="중립")
        fig.add_hline(y=25, line=dict(color="blue", width=1, dash="dash"), 
                      annotation_text="공포")
        
        # 현재값 포인트 추가
        if self.fear_greed_current and self.fear_greed_history is not None and not self.fear_greed_history.empty:
            fig.add_trace(go.Scatter(
                x=[self.fear_greed_history['Date'].iloc[-1]],
                y=[self.fear_greed_current],
                mode='markers',
                marker=dict(color='red', size=10),
                name=f'현재: {self.fear_greed_current:.1f}'
            ))
        
        period_label = self.period_labels.get(period, period)
        
        fig.update_layout(
            title=f"공포 & 탐욕 지수 ({period_label})",
            xaxis_title="날짜",
            yaxis_title="지수",
            height=300,
            showlegend=True,
            # plot_bgcolor='white',
            # paper_bgcolor='white',
            xaxis=dict(gridcolor='lightgray'),
            yaxis=dict(range=[0, 100], gridcolor='lightgray'),
            margin=dict(t=40, b=40, l=50, r=50)
        )
        
        return fig
    
    def calculate_moving_averages(self, df):
        """이동평균선 계산"""
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['MA125'] = df['Close'].rolling(window=125).mean()
        return df
    
    def check_golden_cross(self, df):
        """골든크로스 확인 - 최근 10일 내에 발생했는지 확인"""
        if len(df) < 10:
            return False, None
        
        # 최근 10일간의 데이터 확인
        recent_data = df.tail(10)
        
        for i in range(1, len(recent_data)):
            current_20 = recent_data['MA20'].iloc[i]
            current_60 = recent_data['MA60'].iloc[i]
            current_125 = recent_data['MA125'].iloc[i]
            prev_20 = recent_data['MA20'].iloc[i-1]
            prev_60 = recent_data['MA60'].iloc[i-1]
            
            # 골든크로스 조건:
            # 1. 이전에는 20일선이 60일선 아래
            # 2. 현재는 20일선이 60일선 위
            # 3. 두 이동평균선이 모두 125일선 아래에 있어야 함
            golden_cross = (
                (prev_20 <= prev_60) and  # 이전: 20일선이 60일선 아래
                (current_20 > current_60) and  # 현재: 20일선이 60일선 위
                (current_20 < current_125) and  # 20일선이 125일선 아래
                (current_60 < current_125)  # 60일선이 125일선 아래
            )
            
            if golden_cross:
                cross_date = recent_data.index[i]
                return True, cross_date
        
        return False, None
    
    def check_above_ma_lines(self, df):
        """현재 가격이 20일선, 60일선 위에 있는지 확인"""
        if len(df) < 1:
            return False
        
        current_price = df['Close'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]
        ma60 = df['MA60'].iloc[-1]
        
        # 현재가가 20일선, 60일선 위에 있는지 확인
        return current_price > ma20 and current_price > ma60
    
    def check_ma125_support(self, df):
        """125일선 위에서 2개 이상 캔들이 지지하는지 확인"""
        if len(df) < 2:
            return False, 0
        
        # 최근 5개 캔들 확인
        recent_candles = df.tail(5)
        support_count = 0
        
        for i in range(len(recent_candles)):
            candle_low = recent_candles['Low'].iloc[i]
            candle_high = recent_candles['High'].iloc[i]
            candle_close = recent_candles['Close'].iloc[i]
            candle_open = recent_candles['Open'].iloc[i]
            ma125 = recent_candles['MA125'].iloc[i]
            
            # 캔들 몸통이 125일선 위에 있는지 확인
            candle_body_low = min(candle_open, candle_close)
            if candle_body_low > ma125:
                support_count += 1
        
        return support_count >= 2, support_count
    
    def check_trend_stability(self, df):
        """추세 안정성 확인 (지그재그 움직임이 아닌 안정적 상승)"""
        if len(df) < 10:
            return False
        
        # 최근 10일간의 이동평균선 기울기 확인
        recent_ma20 = df['MA20'].tail(10)
        recent_ma60 = df['MA60'].tail(10)
        
        # 20일선, 60일선이 상승 추세인지 확인
        ma20_slope = (recent_ma20.iloc[-1] - recent_ma20.iloc[0]) / 10
        ma60_slope = (recent_ma60.iloc[-1] - recent_ma60.iloc[0]) / 10
        
        # 둘 다 상승 추세면서 20일선이 60일선 위에 있어야 함
        return ma20_slope > 0 and ma60_slope > 0 and recent_ma20.iloc[-1] > recent_ma60.iloc[-1]
    
    def analyze_stock(self, symbol, period='6mo', symbols_dict=None):
        """종목 분석"""
        try:
            print(f"[DEBUG] analyze_stock 호출: {symbol}, period={period}")
            
            # 주식 데이터 가져오기
            stock = yf.Ticker(symbol)
            
            # 충분한 데이터를 위해 더 긴 기간으로 가져오기
            extended_period = self._get_extended_period_for_ma(period)
            df_full = stock.history(period=extended_period)
            
            print(f"[DEBUG] {symbol} 전체 데이터 수신: {len(df_full)}행, 기간={extended_period}")
            
            if df_full.empty:
                print(f"[WARNING] {symbol} 데이터가 비어있음")
                return None
            
            # 이동평균선 계산 (전체 데이터로)
            df_full = self.calculate_moving_averages(df_full)
            
            # 선택된 기간만큼 데이터 자르기 (표시용)
            days_to_show = self.get_period_days(period)
            if len(df_full) > days_to_show:
                df_display = df_full.tail(days_to_show).copy()
            else:
                df_display = df_full.copy()
            
            print(f"[DEBUG] {symbol} 표시용 데이터: {len(df_display)}행")
            
            # 회사명 가져오기
            company_name = self.get_company_name(symbol, symbols_dict)
            
            # 각 조건 확인 (표시용 데이터로)
            golden_cross, cross_date = self.check_golden_cross(df_display)
            above_ma_lines = self.check_above_ma_lines(df_display)
            ma125_support, support_count = self.check_ma125_support(df_display)
            trend_stable = self.check_trend_stability(df_display)
            
            # 현재 가격 정보
            current_price = df_display['Close'].iloc[-1]
            
            # 종합 점수 계산
            score = 0
            if golden_cross:
                score += 25
            if above_ma_lines:
                score += 25
            if ma125_support:
                score += 25
            if trend_stable:
                score += 25
            
            # 기간별 라벨 추가
            period_label = self.period_labels.get(period, period)
            
            analysis_result = {
                'symbol': symbol,
                'company_name': company_name,
                'current_price': current_price,
                'golden_cross': golden_cross,
                'cross_date': cross_date,
                'above_ma_lines': above_ma_lines,
                'ma125_support': ma125_support,
                'support_count': support_count,
                'trend_stable': trend_stable,
                'score': score,
                'data': df_display,  # 표시용 데이터 사용
                'period': period,
                'period_label': period_label,
                'data_days': len(df_display)
            }
            
            return analysis_result
            
        except Exception as e:
            print(f"[ERROR] {symbol} 분석 중 오류: {str(e)}")
            return None
    
    def get_company_name(self, symbol, symbols_dict=None):
        """회사명 가져오기"""
        if symbols_dict and symbol in symbols_dict:
            return symbols_dict[symbol]
        
        # symbols_dict가 없으면 yfinance에서 직접 가져오기
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('longName', info.get('shortName', symbol))
        except:
            return symbol
    
    def get_recommendations(self, market='ALL', period='6mo'):
        """추천 종목 리스트 가져오기 (전체 또는 제한 없음)"""
        print(f"[DEBUG] get_recommendations 호출: market={market}, period={period}")
        
        # 현재 기간 저장
        self.current_period = period
        
        # 전체 기업 가져오기 (제한 없음)
        symbols = self.get_top_companies_by_market_cap(market, limit=None)
        
        print(f"[DEBUG] 분석할 종목 수: {len(symbols)}")
        
        # 병렬 처리로 분석 수행
        results = self._analyze_stocks_parallel(symbols, period)
        
        # 점수순으로 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"[DEBUG] 분석 완료: {len(results)}개 종목")
        
        return results

    def _analyze_stocks_parallel(self, symbols, period):
        """병렬 처리로 주식 분석 수행 (대량 데이터 처리 최적화)"""
        results = []
        
        def analyze_single_stock(symbol):
            try:
                analysis = self.analyze_stock(symbol, period, symbols)
                return analysis
            except Exception as e:
                print(f"[ERROR] {symbol} 분석 중 오류: {str(e)}")
                return None
        
        # 대량 데이터 처리를 위한 배치 시스템
        batch_size = 20  # 배치 크기
        symbol_list = list(symbols.keys())
        
        print(f"[DEBUG] 총 {len(symbol_list)}개 종목을 {batch_size}개씩 배치로 처리")
        
        for i in range(0, len(symbol_list), batch_size):
            batch_symbols = symbol_list[i:i+batch_size]
            batch_results = []
            
            print(f"[DEBUG] 배치 {i//batch_size + 1}/{(len(symbol_list)-1)//batch_size + 1} 처리 중 ({len(batch_symbols)}개 종목)")
            
            # 배치별로 병렬 처리
            with ThreadPoolExecutor(max_workers=8) as executor:  # 워커 수 증가
                future_to_symbol = {executor.submit(analyze_single_stock, symbol): symbol for symbol in batch_symbols}
                
                # 완료된 작업부터 결과 수집
                for future in as_completed(future_to_symbol, timeout=180):  # 3분 타임아웃
                    symbol = future_to_symbol[future]
                    try:
                        analysis = future.result(timeout=60)  # 각 작업당 1분 타임아웃
                        if analysis:
                            batch_results.append(analysis)
                    except Exception as e:
                        print(f"[ERROR] {symbol} 결과 처리 중 오류: {str(e)}")
            
            results.extend(batch_results)
            print(f"[DEBUG] 배치 완료: {len(batch_results)}개 성공, 누적 {len(results)}개")
            
            # 배치 간 잠시 대기 (API 제한 방지)
            if i + batch_size < len(symbol_list):
                time.sleep(1)
        
        return results

    def _get_us_company_names(self):
        """미국 기업명 하드코딩 (확장된 버전)"""
        return {
            # 기존 기업들
            'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp.', 'GOOGL': 'Alphabet Inc. Class A',
            'GOOG': 'Alphabet Inc. Class C', 'AMZN': 'Amazon.com Inc.', 'NVDA': 'NVIDIA Corp.', 
            'META': 'Meta Platforms Inc.', 'TSLA': 'Tesla Inc.', 'BRK-B': 'Berkshire Hathaway Inc.',
            'LLY': 'Eli Lilly and Co.', 'AVGO': 'Broadcom Inc.', 'UNH': 'UnitedHealth Group Inc.',
            'JPM': 'JPMorgan Chase & Co.', 'XOM': 'Exxon Mobil Corp.', 'V': 'Visa Inc.',
            'PG': 'Procter & Gamble Co.', 'JNJ': 'Johnson & Johnson', 'MA': 'Mastercard Inc.',
            'HD': 'Home Depot Inc.', 'CVX': 'Chevron Corp.', 'ABBV': 'AbbVie Inc.',
            'PFE': 'Pfizer Inc.', 'BAC': 'Bank of America Corp.', 'KO': 'Coca-Cola Co.',
            'COST': 'Costco Wholesale Corp.', 'TMO': 'Thermo Fisher Scientific Inc.', 'WMT': 'Walmart Inc.',
            'CSCO': 'Cisco Systems Inc.', 'DIS': 'Walt Disney Co.', 'ABT': 'Abbott Laboratories',
            'DHR': 'Danaher Corp.', 'MRK': 'Merck & Co. Inc.', 'ADBE': 'Adobe Inc.',
            'CRM': 'Salesforce Inc.', 'NFLX': 'Netflix Inc.', 'INTC': 'Intel Corp.',
            'AMD': 'Advanced Micro Devices Inc.', 'QCOM': 'Qualcomm Inc.', 'IBM': 'International Business Machines Corp.',
            'GE': 'General Electric Co.', 'BA': 'Boeing Co.', 'CAT': 'Caterpillar Inc.',
            'HON': 'Honeywell International Inc.', 'RTX': 'Raytheon Technologies Corp.', 'GS': 'Goldman Sachs Group Inc.',
            'MS': 'Morgan Stanley', 'VZ': 'Verizon Communications Inc.', 'CMCSA': 'Comcast Corp.',
            'NKE': 'Nike Inc.', 'ORCL': 'Oracle Corp.', 'PEP': 'PepsiCo Inc.',
            'TXN': 'Texas Instruments Inc.', 'PM': 'Philip Morris International Inc.', 'T': 'AT&T Inc.',
            'AMGN': 'Amgen Inc.', 'COP': 'ConocoPhillips', 'UNP': 'Union Pacific Corp.',
            'NEE': 'NextEra Energy Inc.', 'LOW': "Lowe's Companies Inc.", 'TMUS': 'T-Mobile US Inc.',
            'AMAT': 'Applied Materials Inc.', 'ISRG': 'Intuitive Surgical Inc.', 'BKNG': 'Booking Holdings Inc.',
            'VRTX': 'Vertex Pharmaceuticals Inc.', 'ADP': 'Automatic Data Processing Inc.', 'SBUX': 'Starbucks Corp.',
            'GILD': 'Gilead Sciences Inc.', 'ADI': 'Analog Devices Inc.', 'LRCX': 'Lam Research Corp.',
            'MDLZ': 'Mondelez International Inc.', 'REGN': 'Regeneron Pharmaceuticals Inc.', 'PYPL': 'PayPal Holdings Inc.',
            'KLAC': 'KLA Corp.', 'MRVL': 'Marvell Technology Inc.', 'ORLY': "O'Reilly Automotive Inc.",
            'CDNS': 'Cadence Design Systems Inc.', 'SNPS': 'Synopsys Inc.', 'NXPI': 'NXP Semiconductors NV',
            'WDAY': 'Workday Inc.', 'ABNB': 'Airbnb Inc.', 'FTNT': 'Fortinet Inc.',
            'DDOG': 'Datadog Inc.', 'TEAM': 'Atlassian Corp.', 'ZM': 'Zoom Video Communications Inc.',
            'CRWD': 'CrowdStrike Holdings Inc.', 'ZS': 'Zscaler Inc.', 'OKTA': 'Okta Inc.',
            'DOCU': 'DocuSign Inc.', 'NOW': 'ServiceNow Inc.', 'PANW': 'Palo Alto Networks Inc.',
            'MU': 'Micron Technology Inc.', 'ANET': 'Arista Networks Inc.', 'LULU': 'Lululemon Athletica Inc.',
            'ODFL': 'Old Dominion Freight Line Inc.', 'EXC': 'Exelon Corp.', 'CTAS': 'Cintas Corp.',
            'ROST': 'Ross Stores Inc.', 'TJX': 'TJX Companies Inc.', 'MCD': "McDonald's Corp.",
            'YUM': 'Yum! Brands Inc.', 'CMG': 'Chipotle Mexican Grill Inc.'
        }

    def _get_sector_company_names(self):
        """섹터별 기업명 매핑"""
        return {
            # 우주항공 추가 기업들
            'LMT': 'Lockheed Martin Corp.', 'HWM': 'Howmet Aerospace Inc.', 'LHX': 'L3Harris Technologies Inc.',
            'RKLB': 'Rocket Lab USA Inc.', 'SPCE': 'Virgin Galactic Holdings Inc.', 'ASTR': 'Astra Space Inc.',
            'BLDE': 'Blade Air Mobility Inc.', 'JOBY': 'Joby Aviation Inc.', 'EVTL': 'Vertical Aerospace Ltd.',
            'LILM': 'Lilium N.V.', 'ACHR': 'Archer Aviation Inc.', 'MAXR': 'Maxar Technologies Inc.',
            'SPIR': 'Spire Global Inc.', 'IRDM': 'Iridium Communications Inc.', 'VSAT': 'Viasat Inc.',
            'GSAT': 'Globalstar Inc.', 'ASTS': 'AST SpaceMobile Inc.', 'ORBC': 'ORBCOMM Inc.',
            'GILT': 'Gilat Satellite Networks Ltd.', 'TXT': 'Textron Inc.', 'PH': 'Parker-Hannifin Corp.',
            'ITT': 'ITT Inc.', 'CW': 'Curtiss-Wright Corp.', 'MOG-A': 'Moog Inc.',
            
            # 양자컴퓨터 관련 기업들
            'IONQ': 'IonQ Inc.', 'RGTI': 'Rigetti Computing Inc.', 'QUBT': 'Quantum Computing Inc.',
            'ARQQ': 'Arqit Quantum Inc.', 'QTUM': 'Quantum Corp.', 'DEFN': 'DefenseStorm Inc.',
            'TSM': 'Taiwan Semiconductor Manufacturing Co.', 'ASML': 'ASML Holding N.V.',
            
            # 노화역전/장수 기업들
            'NVAX': 'Novavax Inc.', 'BNTX': 'BioNTech SE', 'GSK': 'GlaxoSmithKline plc',
            'NVO': 'Novo Nordisk A/S', 'AZN': 'AstraZeneca plc', 'UNITY': 'Unity Biotechnology Inc.',
            'SEER': 'Seer Inc.', 'TWST': 'Twist Bioscience Corp.', 'CRSP': 'CRISPR Therapeutics AG',
            'EDIT': 'Editas Medicine Inc.', 'NTLA': 'Intellia Therapeutics Inc.', 'BEAM': 'Beam Therapeutics Inc.',
            'VERV': 'Verve Therapeutics Inc.',
            
            # 합성생물학 기업들
            'FATE': 'Fate Therapeutics Inc.', 'BLUE': 'bluebird bio Inc.',
            'DNA': 'Ginkgo Bioworks Holdings Inc.', 'SYN': 'Synthetic Biologics Inc.', 'AMRS': 'Amyris Inc.',
            'CODX': 'Co-Diagnostics Inc.', 'PACB': 'Pacific Biosciences of California Inc.', 'LIFE': 'aTyr Pharma Inc.',
            'BIO': 'Bio-Rad Laboratories Inc.', 'CDNA': 'CareDx Inc.', 'FOLD': 'Amicus Therapeutics Inc.',
            'RGNX': 'REGENXBIO Inc.', 'SGEN': 'Seagen Inc.', 'HALO': 'Halozyme Therapeutics Inc.',
            'EVGN': 'Evogene Ltd.', 'CYTK': 'Cytokinetics Inc.', 'ABUS': 'Arbutus Biopharma Corp.',
            'IMUX': 'Immunic Inc.',
            
            # 스테이블코인/암호화폐 관련 기업들
            'MSTR': 'MicroStrategy Inc.', 'RIOT': 'Riot Blockchain Inc.', 'MARA': 'Marathon Digital Holdings Inc.',
            'CLSK': 'CleanSpark Inc.', 'BITF': 'Bitfarms Ltd.', 'HUT': 'Hut 8 Mining Corp.',
            'CAN': 'Canaan Inc.', 'BTBT': 'Bit Digital Inc.', 'LC': 'LendingClub Corp.',
            'GBTC': 'Grayscale Bitcoin Trust', 'ETHE': 'Grayscale Ethereum Trust', 'LTCN': 'Grayscale Litecoin Trust',
            'BITO': 'ProShares Bitcoin Strategy ETF', 'ARKK': 'ARK Innovation ETF',
            
            # 데이터센터 냉각기술 기업들
            'JCI': 'Johnson Controls International plc', 'XYL': 'Xylem Inc.', 'VLTO': 'Veralto Corp.',
            'CGNX': 'Cognex Corp.', 'NOVT': 'Novanta Inc.',
            'AAON': 'AAON Inc.', 'SMTC': 'Semtech Corp.', 'EVTC': 'Evertec Inc.',
            
            # BCI (뇌-컴퓨터 인터페이스) 기업들
            'NEGG': 'Newegg Commerce Inc.', 'CTRL': 'Control4 Corp.', 'NURO': 'NeuroMetrix Inc.',
            'SYNC': 'Synacor Inc.', 'LFMD': 'LifeMD Inc.', 'AXGN': 'AxoGen Inc.',
            'PRTS': 'CarParts.com Inc.', 'GMED': 'Globus Medical Inc.', 'KALA': 'Kala Pharmaceuticals Inc.',
            'INVA': 'Innoviva Inc.', 'PHVS': 'Pharvaris N.V.', 'SENS': 'Senseonics Holdings Inc.',
            'CRMD': 'CorMedix Inc.', 'KRYS': 'Krystal Biotech Inc.', 'ATNF': '180 Life Sciences Corp.',
            
            # 미래 대장주 후보 기업들 (추가 매핑)
            'C3AI': 'C3.ai Inc.', 'PLTR': 'Palantir Technologies Inc.'
        }

    def _get_korea_company_names_parallel(self, symbols):
        """한국 기업명 병렬 처리로 가져오기"""
        companies = {}
        
        def get_company_name(symbol):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                company_name = info.get('longName', info.get('shortName', symbol))
                return symbol, company_name
            except Exception as e:
                print(f"[WARNING] {symbol} 회사명 조회 실패: {e}")
                return symbol, symbol
        
        # ThreadPoolExecutor로 병렬 처리
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 모든 작업을 제출
            future_to_symbol = {executor.submit(get_company_name, symbol): symbol for symbol in symbols}
            
            # 완료된 작업부터 결과 수집
            for future in as_completed(future_to_symbol):
                symbol, company_name = future.result()
                companies[symbol] = company_name
        
        return companies

    def create_stock_chart(self, analysis):
        """종목 차트 생성"""
        try:
            df = analysis['data']
            symbol = analysis['symbol']
            company_name = analysis['company_name']
            score = analysis['score']
            period_label = analysis['period_label']
            
            # 캔들스틱 차트 생성
            fig = go.Figure()
            
            # 캔들스틱 (양봉: 빨간색, 음봉: 파란색, 투명도 적용)
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='주가',
                increasing=dict(line=dict(color='red'), fillcolor='rgba(255, 0, 0, 0.7)'),
                decreasing=dict(line=dict(color='blue'), fillcolor='rgba(0, 0, 255, 0.7)')
            ))
            
            # 이동평균선들
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MA20'],
                mode='lines',
                name='20일선',
                line=dict(color='red', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MA60'],
                mode='lines',
                name='60일선',
                line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MA125'],
                mode='lines',
                name='125일선',
                line=dict(color='orange', width=2)
            ))
            
            # 골든크로스 표시
            if analysis['golden_cross'] and analysis['cross_date']:
                cross_date = analysis['cross_date']
                cross_price = df.loc[cross_date, 'MA20']
                
                # 골든크로스 마커
                fig.add_trace(go.Scatter(
                    x=[cross_date],
                    y=[cross_price],
                    mode='markers',
                    marker=dict(color='red', size=15, symbol='star', line=dict(color='black', width=2)),
                    name='골든크로스',
                    text=[f'골든크로스<br>{cross_date.strftime("%Y-%m-%d")}'],
                    hovertemplate='%{text}<extra></extra>'
                ))
            
            # MA 조건 확인: 현재가가 20일선, 60일선 위에 있을 때만 표시
            if analysis['above_ma_lines']:
                current_price = df['Close'].iloc[-1]
                ma20 = df['MA20'].iloc[-1]
                ma60 = df['MA60'].iloc[-1]
                
                # 조건 재확인: 현재가 > 20일선, 60일선
                if current_price > ma20 and current_price > ma60:
                    recent_date = df.index[-1]
                    
                    # 텍스트 주석 추가
                    fig.add_annotation(
                        x=recent_date,
                        y=current_price * 1.03,
                        text="현재가 20,60일선 위",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="green",
                        font=dict(size=10, color="green")
                    )
            
            fig.update_layout(
                title=f"{company_name} ({symbol}) - 점수: {score}점 ({period_label})",
                xaxis_title="날짜",
                yaxis_title="가격",
                height=600,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(
                    gridcolor='lightgray',
                    rangeslider=dict(visible=False)
                ),
                yaxis=dict(
                    gridcolor='lightgray',
                    tickformat='.0f',
                    separatethousands=True,
                    tickmode='auto',
                    nticks=10,
                    autorange=True,
                    fixedrange=False,
                    automargin=True
                ),
                margin=dict(t=35, b=35, l=35, r=35),
                dragmode='zoom'
            )
            
            return fig
            
        except Exception as e:
            print(f"[ERROR] 차트 생성 중 오류: {str(e)}")
            return None

# Streamlit 앱 메인 함수
def main():
    st.set_page_config(
        page_title="📈 주식 기술적 분석 종목 추천 시스템",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📈 주식 기술적 분석 종목 추천 시스템 (미래 대장주 엄선 포함)")
    
    # 사이드바 설정
    st.sidebar.header("🔍 분석 설정")
    
    market = st.sidebar.selectbox(
        "시장/섹터 선택",
        options=['SP500', 'NASDAQ', 'ALL', 'KOSPI', 'KOSDAQ', 'FUTURE_LEADERS', 'AEROSPACE', 'QUANTUM', 'LONGEVITY', 'SYNTHETIC_BIO', 'STABLECOIN', 'DATACENTER_COOLING', 'BCI'],
        format_func=lambda x: {
            'SP500': 'S&P 500 (전체 500개)',
            'NASDAQ': 'NASDAQ (전체 주요 기술주)',
            'ALL': '미국 전체 (S&P500 + NASDAQ)',
            'KOSPI': 'KOSPI (50개)',
            'KOSDAQ': 'KOSDAQ (50개)',
            'FUTURE_LEADERS': '🌟 미래 대장주 엄선 (60개)',
            'AEROSPACE': '🚀 우주항공 섹터',
            'QUANTUM': '⚛️ 양자컴퓨터 섹터',
            'LONGEVITY': '🧬 노화역전/장수 섹터',
            'SYNTHETIC_BIO': '🔬 합성생물학 섹터',
            'STABLECOIN': '💰 스테이블코인/암호화폐 섹터',
            'DATACENTER_COOLING': '❄️ 데이터센터 냉각기술 섹터',
            'BCI': '🧠 뇌-컴퓨터 인터페이스(BCI) 섹터'
        }[x]
    )
    
    period = st.sidebar.selectbox(
        "📅 조회 기간 설정",
        options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
        index=2,  # 기본값: 6mo
        format_func=lambda x: {
            '1mo': '1개월',
            '3mo': '3개월',
            '6mo': '6개월',
            '1y': '1년',
            '2y': '2년',
            '5y': '5년'
        }[x]
    )
    
    # 분석 시작 버튼
    analyze_button = st.sidebar.button("🚀 분석 시작", type="primary")
    
    # 경고 메시지 표시
    if market in ['SP500', 'NASDAQ', 'ALL']:
        expected_count = {
            'SP500': '500개',
            'NASDAQ': '400개+',
            'ALL': '900개+'
        }
        st.sidebar.warning(f"⚠️ {market} 전체 분석 예상 시간: 5분 이내\n예상 종목 수: {expected_count[market]}")
    elif market in ['AEROSPACE', 'QUANTUM', 'LONGEVITY', 'SYNTHETIC_BIO', 'STABLECOIN', 'DATACENTER_COOLING', 'BCI', 'FUTURE_LEADERS']:
        sector_info = {
            'FUTURE_LEADERS': '🌟 미래 대장주 엄선 60개 기업 (각 섹터 최고 유망주)',
            'AEROSPACE': '우주항공 관련 33개 기업',
            'QUANTUM': '양자컴퓨터 관련 24개 기업', 
            'LONGEVITY': '노화역전/장수 관련 36개 기업',
            'SYNTHETIC_BIO': '합성생물학 관련 36개 기업',
            'STABLECOIN': '스테이블코인/암호화폐 관련 27개 기업',
            'DATACENTER_COOLING': '데이터센터 냉각기술 관련 31개 기업',
            'BCI': '뇌-컴퓨터 인터페이스 관련 35개 기업'
        }
        st.sidebar.info(f"ℹ️ {sector_info[market]}\n예상 분석 시간: 1분 이내")
    
    # StockAnalyzer 인스턴스 생성
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = StockAnalyzer()
    
    analyzer = st.session_state.analyzer
    
    # 분석 결과 저장용 session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    
    # 공포 탐욕 지수 (full width)
    st.subheader("😨 공포 탐욕 지수")
    
    if analyze_button or 'fear_greed_current' in st.session_state:
        try:
            if analyze_button:
                with st.spinner("공포 탐욕 지수 로딩 중..."):
                    fear_greed = analyzer.get_fear_greed_index(period)
                    st.session_state.fear_greed_current = fear_greed
                    st.session_state.fear_greed_label = analyzer.fear_greed_label
                    st.session_state.fear_greed_chart = analyzer.get_fear_greed_chart()
            
            # 현재 지수 표시
            fear_greed = st.session_state.get('fear_greed_current', 50.0)
            fear_greed_label = st.session_state.get('fear_greed_label', 'Neutral')
            
            # 감정 상태 및 색상 결정
            if fear_greed >= 75:
                color = 'red'
                emotion = '극도의 탐욕'
            elif fear_greed >= 55:
                color = 'orange'
                emotion = '탐욕'
            elif fear_greed >= 45:
                color = 'gray'
                emotion = '중립'
            elif fear_greed >= 25:
                color = 'blue'
                emotion = '공포'
            else:
                color = 'darkblue'
                emotion = '극도의 공포'
            
            # 지수와 차트를 나란히 배치
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # 지수 표시
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; border: 2px solid {color}; border-radius: 10px; margin: 10px 0;">
                    <h1 style="color: {color}; margin: 0;">{fear_greed:.1f}</h1>
                    <h3 style="color: {color}; margin: 0;">{emotion}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # 차트 표시
                if 'fear_greed_chart' in st.session_state:
                    st.plotly_chart(st.session_state.fear_greed_chart, use_container_width=True)
                    
        except Exception as e:
            st.error(f"공포 탐욕 지수 로딩 실패: {e}")
            st.markdown("""
            <div style="text-align: center; padding: 20px; border: 2px solid gray; border-radius: 10px; margin: 10px 0;">
                <h1 style="color: gray; margin: 0;">50.0</h1>
                <h3 style="color: gray; margin: 0;">중립 (오류)</h3>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("왼쪽에서 분석 설정을 선택하고 '분석 시작' 버튼을 클릭하세요.")
    
    # 분석 실행
    if analyze_button:
        # 진행률 표시용 컨테이너
        progress_container = st.container()
        
        with progress_container:
            st.subheader(f"🔄 {market} 분석 진행 중...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("분석을 시작합니다...")
                
                # 분석 실행
                results = analyzer.get_recommendations(market, period)
                
                progress_bar.progress(100)
                status_text.text(f"✅ 분석 완료! 총 {len(results)}개 종목 분석됨")
                
                st.session_state.analysis_results = results
                st.session_state.current_market = market
                st.session_state.current_period = period
                
                st.success(f"✅ {market} 분석 완료! 총 {len(results)}개 종목 중 상위 종목들을 확인하세요.")
                
            except Exception as e:
                st.error(f"❌ 분석 중 오류 발생: {str(e)}")
                st.session_state.analysis_results = []
            finally:
                # 진행률 표시 제거
                progress_container.empty()
    
    # 분석 결과 표시
    if st.session_state.analysis_results:
        st.subheader("🎯 분석 결과")
        
        # 통계 정보 표시
        total_stocks = len(st.session_state.analysis_results)
        high_score_stocks = len([r for r in st.session_state.analysis_results if r['score'] >= 75])
        medium_score_stocks = len([r for r in st.session_state.analysis_results if 50 <= r['score'] < 75])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 분석 종목", f"{total_stocks}개")
        with col2:
            st.metric("고득점 (75점+)", f"{high_score_stocks}개")
        with col3:
            st.metric("중간점수 (50-74점)", f"{medium_score_stocks}개")
        with col4:
            current_market = st.session_state.get('current_market', market)
            st.metric("분석 시장/섹터", current_market)
        
        # 점수별 필터링 옵션
        score_filter = st.selectbox(
            "점수별 필터링",
            options=['전체', '고득점 (75점+)', '중간이상 (50점+)', '골든크로스만', '추세안정만'],
            index=0
        )
        
        # 필터링 적용
        filtered_results = st.session_state.analysis_results.copy()
        
        if score_filter == '고득점 (75점+)':
            filtered_results = [r for r in filtered_results if r['score'] >= 75]
        elif score_filter == '중간이상 (50점+)':
            filtered_results = [r for r in filtered_results if r['score'] >= 50]
        elif score_filter == '골든크로스만':
            filtered_results = [r for r in filtered_results if r['golden_cross']]
        elif score_filter == '추세안정만':
            filtered_results = [r for r in filtered_results if r['trend_stable']]
        
        # 결과를 DataFrame으로 변환
        if filtered_results:
            results_data = []
            for i, result in enumerate(filtered_results):
                results_data.append({
                    'Index': i,
                    'Symbol': result['symbol'],
                    'Company': result['company_name'],
                    'Price': f"${result['current_price']:.2f}",
                    'GC': '✅' if result['golden_cross'] else '❌',
                    'MA': '✅' if result['above_ma_lines'] else '❌', 
                    '125': '✅' if result['ma125_support'] else '❌',
                    'Trend': '✅' if result['trend_stable'] else '❌',
                    'Score': result['score']
                })
            
            df_results = pd.DataFrame(results_data)
            
            st.write(f"📊 필터링된 결과: {len(filtered_results)}개 종목")
            
            # 데이터프레임 표시 (클릭 가능)
            selected_indices = st.dataframe(
                df_results[['Symbol', 'Company', 'Price', 'GC', 'MA', '125', 'Trend', 'Score']],
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # 선택된 종목의 차트 표시
            if selected_indices['selection']['rows']:
                selected_idx = selected_indices['selection']['rows'][0]
                selected_result = filtered_results[selected_idx]
                
                st.subheader(f"📊 {selected_result['company_name']} ({selected_result['symbol']}) 차트")
                
                # 차트 생성 및 표시
                with st.spinner("차트 생성 중..."):
                    chart = analyzer.create_stock_chart(selected_result)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                    else:
                        st.error("차트를 생성할 수 없습니다.")
                        
                # 분석 세부 정보 표시
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("골든크로스", "✅" if selected_result['golden_cross'] else "❌")
                with col2:
                    st.metric("이평선 위", "✅" if selected_result['above_ma_lines'] else "❌")
                with col3:
                    st.metric("125일선 지지", "✅" if selected_result['ma125_support'] else "❌")
                with col4:
                    st.metric("추세 안정", "✅" if selected_result['trend_stable'] else "❌")
                    
                # 종합 점수 표시
                score_color = "green" if selected_result['score'] >= 75 else "orange" if selected_result['score'] >= 50 else "red"
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; border: 2px solid {score_color}; border-radius: 10px; margin: 10px 0;">
                    <h2 style="color: {score_color}; margin: 0;">종합 점수: {selected_result['score']}점</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # 추가 정보 표시
                if selected_result['golden_cross'] and selected_result['cross_date']:
                    st.info(f"🌟 골든크로스 발생일: {selected_result['cross_date'].strftime('%Y-%m-%d')}")
                
                if selected_result['ma125_support']:
                    st.info(f"🛡️ 125일선 지지: 최근 {selected_result['support_count']}개 캔들이 125일선 위에서 지지")
        else:
            st.warning("필터링 조건에 해당하는 종목이 없습니다.")
    
    # 사이드바에 사용법 설명
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 사용법")
    st.sidebar.markdown("""
    1. **시장/섹터 선택**: 분석할 시장이나 섹터를 선택하세요
       - **전통 시장**: S&P 500, NASDAQ, KOSPI, KOSDAQ
       - **🌟 미래 대장주**: 각 섹터 최고 유망주만 엄선 (60개)
       - **미래 성장 섹터**: 
         - 🚀 우주항공 (SpaceX, Boeing, Lockheed 등)
         - ⚛️ 양자컴퓨터 (IBM, Google, IonQ 등) 
         - 🧬 노화역전/장수 (Unity Bio, CRISPR 등)
         - 🔬 합성생물학 (Twist Bio, Ginkgo 등)
         - 💰 스테이블코인/암호화폐 (Coinbase, MicroStrategy 등)
         - ❄️ 데이터센터 냉각 (Johnson Controls, Xylem 등)
         - 🧠 BCI/뇌컴퓨터 (Tesla, Meta, Neuralink 관련 등)
    2. **기간 설정**: 차트 조회 기간을 설정하세요  
    3. **분석 시작**: 버튼을 클릭하여 분석을 시작하세요
    4. **결과 확인**: 점수별 필터링 후 종목을 클릭하면 차트가 표시됩니다
    
    **점수 기준:**
    - 골든크로스: 25점
    - 이평선 위: 25점  
    - 125일선 지지: 25점
    - 추세 안정: 25점
    
    **⚠️ 주의사항:**
    - 전체 시장 분석은 시간이 오래 걸립니다
    - 섹터별 분석은 빠르게 완료됩니다 (1분 이내)
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ 섹터별 분석 정보")
    st.sidebar.markdown("""
    **🌟 미래 대장주 엄선 섹터:**
    - 각 미래 성장 섹터에서 가장 유망한 기업들만 선별
    - 🚀 우주항공: Rocket Lab, Virgin Galactic, Boeing, Lockheed
    - ⚛️ 양자컴퓨터: IonQ, Rigetti, IBM, Google, NVIDIA
    - 🧬 노화역전: Unity Bio, CRISPR, Editas, Beam Therapeutics
    - 🔬 합성생물학: Ginkgo Bioworks, Twist Bio, Amyris
    - 💰 암호화폐: Coinbase, MicroStrategy, Riot, Marathon
    - ❄️ 데이터센터: NVIDIA, AMD, Johnson Controls
    - 🧠 BCI: Tesla, Meta, NVIDIA, Intuitive Surgical
    - 🤖 AI/로봇: NVIDIA, Google, Microsoft, Palantir
    
    **미래 성장 섹터 특징:**
    - 🚀 **우주항공**: 우주여행, 위성통신, 항공우주
    - ⚛️ **양자컴퓨터**: 양자프로세서, 양자알고리즘
    - 🧬 **노화역전**: 유전자치료, 줄기세포, 수명연장
    - 🔬 **합성생물학**: DNA편집, 바이오제조
    - 💰 **스테이블코인**: 블록체인, 디지털자산
    - ❄️ **데이터센터 냉각**: AI칩 냉각, 에너지효율
    - 🧠 **BCI**: 뇌임플란트, 뉴럴인터페이스
    
    **투자 시 고려사항:**
    - 신기술 섹터는 변동성이 클 수 있습니다
    - 장기적 성장 관점에서 접근하세요
    - 포트폴리오 분산을 권장합니다
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ 분석 정보")
    st.sidebar.markdown("""
    - 실시간 데이터 기반 분석
    - 기술적 분석 지표 활용
    - 골든크로스 패턴 감지
    - 이동평균선 기반 추세 분석
    - 대용량 병렬 처리 최적화
    - 배치 단위 분석으로 안정성 확보
    """)
    
    # 하단 정보
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: gray; font-size: 12px;">
    📈 주식 기술적 분석 종목 추천 시스템 (미래 대장주 엄선 포함)<br>
    🌟 미래 대장주 엄선 특화 분석 | ⚠️ 투자 결정은 본인의 판단과 책임 하에 하시기 바랍니다.
    </div>
    """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()
