import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="주식 변동성 및 리스크 분석기",
    page_icon="🌪️",
    layout="wide"
)

st.title("🌪️ AI 주식 변동성(Volatility) 및 리스크 분석기")
st.markdown("""
이 대시보드는 주식의 **과거 변동성과 볼린저 밴드, ATR 지표**를 분석하여 
조만간 주가가 크게 요동칠 가능성이 있는지(변동성 확대 국면)를 시각적으로 진단해 줍니다.
""")

# Sidebar
st.sidebar.header("⚙️ 분석 설정")
ticker = st.sidebar.text_input("종목 티커 입력 (예: 005930.KS, AAPL, TSLA)", value="TSLA")
period = st.sidebar.selectbox("데이터 조회 기간", ["6mo", "1y", "2y", "5y"], index=1)

if st.sidebar.button("변동성 분석 실행", type="primary"):
    with st.spinner(f"{ticker} 변동성 데이터를 분석 중입니다..."):
        try:
            # 1. 데이터 수집
            df = yf.download(ticker, period=period, progress=False)
            
            if df.empty:
                st.error("데이터를 가져오지 못했습니다. 티커명을 확인해 주세요.")
            else:
                # MultiIndex 오류 평탄화 (yfinance 최신버전 대응)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                    
                # 2. 지표 계산
                # (1) 볼린저 밴드 (20일 기준)
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['StdDev'] = df['Close'].rolling(window=20).std()
                df['BB_Upper'] = df['MA20'] + (df['StdDev'] * 2)
                df['BB_Lower'] = df['MA20'] - (df['StdDev'] * 2)
                df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['MA20'] * 100 # 밴드폭(%)
                
                # (2) 역사적 변동성 (Historical Volatility, 20일 기준 연율화)
                df['Daily_Return'] = df['Close'].pct_change()
                df['HV'] = df['Daily_Return'].rolling(window=20).std() * np.sqrt(252) * 100
                
                # (3) ATR (Average True Range, 14일 기준) - 하루 평균 움직임 폭
                df['High-Low'] = df['High'] - df['Low']
                df['High-PrevClose'] = np.abs(df['High'] - df['Close'].shift(1))
                df['Low-PrevClose'] = np.abs(df['Low'] - df['Close'].shift(1))
                df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)
                df['ATR'] = df['TR'].rolling(window=14).mean()
                
                # 결측치 제거
                df = df.dropna()
                
                # 3. 최신 데이터 추출
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                
                current_price = float(latest['Close'])
                current_hv = float(latest['HV'])
                current_bb_width = float(latest['BB_Width'])
                current_atr = float(latest['ATR'])
                
                currency_symbol = "원" if ".KS" in ticker or ".KQ" in ticker else "$"
                format_price = lambda x: f"{int(x):,}{currency_symbol}" if currency_symbol == "원" else f"${x:,.2f}"
                
                # 4. 상단 요약 매트릭스
                st.subheader(f"📊 {ticker} 현재 변동성 진단")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("현재 종가", format_price(current_price))
                col2.metric("역사적 변동성 (HV)", f"{current_hv:.1f}%", 
                            help="연간 기준으로 환산한 주가 수익률의 표준편차입니다. 30% 이상이면 고변동성 종목으로 분류됩니다.")
                
                # 볼린저 밴드 폭 변화량 계산
                bb_width_change = current_bb_width - float(prev['BB_Width'])
                col3.metric("볼린저 밴드 폭 (수축/확장)", f"{current_bb_width:.1f}%", delta=f"{bb_width_change:+.1f}%", delta_color="off",
                            help="밴드 폭이 좁아질수록 에너지가 응축되어 조만간 큰 변동이 발생할 확률이 높습니다.")
                
                col4.metric("하루 평균 변동폭 (ATR)", format_price(current_atr),
                            help="최근 14일 동안 하루 평균 주가가 고점과 저점 사이에서 얼마만큼 움직였는지 나타냅니다.")
                
                # 5. AI 변동성 코멘트
                st.markdown("### 💡 변동성 시그널 분석")
                if current_bb_width < df['BB_Width'].quantile(0.2):
                    st.warning("**⚠️ 볼린저 밴드 수축(Squeeze) 상태:** 밴드 폭이 과거 1년 중 하위 20% 이내로 매우 좁습니다. 에너지가 응축되어 있어 조만간 위든 아래든 **급격한 주가 변동이 발생할 가능성이 매우 높습니다.** 방향성 이탈을 주의 깊게 살피세요.")
                elif current_bb_width > df['BB_Width'].quantile(0.8):
                    st.info("**📈 볼린저 밴드 확장 상태:** 주가 변동성이 이미 크게 확대된 상태입니다. 단기 고점이나 저점을 형성한 후 다시 안정화(평균 회귀)될 가능성이 있습니다.")
                else:
                    st.success("**✅ 정상 변동성 구간:** 주가가 일반적인 변동성 범위 내에서 안정적으로 움직이고 있습니다.")
                
                # 6. 인터랙티브 차트 (Plotly)
                st.subheader("📈 주가 및 볼린저 밴드 차트")
                
                fig = go.Figure()
                
                # 캔들스틱 차트
                fig.add_trace(go.Candlestick(x=df.index,
                                open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'],
                                name='캔들스틱'))
                
                # 볼린저 밴드 영역
                fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='rgba(250, 0, 0, 0.2)'), name='Upper Band'))
                fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='rgba(0, 0, 250, 0.2)'), fill='tonexty', name='Lower Band'))
                fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1.5), name='20일 이평선'))
                
                fig.update_layout(xaxis_rangeslider_visible=False, height=500, template='plotly_dark')
                st.plotly_chart(fig, use_container_width=True)
                
                # 하단 차트: 역사적 변동성 트렌드
                st.subheader("📉 역사적 변동성(HV) 흐름")
                st.line_chart(df['HV'], height=200)

        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
else:
    st.info("← 사이드바에서 티커를 입력하고 버튼을 클릭하세요.")
