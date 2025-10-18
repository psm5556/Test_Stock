import streamlit as st
import plotly.graph_objs as go
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime
from fear_and_greed import get
import warnings
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

class StockAnalyzer:
    """주식 기술적 분석을 위한 클래스"""
    
    def __init__(self):
        self.fear_greed_current = None
        self.fear_greed_label = None
        self.fear_greed_history = None
        self.current_period = '6mo'
        
        self.period_labels = {
            '1mo': '1개월', '3mo': '3개월', '6mo': '6개월',
            '1y': '1년', '2y': '2년', '5y': '5년'
        }
        
        self.period_days = {
            '1mo': 30, '3mo': 90, '6mo': 180,
            '1y': 365, '2y': 730, '5y': 1825
        }
    
    def _get_sector_symbols(self, sector_type):
        """섹터별 주요 기업 심볼 가져오기"""
        sector_symbols = {
            'AEROSPACE': ['BA', 'LMT', 'RTX', 'NOC', 'GD', 'LHX', 'TDG', 'HWM', 'LDOS', 'KTOS',
                          'AVAV', 'RKLB', 'SPCE', 'ASTR', 'BLDE', 'JOBY', 'EVTL', 'LILM', 'ACHR',
                          'MAXR', 'SPIR', 'IRDM', 'VSAT', 'GSAT', 'ASTS', 'ORBC', 'GILT',
                          'CAT', 'HON', 'TXT', 'PH', 'ITT', 'CW', 'MOG-A'],
            'QUANTUM': ['IBM', 'GOOGL', 'MSFT', 'NVDA', 'INTC', 'AMD', 'QCOM', 'MRVL',
                        'IONQ', 'RGTI', 'QUBT', 'ARQQ', 'QTUM', 'DEFN', 'AMZN', 'CRM',
                        'ORCL', 'CSCO', 'TSM', 'ASML', 'KLAC', 'LRCX', 'AMAT', 'TXN'],
            'LONGEVITY': ['GILD', 'AMGN', 'REGN', 'VRTX', 'BIIB', 'MRNA', 'NVAX', 'BNTX', 'ILMN',
                          'TMO', 'DHR', 'A', 'DXCM', 'ISRG', 'VEEV', 'BSX', 'MDT', 'ABT',
                          'JNJ', 'PFE', 'ABBV', 'LLY', 'BMY', 'MRK', 'GSK', 'NVO', 'AZN',
                          'UNITY', 'SEER', 'TWST', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'VERV'],
            'SYNTHETIC_BIO': ['TWST', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'VERV', 'SEER', 'UNITY', 'FATE',
                              'BLUE', 'GILD', 'MRNA', 'BNTX', 'NVAX', 'DNA', 'SYN', 'AMRS',
                              'CODX', 'PACB', 'ILMN', 'TMO', 'DHR', 'A', 'LIFE', 'BIO', 'CDNA',
                              'FOLD', 'RGNX', 'SGEN', 'HALO', 'EVGN', 'CYTK', 'ABUS', 'IMUX'],
            'STABLECOIN': ['COIN', 'MSTR', 'RIOT', 'MARA', 'CLSK', 'BITF', 'HUT', 'CAN', 'BTBT',
                           'SQ', 'PYPL', 'MA', 'V', 'NVDA', 'AMD', 'TSLA', 'HOOD', 'SOFI',
                           'AFRM', 'UPST', 'LC', 'GBTC', 'ETHE', 'LTCN', 'BITO', 'ARKK'],
            'DATACENTER_COOLING': ['NVDA', 'AMD', 'INTC', 'QCOM', 'MRVL', 'AMAT', 'LRCX', 'KLAC',
                                   'JCI', 'CARR', 'ITW', 'EMR', 'HON', 'DHR', 'TMO', 'WAT', 'XYL',
                                   'VLTO', 'CGNX', 'TER', 'KEYS', 'NOVT', 'NDSN', 'HUBB',
                                   'AAON', 'SMTC', 'EVTC', 'DLR', 'EQIX', 'AMT'],
            'BCI': ['NVDA', 'GOOGL', 'MSFT', 'META', 'AAPL', 'TSLA', 'NEGG', 'SNAP', 'MRNA',
                    'ILMN', 'TMO', 'DHR', 'A', 'ISRG', 'VEEV', 'BSX', 'MDT', 'ABT',
                    'JNJ', 'DXCM', 'CTRL', 'NURO', 'SYNC', 'LFMD', 'AXGN', 'PRTS',
                    'GMED', 'KALA', 'INVA', 'PHVS', 'SENS', 'CRMD', 'KRYS', 'ATNF'],
            'FUTURE_LEADERS': ['RKLB', 'SPCE', 'BA', 'LMT', 'RTX', 'NOC', 'MAXR', 'ASTS',
                               'IONQ', 'RGTI', 'QUBT', 'IBM', 'GOOGL', 'NVDA', 'MSFT',
                               'UNITY', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'VERV', 'TWST', 'GILD', 'MRNA',
                               'DNA', 'TWST', 'AMRS', 'CRSP', 'EDIT', 'FATE', 'BLUE', 'SYN',
                               'COIN', 'MSTR', 'RIOT', 'MARA', 'CLSK', 'SQ', 'PYPL', 'HOOD',
                               'NVDA', 'AMD', 'JCI', 'CARR', 'XYL', 'SMTC', 'DLR', 'EQIX',
                               'NVDA', 'TSLA', 'META', 'GOOGL', 'ISRG', 'DXCM', 'BSX', 'SYNC',
                               'NVDA', 'AMD', 'GOOGL', 'MSFT', 'TSLA', 'META', 'PLTR', 'C3AI']
        }
        return sector_symbols.get(sector_type, [])
        
    def _get_sp500_symbols_full(self):
        """S&P 500 전체 기업 리스트 동적 가져오기"""
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        symbols = tables[0]['Symbol'].tolist()
        return symbols
    
    def _get_nasdaq_symbols_full(self):
        """NASDAQ-100 전체 주요 기업 리스트 동적 가져오기"""
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tables = pd.read_html(url)
        # NASDAQ-100 테이블은 보통 4번째 테이블 (인덱스 3)
        symbols = tables[3]['Ticker'].tolist()
        return symbols
    
    def _get_us_market_cap_from_yahoo(self, market_type='SP500', limit=None):
        if market_type == 'SP500':
            symbols = self._get_sp500_symbols_full()
        elif market_type == 'NASDAQ':
            symbols = self._get_nasdaq_symbols_full()
        elif market_type == 'ALL':
            sp500 = self._get_sp500_symbols_full()
            nasdaq = self._get_nasdaq_symbols_full()
            symbols = list(set(sp500 + nasdaq))
        elif market_type in ['AEROSPACE', 'QUANTUM', 'LONGEVITY', 'SYNTHETIC_BIO', 'STABLECOIN', 'DATACENTER_COOLING', 'BCI', 'FUTURE_LEADERS']:
            symbols = self._get_sector_symbols(market_type)
        else:
            symbols = self._get_sp500_symbols_full()
        
        if limit:
            symbols = symbols[:limit]
        return symbols

    def get_top_companies_by_market_cap(self, market='SP500', limit=None):
        companies = {}
        if market in ['SP500', 'NASDAQ', 'ALL', 'AEROSPACE', 'QUANTUM', 'LONGEVITY', 'SYNTHETIC_BIO', 'STABLECOIN', 'DATACENTER_COOLING', 'BCI', 'FUTURE_LEADERS']:
            us_symbols = self._get_us_market_cap_from_yahoo(market, limit)
            if us_symbols:
                company_names = self._get_us_company_names()
                sector_company_names = self._get_sector_company_names()
                company_names.update(sector_company_names)
                for symbol in us_symbols:
                    companies[symbol] = company_names.get(symbol, symbol)
        elif market in ['KOSPI', 'KOSDAQ']:
            korea_symbols = self._get_korea_market_cap_from_naver(market, limit or 1000)
            if korea_symbols:
                companies = self._get_korea_company_names_parallel(korea_symbols)
        return companies
    
    def _get_korea_market_cap_from_naver(self, market_type='KOSPI', limit=1000):
        all_codes = []
        page = 1
        if market_type == 'KOSPI':
            base_url = "https://finance.naver.com/sise/sise_market_sum.nhn"
        elif market_type == 'KOSDAQ':
            base_url = "https://finance.naver.com/sise/sise_market_sum.nhn?sosok=1"
        else:
            base_url = "https://finance.naver.com/sise/sise_market_sum.nhn"
        
        while len(all_codes) < limit and page <= 4:
            url = f"{base_url}?&page={page}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            pattern = r'/item/main\.naver\?code=(\d{6})'
            matches = re.findall(pattern, response.text)
            all_codes.extend(matches)
            all_codes = list(dict.fromkeys(all_codes))
            page += 1
        
        symbols = [f"{code}.KS" for code in all_codes[:limit]]
        return symbols
        
    def get_period_days(self, period):
        return self.period_days.get(period, 180)
    
    def _get_extended_period_for_ma(self, period):
        extended_periods = {
            '1mo': '1y', '3mo': '1y', '6mo': '2y',
            '1y': '3y', '2y': '5y', '5y': 'max'
        }
        return extended_periods.get(period, '2y')
        
    def get_fear_greed_index(self, period='6mo'):
        self.current_period = period
        fear_greed_data = get()
        self.fear_greed_current = fear_greed_data.value
        self.fear_greed_label = fear_greed_data.description
        self.fear_greed_history = self._get_real_fear_greed_history(period)
        return self.fear_greed_current
    
    def _get_real_fear_greed_history(self, period='6mo'):
        days = self.get_period_days(period)
        url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata?start=0&end={days}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if 'fear_and_greed_historical' in data:
            scores = data['fear_and_greed_historical']
            df = pd.DataFrame(scores['data'])
            df['x'] = pd.to_datetime(df['x'], unit='ms')
            df = df.rename(columns={'x': 'Date', 'y': 'Value'})
            df = df[['Date', 'Value']]
            return df
        return None
    
    def get_fear_greed_chart(self):
        period = getattr(self, 'current_period', '6mo')
        if self.fear_greed_history is None:
            return go.Figure()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.fear_greed_history['Date'], y=self.fear_greed_history['Value'],
                                 mode='lines', name='Fear & Greed Index', line=dict(color='purple', width=2), fill='tonexty'))
        fig.add_hline(y=75, line=dict(color="red", width=1, dash="dash"), annotation_text="극도의 탐욕")
        fig.add_hline(y=55, line=dict(color="orange", width=1, dash="dash"), annotation_text="탐욕")
        fig.add_hline(y=45, line=dict(color="gray", width=1, dash="dash"), annotation_text="중립")
        fig.add_hline(y=25, line=dict(color="blue", width=1, dash="dash"), annotation_text="공포")
        
        if self.fear_greed_current and not self.fear_greed_history.empty:
            fig.add_trace(go.Scatter(x=[self.fear_greed_history['Date'].iloc[-1]], y=[self.fear_greed_current],
                                     mode='markers', marker=dict(color='red', size=10),
                                     name=f'현재: {self.fear_greed_current:.1f}'))
        
        period_label = self.period_labels.get(period, period)
        fig.update_layout(title=f"공포 & 탐욕 지수 ({period_label})", xaxis_title="날짜", yaxis_title="지수",
                          height=300, showlegend=True, xaxis=dict(gridcolor='lightgray'),
                          yaxis=dict(range=[0, 100], gridcolor='lightgray'), margin=dict(t=40, b=40, l=50, r=50))
        return fig
    
    def calculate_moving_averages(self, df):
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['MA125'] = df['Close'].rolling(window=125).mean()
        return df
    
    def check_golden_cross(self, df):
        if len(df) < 10:
            return False, None
        recent_data = df.tail(10)
        for i in range(1, len(recent_data)):
            current_20 = recent_data['MA20'].iloc[i]
            current_60 = recent_data['MA60'].iloc[i]
            current_125 = recent_data['MA125'].iloc[i]
            prev_20 = recent_data['MA20'].iloc[i-1]
            prev_60 = recent_data['MA60'].iloc[i-1]
            golden_cross = ((prev_20 <= prev_60) and (current_20 > current_60) and
                            (current_20 < current_125) and (current_60 < current_125))
            if golden_cross:
                return True, recent_data.index[i]
        return False, None
    
    def check_above_ma_lines(self, df):
        if len(df) < 1:
            return False
        current_price = df['Close'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]
        ma60 = df['MA60'].iloc[-1]
        return current_price > ma20 and current_price > ma60
    
    def check_ma125_support(self, df):
        if len(df) < 2:
            return False, 0
        recent_candles = df.tail(5)
        support_count = 0
        for i in range(len(recent_candles)):
            candle_open = recent_candles['Open'].iloc[i]
            candle_close = recent_candles['Close'].iloc[i]
            ma125 = recent_candles['MA125'].iloc[i]
            candle_body_low = min(candle_open, candle_close)
            if candle_body_low > ma125:
                support_count += 1
        return support_count >= 2, support_count
    
    def check_trend_stability(self, df):
        if len(df) < 10:
            return False
        recent_ma20 = df['MA20'].tail(10)
        recent_ma60 = df['MA60'].tail(10)
        ma20_slope = (recent_ma20.iloc[-1] - recent_ma20.iloc[0]) / 10
        ma60_slope = (recent_ma60.iloc[-1] - recent_ma60.iloc[0]) / 10
        return ma20_slope > 0 and ma60_slope > 0 and recent_ma20.iloc[-1] > recent_ma60.iloc[-1]
    
    def analyze_stock(self, symbol, period='6mo', symbols_dict=None):
        stock = yf.Ticker(symbol)
        extended_period = self._get_extended_period_for_ma(period)
        df_full = stock.history(period=extended_period)
        if df_full.empty:
            return None
        df_full = self.calculate_moving_averages(df_full)
        days_to_show = self.get_period_days(period)
        df_display = df_full.tail(days_to_show).copy() if len(df_full) > days_to_show else df_full.copy()
        company_name = self.get_company_name(symbol, symbols_dict)
        golden_cross, cross_date = self.check_golden_cross(df_display)
        above_ma_lines = self.check_above_ma_lines(df_display)
        ma125_support, support_count = self.check_ma125_support(df_display)
        trend_stable = self.check_trend_stability(df_display)
        current_price = df_display['Close'].iloc[-1]
        score = sum([25 for cond in [golden_cross, above_ma_lines, ma125_support, trend_stable] if cond])
        period_label = self.period_labels.get(period, period)
        return {
            'symbol': symbol, 'company_name': company_name, 'current_price': current_price,
            'golden_cross': golden_cross, 'cross_date': cross_date, 'above_ma_lines': above_ma_lines,
            'ma125_support': ma125_support, 'support_count': support_count, 'trend_stable': trend_stable,
            'score': score, 'data': df_display, 'period': period, 'period_label': period_label,
            'data_days': len(df_display)
        }
    
    def get_company_name(self, symbol, symbols_dict=None):
        if symbols_dict and symbol in symbols_dict:
            return symbols_dict[symbol]
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('longName', info.get('shortName', symbol))
        except:
            return symbol
    
    def get_recommendations(self, market='ALL', period='6mo'):
        self.current_period = period
        symbols = self.get_top_companies_by_market_cap(market, limit=None)
        results = self._analyze_stocks_parallel(symbols, period)
        results = [r for r in results if r]  # None 제거
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def _analyze_stocks_parallel(self, symbols, period):
        results = []
        def analyze_single_stock(symbol):
            return self.analyze_stock(symbol, period, symbols)
        
        batch_size = 20
        symbol_list = list(symbols.keys())
        for i in range(0, len(symbol_list), batch_size):
            batch_symbols = symbol_list[i:i+batch_size]
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_symbol = {executor.submit(analyze_single_stock, symbol): symbol for symbol in batch_symbols}
                for future in as_completed(future_to_symbol):
                    try:
                        analysis = future.result()
                        if analysis:
                            results.append(analysis)
                    except:
                        pass
        return results

    def _get_us_company_names(self):
        return {
            'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp.', 'GOOGL': 'Alphabet Inc. Class A',
            # ... (전체 매핑 유지, 필요 시 업데이트)
            'C3AI': 'C3.ai Inc.', 'PLTR': 'Palantir Technologies Inc.'  # 마지막
        }  # 전체 매핑을 채워넣으세요.

    def _get_sector_company_names(self):
        return {
            'LMT': 'Lockheed Martin Corp.', 'HWM': 'Howmet Aerospace Inc.',
            # ... (전체 매핑 유지)
            'C3AI': 'C3.ai Inc.', 'PLTR': 'Palantir Technologies Inc.'
        }

    def _get_korea_company_names_parallel(self, symbols):
        companies = {}
        def get_company_name(symbol):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return symbol, info.get('longName', info.get('shortName', symbol))
            except:
                return symbol, symbol
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_symbol = {executor.submit(get_company_name, symbol): symbol for symbol in symbols}
            for future in as_completed(future_to_symbol):
                symbol, company_name = future.result()
                companies[symbol] = company_name
        return companies

    def create_stock_chart(self, analysis):
        df = analysis['data']
        symbol = analysis['symbol']
        company_name = analysis['company_name']
        score = analysis['score']
        period_label = analysis['period_label']
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                     name='주가', increasing=dict(line=dict(color='red'), fillcolor='rgba(255, 0, 0, 0.7)'),
                                     decreasing=dict(line=dict(color='blue'), fillcolor='rgba(0, 0, 255, 0.7)')))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='20일선', line=dict(color='red', width=2)))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], mode='lines', name='60일선', line=dict(color='blue', width=2)))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA125'], mode='lines', name='125일선', line=dict(color='orange', width=2)))
        if analysis['golden_cross'] and analysis['cross_date']:
            cross_date = analysis['cross_date']
            cross_price = df.loc[cross_date, 'MA20']
            fig.add_trace(go.Scatter(x=[cross_date], y=[cross_price], mode='markers',
                                     marker=dict(color='red', size=15, symbol='star', line=dict(color='black', width=2)),
                                     name='골든크로스', text=[f'골든크로스<br>{cross_date.strftime("%Y-%m-%d")}']))
        if analysis['above_ma_lines']:
            current_price = df['Close'].iloc[-1]
            ma20 = df['MA20'].iloc[-1]
            ma60 = df['MA60'].iloc[-1]
            if current_price > ma20 and current_price > ma60:
                recent_date = df.index[-1]
                fig.add_annotation(x=recent_date, y=current_price * 1.03, text="현재가 20,60일선 위",
                                   showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="green",
                                   font=dict(size=10, color="green"))
        fig.update_layout(title=f"{company_name} ({symbol}) - 점수: {score}점 ({period_label})",
                          xaxis_title="날짜", yaxis_title="가격", height=600, showlegend=True,
                          plot_bgcolor='white', paper_bgcolor='white',
                          xaxis=dict(gridcolor='lightgray', rangeslider=dict(visible=False)),
                          yaxis=dict(gridcolor='lightgray', tickformat='.0f', separatethousands=True, tickmode='auto', nticks=10,
                                     autorange=True, fixedrange=False, automargin=True),
                          margin=dict(t=35, b=35, l=35, r=35), dragmode='zoom')
        return fig

# Streamlit 앱 메인 함수
def main():
    st.set_page_config(page_title="📈 주식 기술적 분석 종목 추천 시스템", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
    st.title("📈 주식 기술적 분석 종목 추천 시스템 (미래 대장주 엄선 포함)")
    
    st.sidebar.header("🔍 분석 설정")
    market = st.sidebar.selectbox("시장/섹터 선택", options=['SP500', 'NASDAQ', 'ALL', 'KOSPI', 'KOSDAQ', 'FUTURE_LEADERS', 'AEROSPACE', 'QUANTUM', 'LONGEVITY', 'SYNTHETIC_BIO', 'STABLECOIN', 'DATACENTER_COOLING', 'BCI'],
                                  format_func=lambda x: {'SP500': 'S&P 500', 'NASDAQ': 'NASDAQ', 'ALL': '미국 전체', 'KOSPI': 'KOSPI', 'KOSDAQ': 'KOSDAQ',
                                                          'FUTURE_LEADERS': '🌟 미래 대장주', 'AEROSPACE': '🚀 우주항공', 'QUANTUM': '⚛️ 양자컴퓨터',
                                                          'LONGEVITY': '🧬 노화역전', 'SYNTHETIC_BIO': '🔬 합성생물학', 'STABLECOIN': '💰 스테이블코인',
                                                          'DATACENTER_COOLING': '❄️ 데이터센터 냉각', 'BCI': '🧠 BCI'}[x])
    period = st.sidebar.selectbox("📅 조회 기간 설정", options=['1mo', '3mo', '6mo', '1y', '2y', '5y'], index=2,
                                  format_func=lambda x: {'1mo': '1개월', '3mo': '3개월', '6mo': '6개월',
                                                         '1y': '1년', '2y': '2년', '5y': '5년'}[x])
    analyze_button = st.sidebar.button("🚀 분석 시작", type="primary")
    
    if market in ['SP500', 'NASDAQ', 'ALL']:
        st.sidebar.warning(f"⚠️ {market} 전체 분석 예상 시간: 5분 이내")
    
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = StockAnalyzer()
    analyzer = st.session_state.analyzer
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    
    st.subheader("😨 공포 탐욕 지수")
    if analyze_button or 'fear_greed_current' in st.session_state:
        if analyze_button:
            with st.spinner("공포 탐욕 지수 로딩 중..."):
                fear_greed = analyzer.get_fear_greed_index(period)
                st.session_state.fear_greed_current = fear_greed
                st.session_state.fear_greed_label = analyzer.fear_greed_label
                st.session_state.fear_greed_chart = analyzer.get_fear_greed_chart()
        fear_greed = st.session_state.get('fear_greed_current', 50.0)
        fear_greed_label = st.session_state.get('fear_greed_label', 'Neutral')
        if fear_greed >= 75:
            color, emotion = 'red', '극도의 탐욕'
        elif fear_greed >= 55:
            color, emotion = 'orange', '탐욕'
        elif fear_greed >= 45:
            color, emotion = 'gray', '중립'
        elif fear_greed >= 25:
            color, emotion = 'blue', '공포'
        else:
            color, emotion = 'darkblue', '극도의 공포'
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f'<div style="text-align: center; padding: 20px; border: 2px solid {color}; border-radius: 10px; margin: 10px 0;">'
                        f'<h1 style="color: {color}; margin: 0;">{fear_greed:.1f}</h1>'
                        f'<h3 style="color: {color}; margin: 0;">{emotion}</h3></div>', unsafe_allow_html=True)
        with col2:
            if 'fear_greed_chart' in st.session_state:
                st.plotly_chart(st.session_state.fear_greed_chart, use_container_width=True)
    else:
        st.info("분석 시작 버튼을 클릭하세요.")
    
    if analyze_button:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("분석 시작...")
        results = analyzer.get_recommendations(market, period)
        progress_bar.progress(100)
        status_text.text(f"✅ 분석 완료! {len(results)}개 종목")
        st.session_state.analysis_results = results
        st.session_state.current_market = market
        st.session_state.current_period = period
        st.success(f"✅ 분석 완료! {len(results)}개 종목")
    
    if st.session_state.analysis_results:
        st.subheader("🎯 분석 결과")
        total_stocks = len(st.session_state.analysis_results)
        high_score_stocks = len([r for r in st.session_state.analysis_results if r['score'] >= 75])
        medium_score_stocks = len([r for r in st.session_state.analysis_results if 50 <= r['score'] < 75])
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 분석 종목", f"{total_stocks}개")
        col2.metric("고득점 (75점+)", f"{high_score_stocks}개")
        col3.metric("중간점수 (50-74점)", f"{medium_score_stocks}개")
        col4.metric("분석 시장/섹터", st.session_state.get('current_market', market))
        
        score_filter = st.selectbox("점수별 필터링", options=['전체', '고득점 (75점+)', '중간이상 (50점+)', '골든크로스만', '추세안정만'])
        filtered_results = st.session_state.analysis_results.copy()
        if score_filter == '고득점 (75점+)':
            filtered_results = [r for r in filtered_results if r['score'] >= 75]
        elif score_filter == '중간이상 (50점+)':
            filtered_results = [r for r in filtered_results if r['score'] >= 50]
        elif score_filter == '골든크로스만':
            filtered_results = [r for r in filtered_results if r['golden_cross']]
        elif score_filter == '추세안정만':
            filtered_results = [r for r in filtered_results if r['trend_stable']]
        
        if filtered_results:
            results_data = []
            for i, result in enumerate(filtered_results):
                results_data.append({
                    'Index': i, 'Symbol': result['symbol'], 'Company': result['company_name'],
                    'Price': f"${result['current_price']:.2f}", 'GC': '✅' if result['golden_cross'] else '❌',
                    'MA': '✅' if result['above_ma_lines'] else '❌', '125': '✅' if result['ma125_support'] else '❌',
                    'Trend': '✅' if result['trend_stable'] else '❌', 'Score': result['score']
                })
            df_results = pd.DataFrame(results_data)
            st.write(f"📊 필터링된 결과: {len(filtered_results)}개 종목")
            selected_indices = st.dataframe(df_results[['Symbol', 'Company', 'Price', 'GC', 'MA', '125', 'Trend', 'Score']],
                                            use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if selected_indices['selection']['rows']:
                selected_idx = selected_indices['selection']['rows'][0]
                selected_result = filtered_results[selected_idx]
                st.subheader(f"📊 {selected_result['company_name']} ({selected_result['symbol']}) 차트")
                with st.spinner("차트 생성 중..."):
                    chart = analyzer.create_stock_chart(selected_result)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("골든크로스", "✅" if selected_result['golden_cross'] else "❌")
                col2.metric("이평선 위", "✅" if selected_result['above_ma_lines'] else "❌")
                col3.metric("125일선 지지", "✅" if selected_result['ma125_support'] else "❌")
                col4.metric("추세 안정", "✅" if selected_result['trend_stable'] else "❌")
                score_color = "green" if selected_result['score'] >= 75 else "orange" if selected_result['score'] >= 50 else "red"
                st.markdown(f'<div style="text-align: center; padding: 15px; border: 2px solid {score_color}; border-radius: 10px; margin: 10px 0;">'
                            f'<h2 style="color: {score_color}; margin: 0;">종합 점수: {selected_result["score"]}점</h2></div>', unsafe_allow_html=True)
                if selected_result['golden_cross'] and selected_result['cross_date']:
                    st.info(f"🌟 골든크로스 발생일: {selected_result['cross_date'].strftime('%Y-%m-%d')}")
                if selected_result['ma125_support']:
                    st.info(f"🛡️ 125일선 지지: 최근 {selected_result['support_count']}개 캔들 지지")
        else:
            st.warning("필터링 조건에 해당하는 종목 없음.")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 사용법")
    st.sidebar.markdown("""
    1. 시장/섹터 선택
    2. 기간 설정
    3. 분석 시작 클릭
    4. 결과 확인 (종목 클릭 시 차트 표시)
    **점수 기준:** 각 조건 25점 (총 100점)
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ 분석 정보")
    st.sidebar.markdown("""
    - 실시간 데이터 기반
    - 기술적 분석 지표 활용
    - 대용량 병렬 처리
    """)
    
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: gray; font-size: 12px;">📈 주식 분석 시스템 | ⚠️ 투자 책임은 본인</div>', unsafe_allow_html=True)

if __name__ == '__main__':
    main()
