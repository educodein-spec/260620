import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="한국 주식 AI 예측 (종목명 검색)",
    page_icon="🔎",
    layout="wide"
)

# --- 핵심 추가 기능: 한국 주식 전체 종목 리스트 불러오기 ---
@st.cache_data # 매번 다운로드하지 않도록 캐싱(저장) 처리
def load_korea_stocks():
    # KRX(코스피, 코스닥, 코넥스) 전체 상장 종목 데이터 가져오기
    df = fdr.StockListing('KRX')
    return df[['Name', 'Code', 'Market']]

try:
    stocks_df = load_korea_stocks()
    stock_names = stocks_df['Name'].tolist()
except Exception as e:
    st.error(f"종목 리스트를 불러오는 중 오류가 발생했습니다: {e}")
    stock_names = ['삼성전자', 'SK하이닉스'] # 실패 시 임시 리스트
    stocks_df = pd.DataFrame({'Name': ['삼성전자', 'SK하이닉스'], 'Code': ['005930', '000660'], 'Market': ['KOSPI', 'KOSPI']})
# -------------------------------------------------------------------

# 2. 제목 및 설명
st.title("🔎 한국 주식 가격 예측 (종목명 검색 기능 탑재)")
st.markdown("""
왼쪽 사이드바에서 **원하는 주식의 한글 종목명을 입력하거나 선택**하세요. 
자동으로 종목 코드를 변환하여 최근 데이터를 분석하고 미래 주가를 예측합니다.
""")

# 3. 사이드바 설정 (종목명 검색 창)
st.sidebar.header("⚙️ 종목 검색 및 설정")

# Streamlit의 selectbox는 타이핑 검색(자동완성) 기능을 기본 지원합니다!
default_index = stock_names.index('삼성전자') if '삼성전자' in stock_names else 0
selected_name = st.sidebar.selectbox("🔍 종목명을 검색하세요", stock_names, index=default_index)

# 날짜 및 예측 기간 설정
today = datetime.today()
start_date = st.sidebar.date_input("데이터 시작일", today - timedelta(days=365))
end_date = st.sidebar.date_input("데이터 종료일", today)
pred_days = st.sidebar.slider("AI 예측 기간 (거래일)", 1, 20, 5)

# 선택한 종목명을 yfinance용 코드로 자동 변환하는 로직
stock_info = stocks_df[stocks_df['Name'] == selected_name].iloc[0]
raw_code = stock_info['Code']
market = stock_info['Market']

if 'KOSPI' in market:
    ticker_symbol = f"{raw_code}.KS"
elif 'KOSDAQ' in market:
    ticker_symbol = f"{raw_code}.KQ"
else:
    ticker_symbol = f"{raw_code}.KS" # 예외 처리

if st.sidebar.button("데이터 분석 및 예측 실행"):
    with st.spinner(f"'{selected_name}'({ticker_symbol}) 데이터를 분석 중입니다..."):
        try:
            # yfinance 데이터 다운로드
            df = yf.download(ticker_symbol, start=start_date, end=end_date, progress=False)

            if df.empty:
                st.error("데이터를 불러오지 못했습니다. 최근 상장된 종목이거나 데이터 제공이 지연되었을 수 있습니다.")
            else:
                # yfinance MultiIndex 버그 방어 코드
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # 기술적 지표 계산
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA50'] = df['Close'].rolling(window=50).mean()

                # 최근 데이터 추출
                latest_close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                price_diff = latest_close - prev_close
                pct_change = (price_diff / prev_close) * 100

                # 상단 지표 요약 (Metric)
                col1, col2, col3 = st.columns(3)
                col1.metric(f"현재가 ({selected_name})", f"{int(latest_close):,}원", f"{price_diff:+,.0f} ({pct_change:+.2f}%)")
                
                # --- AI 선형 회귀 예측 로직 ---
                recent_30 = df['Close'].tail(30).values
                if recent_30.ndim > 1:
                    recent_30 = recent_30.flatten()
                    
                x = np.arange(len(recent_30))
                slope, intercept = np.polyfit(x, recent_30, 1)
                
                # 미래 가격 도출
                future_x = np.arange(len(recent_30), len(recent_30) + pred_days)
                future_preds = slope * future_x + intercept
                final_pred = future_preds[-1]
                
                pred_diff = final_pred - latest_close
                pred_pct = (pred_diff / latest_close) * 100
                
                col2.metric(f"AI {pred_days}일 뒤 예측가", f"{int(final_pred):,}원", 
                           f"{pred_diff:+,.0f} ({pred_pct:+.2f}%)", delta_color="normal" if pred_diff >= 0 else "inverse")
                
                col3.metric("종목 코드 (Ticker)", ticker_symbol)

                # 차트 시각화
                st.subheader(f"📊 {selected_name} 주가 추이 및 예측선")
                
                last_date = df.index[-1]
                future_dates = pd.bdate_range(start=last_date + timedelta(days=1), periods=pred_days)
                
                history = df['Close'].tail(90)
                if isinstance(history, pd.DataFrame):
                    history = history.squeeze()
                    
                forecast = pd.Series(future_preds, index=future_dates)
                forecast_line = pd.concat([pd.Series([latest_close], index=[last_date]), forecast])
                
                plot_df = pd.DataFrame({
                    '실제 과거 주가': history,
                    '🔮 AI 예측 트렌드': forecast_line
                })
                
                st.line_chart(plot_df)

                # 상세 데이터
                st.subheader("📋 최근 데이터 표")
                st.dataframe(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10).style.format("{:,.0f}"))

        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
else:
    st.info("👈 왼쪽 사이드바에서 종목명을 검색하고 실행 버튼을 클릭하세요!")
