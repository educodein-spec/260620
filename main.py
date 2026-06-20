import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="한국 주식 AI 예측 대시보드",
    page_icon="📈",
    layout="wide"
)

# 2. 제목 및 설명
st.title("📈 한국 주식 가격 예측 및 분석 프로그램")
st.markdown("""
이 프로그램은 한국 주식(KOSPI, KOSDAQ) 데이터를 가져와 **선형 회귀 알고리즘**을 통해 향후 주가 추세를 예측합니다.
* **티커 입력 예시:** 삼성전자(`005930.KS`), SK하이닉스(`000660.KS`), 에코프로비엠(`247540.KQ`)
""")

# 3. 사이드바 설정
st.sidebar.header("⚙️ 분석 설정")
ticker_symbol = st.sidebar.text_input("종목 코드를 입력하세요", value="005930.KS")

# 날짜 설정
today = datetime.today()
start_date = st.sidebar.date_input("데이터 시작일", today - timedelta(days=365))
end_date = st.sidebar.date_input("데이터 종료일", today)

# 예측 기간 설정
pred_days = st.sidebar.slider("AI 예측 기간 (거래일)", 1, 20, 5)

# 4. 분석 실행 버튼
if st.sidebar.button("주식 데이터 분석 및 예측 실행"):
    with st.spinner(f"{ticker_symbol} 데이터를 분석 중입니다..."):
        try:
            # 데이터 다운로드
            df = yf.download(ticker_symbol, start=start_date, end=end_date)

            if df.empty:
                st.error("데이터를 불러오지 못했습니다. 종목 코드와 날짜를 확인해 주세요.")
            else:
                # [오류 해결] yfinance MultiIndex 컬럼 평탄화
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # 기술적 지표 계산
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA50'] = df['Close'].rolling(window=50).mean()

                # 현재 상태 지표
                latest_close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                price_diff = latest_close - prev_close
                pct_change = (price_diff / prev_close) * 100

                # 5. 상단 지표 요약 (Metric)
                col1, col2, col3 = st.columns(3)
                
                currency = "원" if (".KS" in ticker_symbol or ".KQ" in ticker_symbol) else "$"
                
                col1.metric("현재가", f"{int(latest_close):,}{currency}", f"{price_diff:+,} ({pct_change:+.2f}%)")
                
                # --- AI 예측 로직 (선형 회귀) ---
                recent_30 = df['Close'].tail(30).values
                x = np.arange(len(recent_30))
                slope, intercept = np.polyfit(x, recent_30, 1) # 기울기와 절편 계산
                
                # 미래 가격 계산
                future_x = np.arange(len(recent_30), len(recent_30) + pred_days)
                future_preds = slope * future_x + intercept
                final_pred = future_preds[-1]
                
                pred_diff = final_pred - latest_close
                pred_pct = (pred_diff / latest_close) * 100
                
                col2.metric(f"{pred_days}일 뒤 예측가", f"{int(final_pred):,}{currency}", 
                           f"{pred_diff:+,} ({pred_pct:+.2f}%)", delta_color="normal" if pred_diff > 0 else "inverse")
                
                col3.metric("데이터 수집량", f"{len(df)}일분")

                # 6. 차트 시각화
                st.subheader(f"📊 {ticker_symbol} 주가 추이 및 AI 예측")
                
                # 미래 날짜 생성 (주말 제외)
                last_date = df.index[-1]
                future_dates = pd.bdate_range(start=last_date + timedelta(days=1), periods=pred_days)
                
                # 시각화용 데이터프레임 구성
                history = df['Close'].tail(100)
                forecast = pd.Series(future_preds, index=future_dates)
                
                # 예측 시작점을 실제 종가와 연결
                forecast = pd.concat([pd.Series([latest_close], index=[last_date]), forecast])
                
                plot_df = pd.DataFrame({
                    '실제 주가': history,
                    'AI 예측선': forecast
                })
                
                st.line_chart(plot_df)

                # 7. 상세 데이터 표
                st.subheader("📋 상세 데이터 (최근 10일)")
                st.dataframe(df[['Open', 'High', 'Low', 'Close', 'Volume', 'MA20']].tail(10).style.format("{:,.0f}"))

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("왼쪽 사이드바에서 종목 코드를 입력하고 버튼을 눌러주세요. (예: 삼성전자 005930.KS)")
