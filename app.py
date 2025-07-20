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
    
    def get_recommendations(self, market='ALL', period='6mo', limit=None):
        """추천 종목 리스트 가져오기 (전체 또는 제한)"""
        print(f"[DEBUG] get_recommendations 호출: market={market}, period={period}, limit={limit}")
        
        # 현재 기간 저장
        self.current_period = period
        
        # 시가총액 기업 가져오기 (전체 또는 제한)
        symbols = self.get_top_companies_by_market_cap(market, limit)
        
        print(f"[DEBUG] 분석할 종목 수: {len(symbols)}")
        
        # 병렬 처리로 분석 수행
        results = self._analyze_stocks_parallel(symbols, period)
        
        # 점수순으로 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"[DEBUG] 분석 완료: {len(results)}개 종목")
        
        return results

    def _analyze_stocks_parallel(self, symbols, period):
        """병렬 처리로 주식 분석 수행"""
        results = []
        total_symbols = len(symbols)
        
        def analyze_single_stock(symbol):
            try:
                analysis = self.analyze_stock(symbol, period, symbols)
                return analysis
            except Exception as e:
                print(f"[ERROR] {symbol} 분석 중 오류: {str(e)}")
                return None
        
        # 대용량 처리를 위해 워커 수와 타임아웃 조정
        max_workers = min(4, total_symbols // 10 + 1)  # 동적 워커 수 조정
        timeout_total = max(600, total_symbols * 2)  # 총 타임아웃 (최소 10분)
        timeout_single = min(60, timeout_total // total_symbols)  # 개별 타임아웃
        
        print(f"[DEBUG] 병렬 처리 설정: 워커={max_workers}, 총타임아웃={timeout_total}초, 개별타임아웃={timeout_single}초")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 모든 분석 작업을 제출
            future_to_symbol = {executor.submit(analyze_single_stock, symbol): symbol for symbol in symbols.keys()}
            
            # 완료된 작업부터 결과 수집
            completed_count = 0
            for future in as_completed(future_to_symbol, timeout=timeout_total):
                symbol = future_to_symbol[future]
                try:
                    analysis = future.result(timeout=timeout_single)
                    if analysis:
                        results.append(analysis)
                    
                    completed_count += 1
                    
                    # 진행률 표시 (10% 단위)
                    if completed_count % max(1, total_symbols // 10) == 0:
                        progress = completed_count / total_symbols * 100
                        print(f"[DEBUG] 분석 진행률: {completed_count}/{total_symbols} ({progress:.1f}%)")
                        
                except Exception as e:
                    print(f"[ERROR] {symbol} 결과 처리 중 오류: {str(e)}")
        
        return results

    def _get_us_company_names(self):
        """미국 기업명 하드코딩 (API 호출 최소화)"""
        return {
            'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp.', 'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.', 'NVDA': 'NVIDIA Corp.', 'META': 'Meta Platforms Inc.',
            'TSLA': 'Tesla Inc.', 'BRK-B': 'Berkshire Hathaway Inc.', 'LLY': 'Eli Lilly and Co.',
            'AVGO': 'Broadcom Inc.', 'UNH': 'UnitedHealth Group Inc.', 'JPM': 'JPMorgan Chase & Co.',
            'XOM': 'Exxon Mobil Corp.', 'V': 'Visa Inc.', 'PG': 'Procter & Gamble Co.',
            'JNJ': 'Johnson & Johnson', 'MA': 'Mastercard Inc.', 'HD': 'Home Depot Inc.',
            'CVX': 'Chevron Corp.', 'ABBV': 'AbbVie Inc.', 'PFE': 'Pfizer Inc.',
            'BAC': 'Bank of America Corp.', 'KO': 'Coca-Cola Co.', 'COST': 'Costco Wholesale Corp.',
            'TMO': 'Thermo Fisher Scientific Inc.', 'WMT': 'Walmart Inc.', 'CSCO': 'Cisco Systems Inc.',
            'DIS': 'Walt Disney Co.', 'ABT': 'Abbott Laboratories', 'DHR': 'Danaher Corp.',
            'MRK': 'Merck & Co. Inc.', 'ADBE': 'Adobe Inc.', 'CRM': 'Salesforce Inc.',
            'NFLX': 'Netflix Inc.', 'INTC': 'Intel Corp.', 'AMD': 'Advanced Micro Devices Inc.',
            'QCOM': 'Qualcomm Inc.', 'IBM': 'International Business Machines Corp.', 'GE': 'General Electric Co.',
            'BA': 'Boeing Co.', 'CAT': 'Caterpillar Inc.', 'HON': 'Honeywell International Inc.',
            'RTX': 'Raytheon Technologies Corp.', 'GS': 'Goldman Sachs Group Inc.', 'MS': 'Morgan Stanley',
            'VZ': 'Verizon Communications Inc.', 'CMCSA': 'Comcast Corp.', 'NKE': 'Nike Inc.',
            'ORCL': 'Oracle Corp.', 'PEP': 'PepsiCo Inc.', 'TXN': 'Texas Instruments Inc.',
            'PM': 'Philip Morris International Inc.', 'T': 'AT&T Inc.', 'AMGN': 'Amgen Inc.',
            'COP': 'ConocoPhillips', 'UNP': 'Union Pacific Corp.', 'NEE': 'NextEra Energy Inc.',
            'LOW': 'Lowe\'s Companies Inc.', 'TMUS': 'T-Mobile US Inc.', 'AMAT': 'Applied Materials Inc.',
            'ISRG': 'Intuitive Surgical Inc.', 'BKNG': 'Booking Holdings Inc.', 'VRTX': 'Vertex Pharmaceuticals Inc.',
            'ADP': 'Automatic Data Processing Inc.', 'SBUX': 'Starbucks Corp.', 'GILD': 'Gilead Sciences Inc.',
            'ADI': 'Analog Devices Inc.', 'LRCX': 'Lam Research Corp.', 'MDLZ': 'Mondelez International Inc.',
            'REGN': 'Regeneron Pharmaceuticals Inc.', 'PYPL': 'PayPal Holdings Inc.', 'KLAC': 'KLA Corp.',
            'MRVL': 'Marvell Technology Inc.', 'ORLY': 'O\'Reilly Automotive Inc.', 'CDNS': 'Cadence Design Systems Inc.',
            'SNPS': 'Synopsys Inc.', 'NXPI': 'NXP Semiconductors NV', 'WDAY': 'Workday Inc.',
            'ABNB': 'Airbnb Inc.', 'FTNT': 'Fortinet Inc.', 'DDOG': 'Datadog Inc.',
            'TEAM': 'Atlassian Corp.', 'ZM': 'Zoom Video Communications Inc.', 'CRWD': 'CrowdStrike Holdings Inc.',
            'ZS': 'Zscaler Inc.', 'OKTA': 'Okta Inc.', 'DOCU': 'DocuSign Inc.',
            'NOW': 'ServiceNow Inc.', 'PANW': 'Palo Alto Networks Inc.', 'MU': 'Micron Technology Inc.',
            'ANET': 'Arista Networks Inc.', 'LULU': 'Lululemon Athletica Inc.', 'ODFL': 'Old Dominion Freight Line Inc.',
            'EXC': 'Exelon Corp.', 'CTAS': 'Cintas Corp.', 'ROST': 'Ross Stores Inc.',
            'TJX': 'TJX Companies Inc.', 'MCD': 'McDonald\'s Corp.', 'YUM': 'Yum! Brands Inc.',
            'CMG': 'Chipotle Mexican Grill Inc.', 'FAST': 'Fastenal Co.', 'PAYX': 'Paychex Inc.',
            'VRSK': 'Verisk Analytics Inc.', 'CHTR': 'Charter Communications Inc.', 'EA': 'Electronic Arts Inc.'
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
        with ThreadPoolExecutor(max_workers=2) as executor:
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
                    
                    # 하이라이트 박스 (테두리 없음)
                    fig.add_shape(
                        type="rect",
                        x0=recent_date - timedelta(days=7),
                        y0=max(ma20, ma60),
                        x1=recent_date,
                        y1=current_price * 1.02,
                        fillcolor="lightgreen",
                        opacity=0.5,
                        layer="below",
                        line=dict(width=0)  # 테두리 제거
                    )
                    
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
            
            # 125일선 지지 영역 표시
            if analysis['ma125_support']:
                recent_dates = df.index[-analysis['support_count']:]
                for i, date in enumerate(recent_dates):
                    ma125_price = df.loc[date, 'MA125']
                    close_price = df.loc[date, 'Close']
                    
                    # 지지 영역 표시 (테두리 없음)
                    fig.add_shape(
                        type="rect",
                        x0=date - timedelta(days=1),
                        y0=ma125_price,
                        x1=date + timedelta(days=1),
                        y1=close_price,
                        fillcolor="yellow",
                        opacity=0.6,
                        layer="below",
                        line=dict(width=0)  # 테두리 제거
                    )
                    
                    # 지지 횟수 표시
                    fig.add_annotation(
                        x=date,
                        y=ma125_price * 0.98,
                        text=f"지지 {i+1}",
                        showarrow=False,
                        font=dict(size=8, color="orange"),
                        bgcolor="yellow",
                        bordercolor="orange",
                        borderwidth=1
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
    
    st.title("📈 주식 기술적 분석 종목 추천 시스템")
    
    # 사이드바 설정
    st.sidebar.header("🔍 분석 설정")
    
    market = st.sidebar.selectbox(
        "시장 선택",
        options=['SP500', 'NASDAQ', 'KOSPI', 'KOSDAQ'],
        format_func=lambda x: {
            'SP500': 'S&P 500 (미국 대형주 전체)',
            'NASDAQ': 'NASDAQ (미국 기술주 전체)',
            'KOSPI': 'KOSPI (한국 대형주 50)',
            'KOSDAQ': 'KOSDAQ (한국 기술주 50)'
        }[x]
    )
    
    # 분석 규모 선택 (미국 시장만)
    analysis_size = None
    if market in ['SP500', 'NASDAQ']:
        analysis_size = st.sidebar.selectbox(
            "분석 규모",
            options=['전체', '상위50', '상위100'],
            index=1,  # 기본값: 상위50
            help="전체 분석 시 시간이 오래 걸릴 수 있습니다."
        )
        
        # 분석 개수 결정
        if analysis_size == '전체':
            limit = None
        elif analysis_size == '상위50':
            limit = 50
        elif analysis_size == '상위100':
            limit = 100
    else:
        limit = 50  # 한국 시장은 기본 50개
    
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
        # 분석 규모에 따른 예상 시간 안내
        if market in ['SP500', 'NASDAQ'] and analysis_size == '전체':
            expected_time = "15-30분"
            total_stocks = "500개" if market == 'SP500' else "200개"
        elif market in ['SP500', 'NASDAQ'] and analysis_size == '상위100':
            expected_time = "5-10분"
            total_stocks = "100개"
        else:
            expected_time = "2-5분"
            total_stocks = "50개"
            
        st.info(f"📊 {total_stocks} 종목 분석 시작 (예상 소요 시간: {expected_time})")
        
        with st.spinner(f"{market} 시장 {total_stocks} 분석 중... 잠시만 기다려주세요."):
            try:
                results = analyzer.get_recommendations(market, period, limit)
                st.session_state.analysis_results = results
                st.session_state.current_market = market
                st.session_state.current_period = period
                st.session_state.current_analysis_size = analysis_size if market in ['SP500', 'NASDAQ'] else '상위50'
                
                st.success(f"✅ 분석 완료! 총 {len(results)}개 종목 분석")
                
            except Exception as e:
                st.error(f"❌ 분석 중 오류 발생: {str(e)}")
                st.session_state.analysis_results = []
    
    # 분석 결과 표시
    if st.session_state.analysis_results:
        current_market = st.session_state.get('current_market', market)
        current_analysis_size = st.session_state.get('current_analysis_size', '상위50')
        
        st.subheader(f"🎯 분석 결과 ({current_market} - {current_analysis_size})")
        
        # 결과를 DataFrame으로 변환
        results_data = []
        for i, result in enumerate(st.session_state.analysis_results):
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
            selected_result = st.session_state.analysis_results[selected_idx]
            
            st.subheader(f"📊 {selected_result['company_name']} ({selected_result['symbol']}) 차트")
            
            # 차트 생성 및 표시
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
    
    # 사이드바에 사용법 설명
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 사용법")
    st.sidebar.markdown("""
    1. **시장 선택**: 분석할 시장을 선택하세요
    2. **분석 규모**: 미국 시장의 경우 전체/상위100/상위50 선택
    3. **기간 설정**: 차트 조회 기간을 설정하세요  
    4. **분석 시작**: 버튼을 클릭하여 분석을 시작하세요
    5. **결과 확인**: 표에서 종목을 클릭하면 차트가 표시됩니다
    
    **점수 기준:**
    - 골든크로스: 25점
    - 이평선 위: 25점  
    - 125일선 지지: 25점
    - 추세 안정: 25점
    
    **⚠️ 주의사항:**
    - 전체 분석 시 시간이 많이 소요됩니다
    - S&P 500 전체: 500개 종목 (15-30분)
    - NASDAQ 전체: 200개 종목 (10-20분)
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ 정보")
    st.sidebar.markdown("""
    - 실시간 데이터 기반 분석
    - 기술적 분석 지표 활용
    - 골든크로스 패턴 감지
    - 이동평균선 기반 추세 분석
    - 대용량 병렬 처리 최적화
    """)
    
    # 성능 정보 표시
    if st.session_state.analysis_results:
        total_analyzed = len(st.session_state.analysis_results)
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📈 분석 현황")
        st.sidebar.metric("분석 완료 종목", f"{total_analyzed}개")
        
        # 점수별 분포
        high_score = len([r for r in st.session_state.analysis_results if r['score'] >= 75])
        medium_score = len([r for r in st.session_state.analysis_results if 50 <= r['score'] < 75])
        low_score = len([r for r in st.session_state.analysis_results if r['score'] < 50])
        
        st.sidebar.markdown("**점수 분포:**")
        st.sidebar.markdown(f"- 고점수 (75점+): {high_score}개")
        st.sidebar.markdown(f"- 중간점수 (50-74점): {medium_score}개") 
        st.sidebar.markdown(f"- 저점수 (50점 미만): {low_score}개")

if __name__ == '__main__':
    main()import streamlit as st
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
        
    def _get_us_market_cap_from_yahoo(self, market_type='SP500', limit=None):
        """미국 시가총액 상위 종목 가져오기 (하드코딩)"""
        try:
            print(f"[DEBUG] 미국 {market_type} 시가총액 종목 조회 시도")
            
            if market_type == 'SP500':
                # S&P 500 전체 기업 리스트 (500개 전체)
                sp500_symbols = [
                    # 대형주 (상위 100개)
                    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'BRK-B', 'LLY', 'AVGO', 'UNH',
                    'JPM', 'XOM', 'V', 'PG', 'JNJ', 'MA', 'HD', 'CVX', 'ABBV', 'PFE',
                    'BAC', 'KO', 'COST', 'TMO', 'WMT', 'CSCO', 'DIS', 'ABT', 'DHR', 'MRK',
                    'ADBE', 'CRM', 'NFLX', 'INTC', 'AMD', 'QCOM', 'IBM', 'GE', 'BA', 'CAT',
                    'HON', 'RTX', 'GS', 'MS', 'VZ', 'CMCSA', 'NKE', 'ORCL', 'PEP', 'TXN',
                    'PM', 'T', 'AMGN', 'COP', 'UNP', 'NEE', 'LOW', 'TMUS', 'AMAT', 'ISRG',
                    'BKNG', 'VRTX', 'ADP', 'SBUX', 'GILD', 'ADI', 'LRCX', 'MDLZ', 'REGN',
                    'PYPL', 'KLAC', 'MRVL', 'ORLY', 'CDNS', 'SNPS', 'NXPI', 'WDAY', 'ABNB', 'FTNT',
                    'DDOG', 'TEAM', 'ZM', 'CRWD', 'ZS', 'OKTA', 'DOCU', 'NOW', 'PANW', 'MU',
                    'ANET', 'LULU', 'ODFL', 'EXC', 'CTAS', 'ROST', 'TJX', 'MCD', 'YUM', 'CMG',
                    
                    # 중형주 (101-200위)
                    'FAST', 'PAYX', 'VRSK', 'CHTR', 'EA', 'PCAR', 'MCHP', 'KDP', 'TTWO', 'CTSH',
                    'DXCM', 'MNST', 'MAR', 'AZO', 'CPRT', 'NTES', 'EBAY', 'IDXX', 'SGEN', 'SPLK',
                    'VRSN', 'SWKS', 'CDW', 'INCY', 'ALGN', 'EXPE', 'TROW', 'FISV', 'CTXS', 'CERN',
                    'XLNX', 'ADSK', 'BMRN', 'MRNA', 'BIIB', 'ILMN', 'CSX', 'WBA', 'DLTR', 'TSCO',
                    'FOX', 'FOXA', 'NDAQ', 'ULTA', 'ANSS', 'ALXN', 'MXIM', 'JBHT', 'SIRI', 'CHRW',
                    'HOLX', 'NTAP', 'MELI', 'JD', 'ROKU', 'CELG', 'WLTW', 'HAS', 'MAT', 'EXPD',
                    'SBAC', 'MSCI', 'INFO', 'TER', 'SIVB', 'NCLH', 'AAL', 'WYNN', 'LVS', 'MGM',
                    'CZR', 'PENN', 'BYD', 'SAVE', 'JBLU', 'ALK', 'LUV', 'UAL', 'DAL', 'CCL',
                    'RCL', 'TRIP', 'UPS', 'FDX', 'POOL', 'TECH', 'SMCI', 'MKTX', 'ENPH', 'MPWR',
                    
                    # 중소형주 (201-300위)
                    'FSLR', 'SEDG', 'RUN', 'SPWR', 'CSIQ', 'JKS', 'SOL', 'NOVA', 'OLED', 'RGEN',
                    'LGND', 'ALNY', 'RARE', 'FOLD', 'SRPT', 'BLUE', 'SAGE', 'ARWR', 'EDIT', 'CRSP',
                    'NTLA', 'BEAM', 'VERV', 'PRTG', 'VCEL', 'CAPR', 'ALEC', 'AMRS', 'GMAB', 'KRTX',
                    'MRTX', 'CVAC', 'BPMC', 'GLPG', 'GTHX', 'IMMU', 'SRNE', 'INO', 'NVAX', 'BNTX',
                    'A', 'SYK', 'BSX', 'MDT', 'HOLX', 'VAR', 'ALGN', 'EW', 'TDOC', 'VEEV',
                    'RMD', 'PODD', 'TNDM', 'OMCL', 'LIVN', 'NEOG', 'NVCR', 'IOVA', 'ZLAB', 'AKCA',
                    'MIRM', 'PRTA', 'PACB', 'NVTA', 'CDNA', 'FATE', 'RGNX', 'DNLI', 'ARCT', 'RDUS',
                    'TGTX', 'CPRX', 'CTIC', 'ADPT', 'MRSN', 'CBPO', 'RVMD', 'SWTX', 'YMAB', 'IBRX',
                    'PRAX', 'PTCT', 'CDMO', 'MDGL', 'HOOK', 'PRME', 'KYMR', 'KRYS', 'ETNB', 'VKTX',
                    'CGEM', 'SERA', 'XENE', 'VTRS', 'LYEL', 'GLUE', 'PCRX', 'TPTX', 'MMM', 'AOS',
                    
                    # 소형주 (301-400위)
                    'APD', 'AKAM', 'ALB', 'ARE', 'ALLE', 'LNT', 'ALL', 'MO', 'AMCR', 'AEE',
                    'AEP', 'AXP', 'AIG', 'AMT', 'AWK', 'AMP', 'ABC', 'AME', 'APH', 'ANTM',
                    'AON', 'APA', 'APTV', 'ADM', 'AJG', 'AIZ', 'ATO', 'AZO', 'AVB', 'AVY',
                    'BKR', 'BLL', 'BBWI', 'BAX', 'BDX', 'BBY', 'BIO', 'BIIB', 'BLK', 'BK',
                    'BKNG', 'BWA', 'BXP', 'BSX', 'BMY', 'BR', 'BRO', 'BF-B', 'CDNS', 'CPT',
                    'CPB', 'COF', 'CAH', 'KMX', 'CARR', 'CTLT', 'CBOE', 'CBRE', 'CDW', 'CE',
                    'CNC', 'CNP', 'CDAY', 'CF', 'CRL', 'SCHW', 'CHD', 'CI', 'CINF', 'CTAS',
                    'CTVA', 'GLW', 'CTSH', 'CME', 'CMS', 'KO', 'CTSH', 'CL', 'CMCSA', 'CMA',
                    'CAG', 'COP', 'ED', 'STZ', 'COO', 'CPRT', 'GLW', 'CTVA', 'COST', 'CTRA',
                    'CCI', 'CSX', 'CMI', 'CVS', 'DHI', 'DHR', 'DRI', 'DVA', 'DE', 'DAL',
                    
                    # 나머지 소형주 (401-500위)
                    'XRAY', 'DVN', 'DXCM', 'FANG', 'DLR', 'DFS', 'DISCA', 'DISCK', 'DISH', 'DG',
                    'DLTR', 'D', 'DPZ', 'DOV', 'DOW', 'DTE', 'DUK', 'DRE', 'DD', 'DXC',
                    'EMN', 'ETN', 'EBAY', 'ECL', 'EIX', 'EW', 'EA', 'EMR', 'ENPH', 'ETR',
                    'EOG', 'EFX', 'EQIX', 'EQR', 'ESS', 'EL', 'ETSY', 'EVRG', 'ES', 'RE',
                    'EXC', 'EXPE', 'EXPD', 'EXR', 'XOM', 'FFIV', 'FB', 'FAST', 'FRT', 'FDX',
                    'FIS', 'FITB', 'FE', 'FRC', 'FISV', 'FLT', 'FLIR', 'FLS', 'FMC', 'F',
                    'FTNT', 'FTV', 'FBHS', 'FOXA', 'FOX', 'BEN', 'FCX', 'GPS', 'GRMN', 'IT',
                    'GNRC', 'GD', 'GE', 'GIS', 'GM', 'GPC', 'GILD', 'GL', 'GPN', 'GS'
                ]
                
                if limit:
                    return sp500_symbols[:limit]
                return sp500_symbols
                
            elif market_type == 'NASDAQ':
                # NASDAQ 100 + 주요 기술주 전체 (약 200개)
                nasdaq_symbols = [
                    # NASDAQ 100 핵심 기업들
                    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ADBE',
                    'CRM', 'NFLX', 'INTC', 'AMD', 'QCOM', 'TMUS', 'AMAT', 'ISRG', 'BKNG', 'VRTX',
                    'ADP', 'SBUX', 'GILD', 'ADI', 'LRCX', 'MDLZ', 'REGN', 'PYPL', 'KLAC', 'MRVL',
                    'ORLY', 'CDNS', 'SNPS', 'NXPI', 'WDAY', 'ABNB', 'FTNT', 'DDOG', 'TEAM', 'ZM',
                    'CRWD', 'ZS', 'OKTA', 'DOCU', 'NOW', 'PANW', 'MU', 'ANET', 'LULU', 'ODFL',
                    
                    # 추가 NASDAQ 주요 기업들
                    'FAST', 'PAYX', 'VRSK', 'CHTR', 'EA', 'PCAR', 'MCHP', 'KDP', 'TTWO', 'CTSH',
                    'DXCM', 'MNST', 'MAR', 'AZO', 'CPRT', 'NTES', 'EBAY', 'IDXX', 'SGEN', 'SPLK',
                    'VRSN', 'SWKS', 'CDW', 'INCY', 'ALGN', 'EXPE', 'TROW', 'FISV', 'CTXS', 'CERN',
                    'XLNX', 'ADSK', 'BMRN', 'MRNA', 'BIIB', 'ILMN', 'CSX', 'WBA', 'DLTR', 'TSCO',
                    'FOX', 'FOXA', 'NDAQ', 'ULTA', 'ANSS', 'ALXN', 'MXIM', 'JBHT', 'SIRI', 'CHRW',
                    
                    # 바이오/헬스케어
                    'HOLX', 'NTAP', 'MELI', 'JD', 'ROKU', 'CELG', 'WLTW', 'HAS', 'MAT', 'EXPD',
                    'SBAC', 'MSCI', 'INFO', 'TER', 'SIVB', 'NCLH', 'AAL', 'WYNN', 'LVS', 'MGM',
                    'CZR', 'PENN', 'BYD', 'SAVE', 'JBLU', 'ALK', 'LUV', 'UAL', 'DAL', 'CCL',
                    'RCL', 'TRIP', 'UPS', 'FDX', 'POOL', 'TECH', 'SMCI', 'MKTX', 'ENPH', 'MPWR',
                    
                    # 신재생에너지 & 클린텍
                    'FSLR', 'SEDG', 'RUN', 'SPWR', 'CSIQ', 'JKS', 'SOL', 'NOVA', 'OLED', 'RGEN',
                    'LGND', 'ALNY', 'RARE', 'FOLD', 'SRPT', 'BLUE', 'SAGE', 'ARWR', 'EDIT', 'CRSP',
                    'NTLA', 'BEAM', 'VERV', 'PRTG', 'VCEL', 'CAPR', 'ALEC', 'AMRS', 'GMAB', 'KRTX',
                    
                    # 소프트웨어 & 클라우드
                    'SNOW', 'PLTR', 'U', 'NET', 'ESTC', 'MDB', 'CFLT', 'GTLB', 'BILL', 'ZI',
                    'SMAR', 'PCTY', 'TENB', 'SUMO', 'AI', 'PATH', 'DOCN', 'FROG', 'BIGC', 'COUP',
                    'VEEV', 'ORCL', 'SAP', 'INTU', 'VMW', 'RNG'
                ]
                
                if limit:
                    return nasdaq_symbols[:limit]
                return nasdaq_symbols
            
            return None
            
        except Exception as e:
            print(f"[WARNING] 미국 {market_type} 조회 실패: {e}")
            return None

    def get_top_companies_by_market_cap(self, market='SP500', limit=None):
        """시가총액 기준 상위 기업 가져오기 (전체 또는 제한)"""
        print(f"[DEBUG] 시가총액 기업 조회 시작: market={market}, limit={limit}")
        
        try:
            companies = {}
            
            if market in ['SP500', 'NASDAQ']:
                # 미국 종목은 하드코딩된 회사명 사용 (API 호출 최소화)
                us_symbols = self._get_us_market_cap_from_yahoo(market, limit)
                if us_symbols:
                    # 하드코딩된 회사명 매핑 사용
                    company_names = self._get_us_company_names()
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
            plot_bgcolor='white',
            paper_bgcolor='white',
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
            # 1. 이전에는 20일선
