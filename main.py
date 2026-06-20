import streamlit as st
import yfinance as tf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="AI 종목별 주식 예측 대시보드",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI 종목별 주식 가격 예측 프로그램")
st.markdown("""
이 프로그램은 여러 종목의 주가 데이터를 개별적으로 분석하고, **과거 데이터 기반의 예측 모델(트렌드 및 이동평균 기반)**을 통해 
각 종목별 향후 흐름을 시각화해 주는 스트림릿 대시보드입니다.
""")

# Sidebar
st.sidebar.header("⚙️ 종목 및 분석 설정")

# Multiple ticker selection or input
ticker_input = st.sidebar.text_input(
    "분석할 주식 티커들을 입력하세요 (쉼표로 구분)", 
    value="AAPL, TSLA, 005930.KS"
)
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# Date selection
today = datetime.today()
start_date = st.sidebar.date_input("시작일", today - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", today)

# Prediction horizon
pred_days = st.sidebar.selectbox("AI 예측 기간 (거래일 기준)", [5, 10, 20, 60], index=0)

if st.sidebar.button("종목별 데이터 분석 및 예측 실행") and tickers:
    # Create tabs for each ticker
    tabs = st.tabs(tickers)
    
    for i, ticker in enumerate(tickers):
        with tabs[i]:
            st.subheader(f"📊 {ticker} 분석 결과")
            
            with st.spinner(f"{ticker} 데이터를 불러오는 중..."):
                try:
                    # Fetch data
                    df = tf.download(ticker, start=start_date, end=end_date)
                    
                    if df.empty:
                        st.error(f"{ticker} 데이터를 가져오지 못했습니다. 티커명을 확인해 주세요.")
                        continue
                        
                    # Calculate features
                    df['MA20'] = df['Close'].rolling(window=20).mean()
                    df['MA50'] = df['Close'].rolling(window=50).mean()
                    
                    # Latest parameters
                    latest_close = float(df['Close'].iloc[-1])
                    prev_close = float(df['Close'].iloc[-2])
                    price_change = latest_close - prev_close
                    pct_change = (price_change / prev_close) * 100
                    
                    # Metrics Layout
                    m1, m2, m3 = st.columns(3)
                    
                    currency_symbol = "원" if ".KS" in ticker or ".KQ" in ticker else "$"
                    val_format = f"{int(latest_close):,}원" if currency_symbol == "원" else f"${latest_close:,.2f}"
                    delta_format = f"{price_change:+,.2f} ({pct_change:+.2f}%)" if currency_symbol == "원" else f"${price_change:+,.2f} ({pct_change:+.2f}%)"
                    
                    m1.metric(label="현재 종가 (최근 거래일)", value=val_format, delta=delta_format)
                    
                    # AI Linear-Trend Projection (Baseline Engine)
                    # Simple linear regression approach on recent 30 days for forecasting
                    recent_data = df['Close'].tail(30).values
                    x = np.arange(len(recent_data))
                    slope, intercept = np.polyfit(x, recent_data, 1)
                    
                    # Forecast future prices
                    future_x = np.arange(len(recent_data), len(recent_data) + pred_days)
                    future_predictions = slope * future_x + intercept
                    predicted_price = future_predictions[-1]
                    
                    pred_change = predicted_price - latest_close
                    pred_pct = (pred_change / latest_close) * 100
                    
                    pred_val_format = f"{int(predicted_price):,}원" if currency_symbol == "원" else f"${predicted_price:,.2f}"
                    pred_delta_format = f"{pred_change:+,.2f} ({pred_pct:+.2f}%)"
                    
                    m2.metric(
                        label=f"AI {pred_days}일 뒤 예상 종가", 
                        value=pred_val_format, 
                        delta=pred_delta_format,
                        delta_color="normal" if pred_change >= 0 else "inverse"
                    )
                    
                    m3.metric(label="데이터 분석 기간", value=f"{len(df)} 거래일")
                    
                    # Combined History + Forecast Chart
                    st.write("📈 **주가 추이 및 AI 예측 라인**")
                    
                    # Prepare dates for future
                    last_date = df.index[-1]
                    future_dates = [last_date + timedelta(days=x) for x in range(1, pred_days + 1)]
                    
                    # Custom plotting using Streamlit Line Chart via DataFrame
                    # For a production app, plotly provides smoother interactive charts
                    history_series = df['Close'].tail(90)
                    forecast_series = pd.Series(future_predictions, index=future_dates)
                    
                    # Merging for visualization
                    plot_df = pd.DataFrame({
                        '💡 실제 과거 종가': history_series,
                        '🔮 AI 예측 가격': pd.concat([pd.Series([latest_close], index=[last_date]), forecast_series])
                    })
                    
                    st.line_chart(plot_df)
                    
                    # Technical summary
                    st.write("🔍 **기술적 분석 지표 (최근 5일)**")
                    st.dataframe(df[['Close', 'Volume', 'MA20', 'MA50']].tail(5).style.format("{:.2f}"))
                    
                except Exception as e:
                    st.error(f"{ticker} 분석 중 오류 발생: {e}")
else:
    st.info("← 왼쪽 사이드바에서 분석을 원하는 종목 티커들을 입력하고 버튼을 클릭하세요. (예: AAPL, TSLA, 005930.KS)")
