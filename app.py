import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
from fear_and_greed import get
import requests
from bs4 import BeautifulSoup
import time
import threading
from waitress import serve

# 앱 생성
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

# 글로벌 변수
analysis_data = {}
analysis_running = False

# 티커 심볼과 함께 회사명을 표시하기 위한 딕셔너리 생성 함수
def get_company_names(tickers):
    company_names = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            company_names[ticker] = info.get('longName', ticker)
        except:
            company_names[ticker] = ticker
    return company_names

# 상위 50개 기업 가져오기 함수
def get_top_stocks():
    # 코스피 상위 50개 (한국 주식은 .KS 접미사 사용)
    try:
        url = 'https://finance.naver.com/sise/sise_market_sum.nhn'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        kospi_tickers = []
        rows = soup.select('table.type_2 tbody tr')
        
        for row in rows:
            if len(kospi_tickers) >= 50:
                break
                
            cols = row.select('td')
            if len(cols) > 1:
                try:
                    ticker_cell = cols[1].select_one('a')
                    if ticker_cell:
                        code = ticker_cell.get('href').split('=')[-1]
                        ticker = f"{code}.KS"  # 야후 파이낸스 형식으로 변환
                        kospi_tickers.append(ticker)
                except:
                    continue
    except:
        # 실패 시 기본 상위 종목 사용
        kospi_tickers = ['005930.KS', '000660.KS', '035420.KS', '005380.KS', '051910.KS']
        # 상위 50개까지 채우기
        kospi_tickers = kospi_tickers + [f"00000{i}.KS" for i in range(len(kospi_tickers), 50)]

    # KOSDAQ 상위 50개 추가
    try:
        kosdaq_url = 'https://finance.naver.com/sise/sise_market_sum.nhn?sosok=1'
        kosdaq_response = requests.get(kosdaq_url)
        kosdaq_soup = BeautifulSoup(kosdaq_response.text, 'html.parser')
        
        kosdaq_tickers = []
        kosdaq_rows = kosdaq_soup.select('table.type_2 tbody tr')
        
        for row in kosdaq_rows:
            if len(kosdaq_tickers) >= 50:
                break
                
            cols = row.select('td')
            if len(cols) > 1:
                try:
                    ticker_cell = cols[1].select_one('a')
                    if ticker_cell:
                        code = ticker_cell.get('href').split('=')[-1]
                        ticker = f"{code}.KQ"  # KOSDAQ은 .KQ 접미사 사용
                        kosdaq_tickers.append(ticker)
                except:
                    continue
    except:
        # 실패 시 기본 KOSDAQ 상위 종목 사용
        kosdaq_tickers = ['091990.KQ', '035720.KQ', '068270.KQ', '058470.KQ', '263750.KQ']
        # 상위 50개까지 채우기
        kosdaq_tickers = kosdaq_tickers + [f"00000{i}.KQ" for i in range(len(kosdaq_tickers), 50)]
    
    # S&P500 상위 50개
    try:
        sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        sp500_res = requests.get(sp500_url)
        sp500_soup = BeautifulSoup(sp500_res.text, 'html.parser')
        
        table = sp500_soup.find('table', {'class': 'wikitable sortable'})
        sp500_tickers = []
        
        for row in table.find_all('tr')[1:51]:  # 첫 번째 행은 헤더이므로 제외, 상위 50개만
            ticker = row.find_all('td')[0].text.strip()
            sp500_tickers.append(ticker)
    except:
        # 실패 시 기본 상위 종목 사용
        sp500_tickers = ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL']
        # 상위 50개까지 채우기
        sp500_tickers = sp500_tickers + [f"SP{i}" for i in range(len(sp500_tickers), 50)]
    
    # 나스닥 상위 50개
    try:
        nasdaq_url = 'https://www.nasdaq.com/market-activity/stocks/screener'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        nasdaq_res = requests.get(nasdaq_url, headers=headers)
        nasdaq_soup = BeautifulSoup(nasdaq_res.text, 'html.parser')
        
        # 나스닥 웹사이트 구조에 따라 수정 필요할 수 있음
        nasdaq_tickers = []
        
        # 실제 구현은 웹사이트 구조에 따라 다를 수 있습니다.
        # 여기서는 API 제한으로 인해 대표적인 나스닥 종목을 하드코딩합니다.
        nasdaq_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'PYPL', 'INTC', 'CMCSA',
                         'NFLX', 'ADBE', 'CSCO', 'PEP', 'AVGO', 'TXN', 'COST', 'QCOM', 'TMUS', 'AMGN',
                         'SBUX', 'CHTR', 'INTU', 'ISRG', 'MDLZ', 'GILD', 'BKNG', 'AMAT', 'AMD', 'MU',
                         'LRCX', 'ADSK', 'CSX', 'BIIB', 'ADP', 'ILMN', 'ATVI', 'JD', 'MNST', 'MELI',
                         'KHC', 'EBAY', 'CTSH', 'EXC', 'NXPI', 'VRTX', 'REGN', 'FISV', 'MRNA', 'KLAC']
    except:
        # 실패 시 기본 상위 종목 사용
        nasdaq_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA']
        # 상위 50개까지 채우기
        nasdaq_tickers = nasdaq_tickers + [f"NAS{i}" for i in range(len(nasdaq_tickers), 50)]
    
    return kospi_tickers, sp500_tickers, nasdaq_tickers, kosdaq_tickers

# 분석 함수
def analyze_stock(ticker, company_name, period='1y'):
    try:
        # 기간에 따른 시작 날짜 계산
        end_date = datetime.now()
        
        if period == '1mo':
            start_date = end_date - timedelta(days=30)
        elif period == '3mo':
            start_date = end_date - timedelta(days=90)
        elif period == '6mo':
            start_date = end_date - timedelta(days=180)
        elif period == '1y':
            start_date = end_date - timedelta(days=365)
        elif period == '2y':
            start_date = end_date - timedelta(days=730)
        elif period == '5y':
            start_date = end_date - timedelta(days=1825)
        else:  # max
            start_date = end_date - timedelta(days=365*10)  # 10년
        
        # 주식 데이터 가져오기
        stock_data = yf.download(ticker, start=start_date, end=end_date)
        
        if len(stock_data) < 125:
            return {
                "ticker": ticker,
                "company_name": company_name,
                "score": 0,
                "price": None,
                "golden_cross": False,
                "above_ma_lines": False,
                "above_125_ma": False,
                "steady_above_125": False,
                "chart_data": None,
                "error": "데이터 부족",
                "period": period
            }
        
        # 이동평균선 계산
        stock_data['MA20'] = stock_data['Close'].rolling(window=20).mean()
        stock_data['MA60'] = stock_data['Close'].rolling(window=60).mean()
        stock_data['MA125'] = stock_data['Close'].rolling(window=125).mean()
        
        # 최근 데이터 (최소 125일 이상의 데이터가 필요)
        recent_data = stock_data.iloc[-30:]
        
        # 골든크로스 확인 (20일선이 60일선을 상향 돌파)
        golden_cross = False
        for i in range(1, len(recent_data)):
            if (recent_data['MA20'].iloc[i-1] <= recent_data['MA60'].iloc[i-1] and 
                recent_data['MA20'].iloc[i] > recent_data['MA60'].iloc[i]):
                golden_cross = True
                break
        
        # 현재 주가가 20일선과 60일선 위에 있는지 확인
        last_price = stock_data['Close'].iloc[-1]
        above_ma_lines = last_price > stock_data['MA20'].iloc[-1] and last_price > stock_data['MA60'].iloc[-1]
        
        # 현재 주가가 125일선 위에 있는지 확인
        above_125_ma = last_price > stock_data['MA125'].iloc[-1]
        
        # 최근 2개 이상의 캔들이 125일선 위에서 지지하는지 확인 (몸통 기준)
        steady_above_125 = False
        if len(stock_data) > 2:
            last_2_days = stock_data.iloc[-2:].copy()
            # 캔들의 몸통(open과 close 중 낮은 값)이 125일선 위에 있는지 확인
            last_2_days['candle_body_low'] = last_2_days[['Open', 'Close']].min(axis=1)
            if all(last_2_days['candle_body_low'] > last_2_days['MA125']):
                steady_above_125 = True
        
        # 점수 계산 (각 조건당 25점)
        score = 0
        if golden_cross:
            score += 25
        if above_ma_lines:
            score += 25
        if above_125_ma:
            score += 25
        if steady_above_125:
            score += 25
        
        # 차트 데이터 준비
        chart_data = {
            'dates': stock_data.index,
            'open': stock_data['Open'],
            'high': stock_data['High'],
            'low': stock_data['Low'],
            'close': stock_data['Close'],
            'ma20': stock_data['MA20'],
            'ma60': stock_data['MA60'],
            'ma125': stock_data['MA125'],
            'golden_cross_index': None,
            'period': period
        }
        
        # 골든크로스 발생 지점 표시
        if golden_cross:
            for i in range(1, len(stock_data)):
                if (stock_data['MA20'].iloc[i-1] <= stock_data['MA60'].iloc[i-1] and 
                    stock_data['MA20'].iloc[i] > stock_data['MA60'].iloc[i]):
                    chart_data['golden_cross_index'] = i
                    break
        
        return {
            "ticker": ticker,
            "company_name": company_name,
            "score": score,
            "price": round(float(last_price), 2),
            "golden_cross": golden_cross,
            "above_ma_lines": above_ma_lines,
            "above_125_ma": above_125_ma,
            "steady_above_125": steady_above_125,
            "chart_data": chart_data,
            "error": None,
            "period": period
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "company_name": company_name,
            "score": 0,
            "price": None,
            "golden_cross": False,
            "above_ma_lines": False,
            "above_125_ma": False,
            "steady_above_125": False,
            "chart_data": None,
            "error": str(e),
            "period": period
        }

# 백그라운드에서 분석 실행
def run_analysis_background(index_type, period='1y'):
    global analysis_data, analysis_running
    
    try:
        analysis_running = True
        
        # 상위 50개 기업 가져오기
        kospi_tickers, sp500_tickers, nasdaq_tickers, kosdaq_tickers = get_top_stocks()
        
        if index_type == 'kospi':
            tickers = kospi_tickers
        elif index_type == 'sp500':
            tickers = sp500_tickers
        elif index_type == 'nasdaq':
            tickers = nasdaq_tickers
        else: # kosdaq
            tickers = kosdaq_tickers
            
        # 회사명 가져오기
        company_names = get_company_names(tickers)
        
        # 공포 & 탐욕 지수 가져오기
        try:
            fear_greed_data = get()
            fear_greed_value = fear_greed_data.value
            fear_greed_label = fear_greed_data.description
        except:
            fear_greed_value = 50
            fear_greed_label = "Neutral"
        
        # 각 종목 분석
        results = []
        for ticker in tickers:
            company_name = company_names.get(ticker, ticker)
            result = analyze_stock(ticker, company_name, period)
            if result['error'] is None:  # 에러가 없는 결과만 포함
                results.append(result)
        
        # 점수순으로 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 결과 저장
        analysis_data = {
            'results': results,
            'fear_greed_value': fear_greed_value,
            'fear_greed_label': fear_greed_label,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period': period
        }
        
    except Exception as e:
        analysis_data = {
            'results': [],
            'fear_greed_value': 50,
            'fear_greed_label': "Error",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error': str(e),
            'period': period
        }
    finally:
        analysis_running = False

# 앱 레이아웃
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("📈 주식 기술적 분석 시스템", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔍 분석 설정"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("📊 지수 선택:", className="form-label"),
                            dcc.Dropdown(
                                id="index-selection",
                                options=[
                                    {"label": "코스피 (KOSPI)", "value": "kospi"},
                                    {"label": "S&P 500", "value": "sp500"},
                                    {"label": "나스닥 (NASDAQ)", "value": "nasdaq"},
                                    {"label": "코스닥 (KOSDAQ)", "value": "kosdaq"}
                                ],
                                value="kospi",
                                className="mb-3"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("📅 분석 기간:", className="form-label"),
                            dcc.Dropdown(
                                id="period-selection",
                                options=[
                                    {"label": "1개월", "value": "1mo"},
                                    {"label": "3개월", "value": "3mo"},
                                    {"label": "6개월", "value": "6mo"},
                                    {"label": "1년", "value": "1y"},
                                    {"label": "2년", "value": "2y"},
                                    {"label": "5년", "value": "5y"},
                                    {"label": "최대", "value": "max"}
                                ],
                                value="1y",
                                className="mb-3"
                            )
                        ], width=6)
                    ]),
                    dbc.Button(
                        "분석 시작",
                        id="analyze-button",
                        color="primary",
                        size="lg",
                        className="w-100"
                    ),
                    html.Div(id="loading-status", className="text-center mt-3")
                ])
            ])
        ], width=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("😨 공포 & 탐욕 지수"),
                dbc.CardBody([
                    html.Div(id="fear-greed-display", className="text-center"),
                    html.Div(id="fear-greed-label", className="text-center"),
                    html.Div(id="analysis-timestamp", className="text-center text-muted mt-2")
                ])
            ])
        ], width=8)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div(id="analysis-results")
        ])
    ]),
    
    # 주기적 업데이트를 위한 인터벌 컴포넌트
    dcc.Interval(
        id='interval-component',
        interval=2*1000,  # 2초마다 업데이트
        n_intervals=0
    )
], fluid=True)

# 콜백 함수들
@app.callback(
    [Output("loading-status", "children"),
     Output("analyze-button", "disabled")],
    [Input("analyze-button", "n_clicks"),
     Input("interval-component", "n_intervals")],
    [State("index-selection", "value"),
     State("period-selection", "value")],
    prevent_initial_call=True
)
def handle_analysis_status(n_clicks, n_intervals, index_type, period):
    if n_clicks and not analysis_running:
        # 백그라운드에서 분석 시작
        thread = threading.Thread(target=run_analysis_background, args=(index_type, period))
        thread.daemon = True
        thread.start()
        return "🔄 분석 중... 잠시만 기다려주세요", True
    
    if analysis_running:
        return "🔄 분석 중... 잠시만 기다려주세요", True
    
    return "", False

@app.callback(
    [Output("fear-greed-display", "children"),
     Output("fear-greed-label", "children"),
     Output("analysis-timestamp", "children"),
     Output("analysis-results", "children")],
    [Input("interval-component", "n_intervals"),
     Input("analyze-button", "n_clicks")],
    [State("index-selection", "value"),
     State("period-selection", "value")],
    prevent_initial_call=True
)
def update_analysis_results(n_intervals, n_clicks, index_type, period):
    if not analysis_data:
        return "분석 버튼을 클릭하세요", "", "", ""
    
    # 공포 & 탐욕 지수 표시
    fear_greed_value = analysis_data.get('fear_greed_value', 50)
    fear_greed_label = analysis_data.get('fear_greed_label', 'Neutral')
    timestamp = analysis_data.get('timestamp', '')
    period_used = analysis_data.get('period', period)
    
    # 색상 결정
    if fear_greed_value >= 75:
        color = "danger"
        emotion = "극도의 탐욕"
    elif fear_greed_value >= 55:
        color = "warning"
        emotion = "탐욕"
    elif fear_greed_value >= 45:
        color = "secondary"
        emotion = "중립"
    elif fear_greed_value >= 25:
        color = "info"
        emotion = "공포"
    else:
        color = "dark"
        emotion = "극도의 공포"
    
    fear_greed_display = dbc.Alert([
        html.H2(f"{fear_greed_value}", className="mb-0"),
        html.P(f"{emotion} ({fear_greed_label})", className="mb-0"),
        html.Small(f"분석 기간: {period_used}", className="text-muted")
    ], color=color, className="text-center")
    
    # 분석 결과 테이블 생성
    results = analysis_data.get('results', [])
    if not results:
        return fear_greed_display, "", timestamp, "분석 결과가 없습니다."
    
    # 상위 20개 결과만 표시
    top_results = results[:20]
    
    table_rows = []
    for result in top_results:
        row = dbc.Row([
            dbc.Col(result['ticker'], width=2),
            dbc.Col(result['company_name'], width=3),
            dbc.Col(f"${result['price']}", width=2),
            dbc.Col("✅" if result['golden_cross'] else "❌", width=1),
            dbc.Col("✅" if result['above_ma_lines'] else "❌", width=1),
            dbc.Col("✅" if result['above_125_ma'] else "❌", width=1),
            dbc.Col("✅" if result['steady_above_125'] else "❌", width=1),
            dbc.Col(html.Span(result['score'], className=f"badge bg-{'success' if result['score'] >= 75 else 'warning' if result['score'] >= 50 else 'danger'}"), width=1)
        ], className="mb-2")
        table_rows.append(row)
    
    results_table = dbc.Card([
        dbc.CardHeader(f"🎯 분석 결과 (상위 20개) - 기간: {period_used}"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col("티커", width=2, className="fw-bold"),
                dbc.Col("회사명", width=3, className="fw-bold"),
                dbc.Col("현재가", width=2, className="fw-bold"),
                dbc.Col("골든크로스", width=1, className="fw-bold"),
                dbc.Col("MA선상", width=1, className="fw-bold"),
                dbc.Col("125일선", width=1, className="fw-bold"),
                dbc.Col("지지", width=1, className="fw-bold"),
                dbc.Col("점수", width=1, className="fw-bold")
            ], className="mb-3"),
            *table_rows
        ])
    ])
    
    return fear_greed_display, "", timestamp, results_table

if __name__ == '__main__':
    print("🚀 주식 분석 시스템 시작...")
    print("📊 브라우저에서 http://localhost:8050 접속")
    serve(app.server, host='0.0.0.0', port=8050)
