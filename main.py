import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="국내 유망 주식 발굴기",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 국내 대표 우량주 상승 잠재력 분석기")
st.markdown("""
이 프로그램은 시가총액 상위 주요 국내 주식들의 최근 데이터를 수집하여, 
**기술적 지표(골든크로스, RSI)**를 바탕으로 단기적으로 상승 잠재력이 있는 종목을 선별해 줍니다.
* **추천 기준:** 단기 이동평균선이 장기 이동평균선을 상향 돌파하려 하거나, RSI가 과매도 구간에서 반등하는 종목에 높은 점수를 부여합니다.
* ⚠️ **주의:** 기술적 분석에 기반한 확률적 추정이므로 실제 투자 시에는 기업의 기본적 가치(재무제표) 및 뉴스를 함께 확인해야 합니다.
""")

# 국내 주요 주식 리스트 (KOSPI 시총 상위 및 주요 KOSDAQ)
target_stocks = {
    '삼성전자': '005930.KS',
    'SK하이닉스': '000660.KS',
    'LG에너지솔루션': '373220.KS',
    '삼성바이오로직스': '207940.KS',
    '현대차': '005380.KS',
    '기아': '000270.KS',
    '셀트리온': '068270.KS',
    'POSCO홀딩스': '005490.KS',
    'NAVER': '035420.KS',
    '카카오': '035720.KS',
    '에코프로비엠': '247540.KQ',
    '알테오젠': '196170.KQ'
}

# RSI 계산 함수
def calculate_rsi(data, periods=14):
    close_delta = data['Close'].diff()
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    rsi = ma_up / ma_down
    rsi = 100 - (100 / (1 + rsi))
    return rsi

if st.button("🔍 상승 유망 종목 분석 시작", type="primary"):
    with st.spinner("데이터를 수집하고 알고리즘을 분석 중입니다. 잠시만 기다려주세요..."):
        
        end_date = datetime.today()
        start_date = end_date - timedelta(days=120) # 최근 4개월 데이터
        
        results = []
        
        # Streamlit 프로그레스 바
        progress_text = "종목 스캔 중..."
        my_bar = st.progress(0, text=progress_text)
        
        total_stocks = len(target_stocks)
        
        for i, (name, ticker) in enumerate(target_stocks.items()):
            try:
                # 데이터 다운로드
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
                
                # MultiIndex 오류 방지
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                if len(df) < 50:
                    continue
                    
                # 지표 계산
                df['MA5'] = df['Close'].rolling(window=5).mean()
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA60'] = df['Close'].rolling(window=60).mean()
                df['RSI'] = calculate_rsi(df)
                
                # 최신 값 추출
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                
                current_price = float(latest['Close'])
                ma5 = float(latest['MA5'])
                ma20 = float(latest['MA20'])
                rsi = float(latest['RSI'])
                
                # 상승 잠재력 평가 알고리즘 (Scoring)
                score = 0
                signal_msg = []
                
                # 1. 이동평균선 정배열 또는 골든크로스 임박
                if ma5 > ma20:
                    score += 30
                    signal_msg.append("단기 상승세(MA5>MA20)")
                elif prev['MA5'] <= prev['MA20'] and ma5 > ma20:
                    score += 50
                    signal_msg.append("🔥골든크로스 발생")
                elif ma20 > ma5 and (ma20 - ma5) / ma20 < 0.02: # 2% 이내로 좁혀짐
                    score += 20
                    signal_msg.append("골든크로스 임박")
                    
                # 2. RSI 분석 (과매도 후 반등)
                if rsi < 30:
                    score += 10
                    signal_msg.append("과매도 구간(바닥)")
                elif 30 <= rsi <= 50 and rsi > float(prev['RSI']):
                    score += 30
                    signal_msg.append("바닥 확인 및 반등 중")
                elif 50 < rsi <= 70:
                    score += 20
                    signal_msg.append("안정적 상승세")
                else:
                    score -= 10
                    signal_msg.append("과매수 구간(조정 주의)")
                    
                results.append({
                    '종목명': name,
                    '현재가': f"{int(current_price):,}원",
                    'RSI 지수': round(rsi, 1),
                    '상승 잠재력 점수': score,
                    'AI 분석 시그널': " / ".join(signal_msg)
                })
                
            except Exception as e:
                pass # 에러 발생 종목은 스킵
            
            # 진행률 업데이트
            my_bar.progress((i + 1) / total_stocks, text=f"분석 중: {name}")
            
        # 스캔 완료
        my_bar.empty()
        st.success("✅ 종목 스캔이 완료되었습니다! 점수가 높은 순으로 정렬된 결과를 확인하세요.")
        
        # 결과를 데이터프레임으로 변환 및 정렬
        if results:
            result_df = pd.DataFrame(results)
            result_df = result_df.sort_values(by='상승 잠재력 점수', ascending=False).reset_index(drop=True)
            
            # 시각적인 테이블 출력
            st.dataframe(
                result_df,
                column_config={
                    "상승 잠재력 점수": st.column_config.ProgressColumn(
                        "상승 잠재력 점수 (100점 만점)",
                        help="점수가 높을수록 단기 상승 확률이 높다고 평가됩니다.",
                        format="%d점",
                        min_value=0,
                        max_value=100,
                    ),
                    "RSI 지수": st.column_config.NumberColumn(
                        "RSI 지수",
                        help="30 이하면 과매도(저평가), 70 이상이면 과매수(고평가) 상태입니다."
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.info("💡 팁: 'AI 분석 시그널'에 '골든크로스'나 '반등 중'이 뜬 종목들의 차트를 기존 대시보드 탭에 입력하여 자세히 분석해 보세요.")
        else:
            st.warning("분석 가능한 종목 데이터를 가져오지 못했습니다.")

else:
    st.info("👆 위 버튼을 눌러 시가총액 상위 종목들의 현재 상승 잠재력을 스캔해 보세요!")
