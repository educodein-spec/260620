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
      {'Name': '삼성전자', 'Code': '005930', 'Market': 'KOSPI', 'Sector': '반도체', 'Industry': '반도체, 스마트폰, 가전'},
        {'Name': 'SK하이닉스', 'Code': '000660', 'Market': 'KOSPI', 'Sector': '반도체', 'Industry': '메모리 반도체 (DRAM, HBM)'},
        {'Name': 'NAVER', 'Code': '035420', 'Market': 'KOSPI', 'Sector': 'IT/플랫폼', 'Industry': '인터넷 포털, AI, 커머스'},
        {'Name': '카카오', 'Code': '035720', 'Market': 'KOSPI', 'Sector': 'IT/플랫폼', 'Industry': '모바일 메신저, 플랫폼'},
        {'Name': '삼성SDS', 'Code': '018260', 'Market': 'KOSPI', 'Sector': 'IT/서비스', 'Industry': 'IT 서비스, 클라우드'},
        {'Name': 'LG에너지솔루션', 'Code': '373220', 'Market': 'KOSPI', 'Sector': '2차전지', 'Industry': '2차전지 배터리 셀'},
        {'Name': 'POSCO홀딩스', 'Code': '005490', 'Market': 'KOSPI', 'Sector': '철강/소재', 'Industry': '철강, 2차전지 소재'},
        {'Name': 'LG화학', 'Code': '051910', 'Market': 'KOSPI', 'Sector': '화학/소재', 'Industry': '2차전지 소재, 기초화학'},
        {'Name': '삼성SDI', 'Code': '006400', 'Market': 'KOSPI', 'Sector': '2차전지', 'Industry': '2차전지, 전자재료'},
        {'Name': '포스코퓨처엠', 'Code': '003670', 'Market': 'KOSPI', 'Sector': '2차전지', 'Industry': '2차전지 양/음극재'},
        {'Name': 'SK이노베이션', 'Code': '096770', 'Market': 'KOSPI', 'Sector': '정유/화학', 'Industry': '정유, 2차전지(SK온)'},
        {'Name': '삼성바이오로직스', 'Code': '207940', 'Market': 'KOSPI', 'Sector': '바이오', 'Industry': '바이오 의약품 위탁생산(CDMO)'},
        {'Name': '셀트리온', 'Code': '068270', 'Market': 'KOSPI', 'Sector': '바이오', 'Industry': '바이오시밀러 신약'},
        {'Name': 'SK바이오팜', 'Code': '326030', 'Market': 'KOSPI', 'Sector': '바이오', 'Industry': '중추신경계 신약 개발'},
        {'Name': '현대차', 'Code': '005380', 'Market': 'KOSPI', 'Sector': '자동차', 'Industry': '글로벌 완성차'},
        {'Name': '기아', 'Code': '000270', 'Market': 'KOSPI', 'Sector': '자동차', 'Industry': '글로벌 완성차'},
        {'Name': '현대모비스', 'Code': '012330', 'Market': 'KOSPI', 'Sector': '자동차', 'Industry': '자동차 핵심 부품'},
        {'Name': 'KB금융', 'Code': '105560', 'Market': 'KOSPI', 'Sector': '금융', 'Industry': '국내 1위 금융지주'},
        {'Name': '신한지주', 'Code': '055550', 'Market': 'KOSPI', 'Sector': '금융', 'Industry': '종합 금융지주'},
        {'Name': '하나금융지주', 'Code': '086790', 'Market': 'KOSPI', 'Sector': '금융', 'Industry': '종합 금융지주'},
        {'Name': '삼성물산', 'Code': '028260', 'Market': 'KOSPI', 'Sector': '지주사', 'Industry': '삼성그룹 실질적 지주사'},
        {'Name': '삼성생명', 'Code': '032830', 'Market': 'KOSPI', 'Sector': '금융', 'Industry': '생명보험 1위'},
        {'Name': '메리츠금융지주', 'Code': '138040', 'Market': 'KOSPI', 'Sector': '금융', 'Industry': '증권/화재 중심 금융지주'},
        {'Name': '카카오뱅크', 'Code': '323410', 'Market': 'KOSPI', 'Sector': '금융', 'Industry': '인터넷 전문은행'},
        {'Name': 'HD현대중공업', 'Code': '329180', 'Market': 'KOSPI', 'Sector': '조선', 'Industry': '글로벌 1위 조선사'},
        {'Name': '한화에어로스페이스', 'Code': '012450', 'Market': 'KOSPI', 'Sector': '방산/항공', 'Industry': '항공우주, K-방산'},
        {'Name': '한국전력', 'Code': '015760', 'Market': 'KOSPI', 'Sector': '유틸리티', 'Industry': '전력 인프라 공기업'},
        {'Name': 'HMM', 'Code': '011200', 'Market': 'KOSPI', 'Sector': '해운', 'Industry': '국내 최대 컨테이너 해운사'},
        {'Name': '현대건설', 'Code': '000720', 'Market': 'KOSPI', 'Sector': '건설', 'Industry': '종합 건설사'},
        {'Name': '대한항공', 'Code': '003490', 'Market': 'KOSPI', 'Sector': '항공/운수', 'Industry': '국내 1위 항공사'},
        
        # --- KOSDAQ (20종목) ---
        {'Name': '에코프로비엠', 'Code': '247540', 'Market': 'KOSDAQ', 'Sector': '2차전지', 'Industry': '양극재 제조 세계 1위 수준'},
        {'Name': '에코프로', 'Code': '086520', 'Market': 'KOSDAQ', 'Sector': '2차전지', 'Industry': '2차전지 소재 지주사'},
        {'Name': '엔켐', 'Code': '348370', 'Market': 'KOSDAQ', 'Sector': '2차전지', 'Industry': '전해액 제조 전문'},
        {'Name': '엘앤에프', 'Code': '066970', 'Market': 'KOSDAQ', 'Sector': '2차전지', 'Industry': '하이니켈 양극재'},
        {'Name': '알테오젠', 'Code': '196170', 'Market': 'KOSDAQ', 'Sector': '바이오', 'Industry': '피하주사 변환 플랫폼'},
        {'Name': 'HLB', 'Code': '028300', 'Market': 'KOSDAQ', 'Sector': '바이오', 'Industry': '표적항암제 등 혁신 신약'},
        {'Name': '셀트리온제약', 'Code': '068760', 'Market': 'KOSDAQ', 'Sector': '바이오/제약', 'Industry': '케미컬 의약품 및 유통'},
        {'Name': '휴젤', 'Code': '145020', 'Market': 'KOSDAQ', 'Sector': '바이오/제약', 'Industry': '보툴리눔 톡신(보톡스) 1위'},
        {'Name': '클래시스', 'Code': '214150', 'Market': 'KOSDAQ', 'Sector': '의료기기', 'Industry': '미용 의료기기 (슈링크)'},
        {'Name': '삼천당제약', 'Code': '000250', 'Market': 'KOSDAQ', 'Sector': '바이오/제약', 'Industry': '안과용 의약품 및 바이오시밀러'},
        {'Name': '리가켐바이오', 'Code': '141080', 'Market': 'KOSDAQ', 'Sector': '바이오', 'Industry': 'ADC(항체-약물 접합체) 기술'},
        {'Name': '파마리서치', 'Code': '214450', 'Market': 'KOSDAQ', 'Sector': '제약/의료', 'Industry': '재생의학 (리쥬란 등)'},
        {'Name': '리노공업', 'Code': '058470', 'Market': 'KOSDAQ', 'Sector': '반도체장비', 'Industry': '반도체 테스트 소켓 1위'},
        {'Name': 'HPSP', 'Code': '403870', 'Market': 'KOSDAQ', 'Sector': '반도체장비', 'Industry': '고압 수소 어닐링 장비 독점'},
        {'Name': '이오테크닉스', 'Code': '039030', 'Market': 'KOSDAQ', 'Sector': '반도체장비', 'Industry': '반도체 레이저 장비'},
        {'Name': '솔브레인', 'Code': '357780', 'Market': 'KOSDAQ', 'Sector': 'IT소재', 'Industry': '반도체/디스플레이 화학 소재'},
        {'Name': '동진쎄미켐', 'Code': '005290', 'Market': 'KOSDAQ', 'Sector': 'IT소재', 'Industry': '반도체 감광액(PR)'},
        {'Name': 'JYP Ent.', 'Code': '035900', 'Market': 'KOSDAQ', 'Sector': '엔터테인먼트', 'Industry': '대형 K-POP 기획사'},
        {'Name': '에스엠', 'Code': '041510', 'Market': 'KOSDAQ', 'Sector': '엔터테인먼트', 'Industry': '글로벌 K-POP 기획사'},
        {'Name': '펄어비스', 'Code': '263750', 'Market': 'KOSDAQ', 'Sector': '게임', 'Industry': '대형 게임 개발 (검은사막)'}
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
