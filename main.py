import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="한국 주식 AI 예측 (종목명 검색)", page_icon="🔎", layout="wide")

# --- 핵심 수정: KRX 서버 차단 대비 예외 처리 및 하드코딩 ---
@st.cache_data(show_spinner=False)
def load_korea_stocks():
    # 해외 클라우드 서버 접속 차단 시 사용할 주요 대표 종목 리스트 (백업용)
    fallback_data = pd.DataFrame([
        {'Name': '삼성전자', 'Code': '005930', 'Market': 'KOSPI'},
        {'Name': 'SK하이닉스', 'Code': '000660', 'Market': 'KOSPI'},
        {'Name': 'LG에너지솔루션', 'Code': '373220', 'Market': 'KOSPI'},
        {'Name': '삼성바이오로직스', 'Code': '207940', 'Market': 'KOSPI'},
        {'Name': '현대차', 'Code': '005380', 'Market': 'KOSPI'},
        {'Name': '기아', 'Code': '000270', 'Market': 'KOSPI'},
        {'Name': '셀트리온', 'Code': '068270', 'Market': 'KOSPI'},
        {'Name': 'POSCO홀딩스', 'Code': '005490', 'Market': 'KOSPI'},
        {'Name': 'NAVER', 'Code': '035420', 'Market': 'KOSPI'},
        {'Name': '카카오', 'Code': '035720', 'Market': 'KOSPI'},
        {'Name': '에코프로비엠', 'Code': '247540', 'Market': 'KOSDAQ'},
        {'Name': '에코프로', 'Code': '086520', 'Market': 'KOSDAQ'},
        {'Name': '알테오젠', 'Code': '196170', 'Market': 'KOSDAQ'},
        {'Name': '엔켐', 'Code': '348370', 'Market': 'KOSDAQ'}
    ])
    try:
        df = fdr.StockListing('KRX')
        return df[['Name', 'Code', 'Market']], True
    except:
        return fallback_data, False

stocks_df, is_live = load_korea_stocks()
stock_names = stocks_df['Name'].tolist()
# ----------------------------------------------------------------

st.title("🔎 한국 주식 가격 예측 (종목명 검색)")

# 차단 안내 메시지 (안전하게 우회되었음을 알림)
if not is_live:
    st.warning("⚠️ 현재 스트림릿 클라우드(해외 서버) 보안 정책으로 인해 한국거래소 전체 종목 검색이 제한되어, 주요 대표 종목 리스트로 대체되었습니다. 목록에 없는 종목은 사이드바에 코드를 직접 입력해 주세요.")

st.sidebar.header("⚙️ 종목 검색 및 설정")

# 1. 종목명 선택
default_index = stock_names.index('삼성전자') if '삼성전자' in stock_names else 0
selected_name = st.sidebar.selectbox("🔍 종목명을 검색하세요 (주요 종목)", stock_names, index=default_index)

# 2. 직접 입력 기능 추가 (목록에 없을 경우 대비)
manual_ticker = st.sidebar.text_input("💡 목록에 없나요? 종목 코드를 직접 입력하세요 (예: 035420.KS)", value="")

today = datetime.today()
start_date = st.sidebar.date_input("데이터 시작일", today - timedelta(days=365))
end_date = st.sidebar.date_input("데이터 종료일", today)
pred_days = st.sidebar.slider("AI 예측 기간 (거래일)", 1, 20, 5)

# 티커 결정 로직
if manual_ticker.strip():
    ticker_symbol = manual_ticker.strip().upper()
    display_name = ticker_symbol
else:
    display_name = selected_name
    stock_info = stocks_df[stocks_df['Name'] == selected_name].iloc[0]
    raw_code = stock_info['Code']
    market = stock_info['Market']
    ticker_symbol = f"{raw_code}.KQ" if 'KOSDAQ' in market else f"{raw_code}.KS"

if st.sidebar.button("데이터 분석 및 예측 실행"):
    with st.spinner(f"'{display_name}' 데이터를 분석 중입니다..."):
        try:
            df = yf.download(ticker_symbol, start=start_date, end=end_date, progress=False)

            if df.empty:
                st.error("데이터를 불러오지 못했습니다. 종목 코드가 정확한지 확인해 주세요.")
            else:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA50'] = df['Close'].rolling(window=50).mean()

                latest_close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                price_diff = latest_close - prev_close
                pct_change = (price_diff / prev_close) * 100

                col1, col2, col3 = st.columns(3)
                col1.metric(f"현재가 ({display_name})", f"{int(latest_close):,}원", f"{price_diff:+,.0f} ({pct_change:+.2f}%)")
                
                recent_30 = df['Close'].tail(30).values
                if recent_30.ndim > 1:
                    recent_30 = recent_30.flatten()
                    
                x = np.arange(len(recent_30))
                slope, intercept = np.polyfit(x, recent_30, 1)
                
                future_x = np.arange(len(recent_30), len(recent_30) + pred_days)
                future_preds = slope * future_x + intercept
                final_pred = future_preds[-1]
                
                pred_diff = final_pred - latest_close
                pred_pct = (pred_diff / latest_close) * 100
                
                col2.metric(f"AI {pred_days}일 뒤 예측가", f"{int(final_pred):,}원", 
                           f"{pred_diff:+,.0f} ({pred_pct:+.2f}%)", delta_color="normal" if pred_diff >= 0 else "inverse")
                
                col3.metric("종목 코드 (Ticker)", ticker_symbol)

                st.subheader(f"📊 {display_name} 주가 추이 및 예측선")
                
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

        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
else:
    st.info("👈 왼쪽 사이드바에서 종목명을 선택하거나 코드를 입력하고 실행 버튼을 클릭하세요!")
