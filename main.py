                                   
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
