import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta
import numpy as np

# 1. 라이브 갱신 설정 (20초 자동 새로고침)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=20000, key="live_refresh")
except ImportError:
    st.sidebar.error("💡 'pip install streamlit-autorefresh'가 필요합니다.")

# [제5원칙] 화면 효율 극대화 및 버전 업데이트
st.set_page_config(page_title="미국 주식 시그니처 터미널 v26.4.24.13", layout="wide", initial_sidebar_state="expanded")

# 미국 시장 상태 판별 함수 (타임존 에러 해결 버전)
def get_us_market_status():
    # [🛡️ 타임존 성역] 서버(UTC)에 관계없이 한국 시간(KST)으로 강제 고정
    now_utc = datetime.utcnow()
    now_kst = now_utc + timedelta(hours=9) 
    
    weekday = now_kst.weekday()
    hour, minute = now_kst.hour, now_kst.minute
    curr_time = hour + minute / 60.0
    
    if weekday >= 5: return "⚪ 시장 마감 (주말)"
    
    # 한국 시간 기준 마켓 타임라인 (마스터 규격 엄수)
    if 10.0 <= curr_time < 17.0: return "☀️ 데이마켓"
    elif 17.0 <= curr_time < 22.5: return "🌅 프리마켓"
    elif curr_time >= 22.5 or curr_time < 5.0: return "🟢 정규장"
    else: return "⚪ 시장 마감"

# 2. 통합 CSS 스타일링 (블러 제거 및 마스터 성역 보존)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    
    /* [🛡️ 블러 박멸 로직] */
    [data-stale="true"] { opacity: 1 !important; filter: none !important; transition: none !important; }
    [data-stale="true"] * { opacity: 1 !important; filter: none !important; }

    .main .block-container { padding-top: 0.2rem !important; padding-bottom: 0rem !important; max-width: 98% !important; }
    .main-title { font-size: 2.5rem !important; font-weight: 800 !important; margin-top: -75px !important; margin-bottom: 5px !important; color: #ffffff; letter-spacing: -1px; }

    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] .stRadio p { font-size: 1.55rem !important; font-weight: 800 !important; padding: 10px 0px !important; }
    .section-header { font-size: 1.4rem !important; font-weight: 700 !important; margin-top: 2px !important; margin-bottom: 10px !important; color: #ffffff; }
    
    /* 🔍 버튼 디자인 성역 (222px) */
    div.stButton { width: 100% !important; display: flex !important; }
    button[kind="primary"] {
        width: 100% !important; height: 222px !important; 
        background-color: rgba(128, 128, 128, 0.1) !important; border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 16px !important; margin: 0 !important; color: #fff !important;
    }
    button[kind="primary"]:hover { background-color: rgba(52, 199, 89, 0.2) !important; border-color: #34c759 !important; }
    button[kind="primary"] p { font-size: 2.8rem !important; margin: 0 !important; }

    .custom-card { background-color: rgba(128, 128, 128, 0.1); border-radius: 16px; padding: 22px 20px; display: flex; flex-direction: column; height: 135px; justify-content: center; border: 1px solid rgba(128, 128, 128, 0.1); margin-bottom: 10px; }
    .metric-val { font-size: 2.1rem !important; font-weight: 700; color: #ffffff; line-height: 2.8rem; white-space: nowrap; }
    .wide-mini-card { background-color: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.05); border-radius: 12px; padding: 0 25px; margin-top: 10px; display: flex; align-items: center; height: 75px; }
    .wide-mini-card-label { color:#aaa; font-size:1.05rem; font-weight:600; margin-right:15px; }

    /* [🛡️ 콤팩트 성역] 32px */
    [data-testid="column"] div[data-baseweb="select"], [data-testid="column"] div[data-testid="stTextInput"] > div:first-child {
        background-color: rgba(128, 128, 128, 0.1) !important; border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 10px !important; height: 32px !important; display: flex !important; align-items: center !important;
    }
    [data-testid="column"] input { height: 32px !important; text-align: center !important; background: transparent !important; color: white !important; border: none !important; }
    [data-testid="column"] div[data-baseweb="select"] * { color: #ffffff !important; font-weight: 700 !important; font-size: 0.9rem !important; text-align: center !important; }

    .detail-header-text { font-size: 1.35rem !important; font-weight: 700; color: #ffffff; padding-bottom: 12px; margin-top: 35px !important; margin-bottom: 15px !important; border-bottom: 1px solid rgba(255,255,255,0.08); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.95rem !important; color: #ddd; }
    .custom-table td { padding: 12px 15px; border-bottom: 1px solid rgba(128, 128, 128, 0.08); }
    .pos-val { color: #34c759 !important; font-weight: 600; } 
    .neg-val { color: #ff3b30 !important; font-weight: 600; }
    .market-status-badge { background-color: rgba(128, 128, 128, 0.1); border-radius: 8px; padding: 10px; margin-bottom: 10px; text-align: center; font-size: 1rem; font-weight: 700; color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.05); }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 엔진 (KeyError 및 배포 환경 최적화)
DB_FILE = "portfolio.csv"
def load_data():
    # 기본 구조 보장 (KeyError 방지용)
    default_df = pd.DataFrame(columns=["Ticker", "Price", "Quantity"])
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df = df.rename(columns={'ticker': 'Ticker', 'price': 'Price', 'quantity': 'Quantity', '평단가': 'Price', '수량': 'Quantity'})
            # 필요한 열이 없으면 기본 열 추가
            for col in ["Ticker", "Price", "Quantity"]:
                if col not in df.columns: df[col] = 0 if col != "Ticker" else "N/A"
            return df[["Ticker", "Price", "Quantity"]]
        except: return default_df
    return default_df

def save_data(df): df.to_csv(DB_FILE, index=False)

def render_metric_card(label, val_fmt, sub_fmt, color):
    card_html = f"""<div class="custom-card"><div style="color:#aaa; font-size:0.95rem;">{label}</div><div class="metric-val">{val_fmt}</div><div style="color: {color}; font-size:0.95rem;">{sub_fmt}</div></div>"""
    st.markdown(card_html, unsafe_allow_html=True)

@st.cache_data(ttl=10, show_spinner=False)
def get_market_bulk_data():
    tickers = {
        '나스닥': '^IXIC', 'S&P500': '^GSPC', '다우존스': '^DJI', 
        '미 국채 10년물': '^TNX', '미 국채 2년물': '^IRX', '달러인덱스': 'DX-Y.NYB', 
        '반도체': '^SOX', 'VIX': '^VIX', '금': 'GC=F', '오일': 'CL=F', 
        '비트코인': 'BTC-USD', '이더리움': 'ETH-USD', 
        'USDKRW': 'USDKRW=X', 'USDEUR': 'USDEUR=X', 'USDJPY': 'USDJPY=X'
    }
    symbol_list = list(tickers.values())
    metrics, fx_rates, charts = {}, {'USD': 1.0}, {}
    krw_pct = 0.0
    try:
        bulk_data = yf.download(symbol_list, period="3mo", group_by='ticker', progress=False).ffill().bfill().fillna(0)
        for name, sym in tickers.items():
            try:
                hist = bulk_data[sym] if len(symbol_list) > 1 else bulk_data
                if hist.empty or 'Close' not in hist: continue
                curr = float(hist['Close'].iloc[-1].item())
                prev = float(hist['Close'].iloc[-2].item())
                if name in ['USDKRW', 'USDEUR', 'USDJPY']:
                    fx_rates[name.replace('USD', '')] = curr if curr != 0 else 1.0
                    if name == 'USDKRW': krw_pct = ((curr - prev) / prev * 100) if prev != 0 else 0.0
                    continue
                metrics[name] = {'val': curr, 'diff': curr - prev, 'pct': ((curr - prev) / prev * 100) if prev != 0 else 0.0}
                charts[name] = hist
            except: pass
    except: pass
    return metrics, charts, fx_rates, krw_pct

@st.cache_data(ttl=600, show_spinner=False)
def get_chart_data(ticker, interval="1d"):
    try:
        tk = yf.Ticker(ticker)
        # [🛡️ 차트 끊김 해결 성역] 2y 확보
        p = "2y" if interval == "1d" else "5y" if interval == "1wk" else "max"
        hist = tk.history(period=p, interval=interval)
        if hist.empty: return pd.DataFrame(), {}
        if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
        for w in [5, 30, 60, 120, 200]: hist[f'MA{w}'] = hist['Close'].rolling(window=w).mean()
        h9, l9 = hist['High'].rolling(9).max(), hist['Low'].rolling(9).min()
        hist['Tenkan'] = (h9 + l9) / 2
        h26, l26 = hist['High'].rolling(26).max(), hist['Low'].rolling(26).min()
        hist['Kijun'] = (h26 + l26) / 2
        hist['SpanA'] = ((hist['Tenkan'] + hist['Kijun']) / 2).shift(26)
        h52, l52 = hist['High'].rolling(52).max(), hist['Low'].rolling(52).min()
        hist['SpanB'] = ((h52 + l52) / 2).shift(26)
        return hist.fillna(0), tk.info
    except: return pd.DataFrame(), {}

# 4. 메뉴 구성
st.sidebar.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>미국 주식 터미널</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("", ["📍 시장 주요 지표", "💰 내 자산 관리", "📊 종목 정밀 분석"], label_visibility="collapsed")

market_metrics, market_charts, fx_rates, krw_pct = get_market_bulk_data()

if menu == "📍 시장 주요 지표":
    st.markdown('<div class="main-title">📍 시장 주요 지표</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📈 미국 3대 지수</div>', unsafe_allow_html=True)
    c_idx = st.columns(3)
    for i, name in enumerate(['나스닥', 'S&P500', '다우존스']):
        with c_idx[i]:
            if name in market_metrics:
                m = market_metrics[name]
                render_metric_card(name, f"{m['val']:,.0f}", f"{m['diff']:+.1f} ({m['pct']:+.1f}%)", "#34c759" if m['diff']>0 else "#ff3b30")
                fig = go.Figure(data=[go.Candlestick(x=market_charts[name].index, open=market_charts[name]['Open'], high=market_charts[name]['High'], low=market_charts[name]['Low'], close=market_charts[name]['Close'], increasing_line_color='#34c759', decreasing_line_color='#ff3b30')])
                fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=180, xaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', showlegend=False, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('<div class="section-header" style="margin-top:20px !important;">📊 매크로 지표</div>', unsafe_allow_html=True)
    m_keys = ['미 국채 10년물', '미 국채 2년물', '달러인덱스', '반도체', 'VIX', '금', '오일', 'USDKRW', '비트코인', '이더리움']
    macro_cols = st.columns(5)
    for i, key in enumerate(m_keys):
        with macro_cols[i % 5]:
            if key == "USDKRW": render_metric_card("실시간 환율", f"₩{fx_rates.get('KRW', 1350):,.0f}", f"{krw_pct:+.1f}%", "#34c759" if krw_pct > 0 else "#ff3b30")
            elif key in market_metrics:
                m = market_metrics[key]
                v_f = f"{m['val']:.2f}%" if '국채' in key else f"${m['val']:,.0f}"
                render_metric_card(key, v_f, f"{m['pct']:+.1f}%", "#34c759" if m['diff']>0 else "#ff3b30")

elif menu == "💰 내 자산 관리":
    portfolio_df = load_data()
    st.markdown('<div class="main-title">💰 내 자산 관리</div>', unsafe_allow_html=True)
    c_h, c_s = st.columns([9.3, 0.7])
    with c_h: st.markdown('<div class="section-header">💳 내 자산 포트폴리오 요약</div>', unsafe_allow_html=True)
    with c_s: st.session_state.currency = st.selectbox("", ["USD", "KRW", "EUR", "JPY"], index=0, label_visibility="collapsed")
    cur = st.session_state.get('currency', 'USD'); rate = fx_rates.get(cur, 1.0); sym = {'USD': '$', 'KRW': '₩', 'EUR': '€', 'JPY': '¥'}[cur]
    
    t_v, t_i, t_p, t_d, r_l = 0.0, 0.0, 0.0, 0.0, []
    if not portfolio_df.empty:
        tk_list = portfolio_df['Ticker'].tolist()
        p_data = yf.download(tk_list, period="2d", group_by='ticker', progress=False).ffill().fillna(0)
        for _, row in portfolio_df.iterrows():
            try:
                sym_t = row['Ticker']
                hist_t = p_data[sym_t] if len(tk_list) > 1 else p_data
                cp = float(hist_t['Close'].iloc[-1].item())
                pp = float(hist_t['Close'].iloc[-2].item())
                info_t = yf.Ticker(sym_t).info
                target_sector = "원자재" if sym_t in ["SLV", "GLDM"] else info_t.get('sector', '기타')
                val = round(cp * row['Quantity'], 1)
                inv = round(row['Price'] * row['Quantity'], 1)
                prev_val = round(pp * row['Quantity'], 1)
                profit_pct = round(((cp - row['Price']) / row['Price'] * 100) if row['Price'] != 0 else 0.0, 1)
                day_pct = round(((cp - pp) / pp * 100) if pp != 0 else 0.0, 1)
                t_v += val; t_i += inv; t_p += prev_val; t_d += round(float(info_t.get('dividendRate', 0) or 0) * row['Quantity'], 1)
                r_l.append({**row.to_dict(), 'Sector': target_sector, 'Val': val, 'Profit': profit_pct, 'DayPct': day_pct})
            except: pass
    
    t_v_c, t_r_c, t_d_c, d_c_c = t_v * rate, (t_v - t_i) * rate, t_d * rate, (t_v - t_p) * rate
    r_p = round(((t_v - t_i) / t_i * 100) if t_i > 0 else 0, 1)
    d_p = round(((t_v - t_p) / t_p * 100) if t_p > 0 else 0, 1)
    
    c1, c2, c3 = st.columns([4.65, 4.65, 0.7])
    with c1:
        render_metric_card("현재 총 자산 현황", f"{sym}{t_v_c:,.1f}", f"실시간 {cur} 합계", "#888")
        st.markdown(f'<div class="wide-mini-card"><span class="wide-mini-card-label">🔥 총 누적 수익:</span><span style="color:{"#34c759" if t_r_c>=0 else "#ff3b30"}; font-weight:700;">{sym}{t_r_c:,.1f} ({r_p:+.1f}%)</span></div>', unsafe_allow_html=True)
    with c2:
        render_metric_card("연간 예상 배당금 현황", f"{sym}{t_d_c:,.1f}", "세전 연간 합계", "#888")
        st.markdown(f'<div class="wide-mini-card"><span class="wide-mini-card-label">📊 전일 대비 손익:</span><span style="color:{"#34c759" if d_c_c>=0 else "#ff3b30"}; font-weight:700;">{sym}{d_c_c:,.1f} ({d_p:+.1f}%)</span></div>', unsafe_allow_html=True)
    with c3:
        if st.button("🔍", key="unified_btn", type="primary"): st.session_state.show_portfolio_detail = not st.session_state.get('show_portfolio_detail', False)
    
    if st.session_state.get('show_portfolio_detail', False) and r_l:
        st.markdown(f'<div class="detail-header-text">🔍 포트폴리오 통합 상세 분석 ({cur})</div>', unsafe_allow_html=True)
        df_d = pd.DataFrame(r_l); col_p, col_t = st.columns([1.1, 2.4])
        with col_p:
            fig_p = px.pie(df_d, values='Val', names='Sector', hole=0.5, color_discrete_sequence=px.colors.sequential.Greens_r)
            fig_p.update_layout(margin=dict(l=0,r=0,t=20,b=20), height=280, showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_p, use_container_width=True)
        with col_t:
            tb = "<table class='custom-table'><thead><tr><th>종목</th><th>섹터</th><th>수량</th><th>수익률</th><th>평가액</th></tr></thead><tbody>"
            for _, r in df_d.iterrows():
                p_cl = "pos-val" if r['Profit'] > 0 else "neg-val"
                tb += f"<tr><td><b>{r['Ticker']}</b></td><td>{r['Sector']}</td><td>{r['Quantity']:,.1f}</td><td class='{p_cl}'>{r['Profit']:+.1f}%</td><td><b>{sym}{r['Val']*rate:,.1f}</b></td></tr>"
            st.markdown(tb + "</tbody></table>", unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    with st.expander("⚙️ 종목 관리", expanded=portfolio_df.empty):
        e1, e2, e3 = st.columns(3); t_in = e1.text_input("티커").upper(); p_in = e2.number_input("평단가(USD)", 0.0); q_in = e3.number_input("보유수량", 0.0)
        if st.button("내 포트폴리오에 저장"):
            if t_in: save_data(pd.concat([portfolio_df, pd.DataFrame([{'Ticker': t_in, 'Price': p_in, 'Quantity': q_in}])], ignore_index=True)); st.rerun()
        if not portfolio_df.empty:
            del_t = st.selectbox("삭제 종목", portfolio_df['Ticker'].tolist())
            if st.button("삭제"): save_data(portfolio_df[portfolio_df['Ticker'] != del_t]); st.rerun()

    if r_l:
        st.markdown(f'<div class="section-header" style="margin-top:20px !important;">🗺️ 섹터별 자산 비중 & 일일 등락 ({cur})</div>', unsafe_allow_html=True)
        df_tr = pd.DataFrame(r_l); df_tr['Val_Conv'] = df_tr['Val'] * rate
        fig_tr = px.treemap(df_tr, path=[px.Constant("Portfolio"), 'Sector', 'Ticker'], values='Val_Conv', color='DayPct', color_continuous_scale='RdYlGn', color_continuous_midpoint=0, custom_data=['DayPct', 'Val_Conv'])
        fig_tr.update_traces(texttemplate=f"<b>%{{label}}</b><br>{sym}%{{customdata[1]:,.1f}}<br><b>%{{customdata[0]:+.1f}}%</b>", textfont=dict(size=22, color="white"), insidetextfont=dict(size=22))
        fig_tr.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0), height=380, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_tr, use_container_width=True)

elif menu == "📊 종목 정밀 분석":
    st.markdown('<div class="main-title">📊 종목 정밀 분석</div>', unsafe_allow_html=True)
    portfolio = load_data()
    search_col, portfolio_col, interval_col = st.columns([8, 1, 1])
    with search_col: search_ticker = st.text_input("티커 검색", value="", placeholder="티커를 입력해 주세요...", label_visibility="collapsed").upper()
    with portfolio_col: selected_ticker = st.selectbox("보유", ["직접 검색"] + (portfolio['Ticker'].tolist() if not portfolio.empty else []), label_visibility="collapsed")
    with interval_col:
        i_c = st.selectbox("주기", ["일봉", "주봉", "월봉"], index=0, label_visibility="collapsed")
        interval = {"일봉": "1d", "주봉": "1wk", "월봉": "1mo"}[i_c]
    target = selected_ticker if selected_ticker != "직접 검색" else (search_ticker if search_ticker else None)
    if target:
        hist, info = get_chart_data(target, interval=interval)
        if not hist.empty:
            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
            plot_df = hist.iloc[-150:]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(x=plot_df.index, y=np.where(plot_df['SpanA']>=plot_df['SpanB'], plot_df['SpanA'], np.nan), line=dict(width=0), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=np.where(plot_df['SpanA']>=plot_df['SpanB'], plot_df['SpanB'], np.nan), fill='tonexty', fillcolor='rgba(52, 199, 89, 0.18)', line=dict(width=0), name="Yang"), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=np.where(plot_df['SpanA']<plot_df['SpanB'], plot_df['SpanA'], np.nan), line=dict(width=0), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=np.where(plot_df['SpanA']<plot_df['SpanB'], plot_df['SpanB'], np.nan), fill='tonexty', fillcolor='rgba(255, 59, 48, 0.18)', line=dict(width=0), name="Um"), row=1, col=1)
            fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name="Price", increasing_line_color='#34c759', decreasing_line_color='#ff3b30'), row=1, col=1)
            ma_cfg = {'MA5':('#fff59d',1.0), 'MA30':('#ffcc80',1.2), 'MA60':('#ffa726',1.5), 'MA120':('#e53935',1.8), 'MA200':('#7f0000',2.2)}
            for ma, (c, w) in ma_cfg.items(): 
                if ma in plot_df.columns: fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df[ma], line=dict(color=c, width=w), name=ma), row=1, col=1)
            fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['Volume'], marker_color=['#34c759' if r['Open']<r['Close'] else '#ff3b30' for _, r in plot_df.iterrows()]), row=2, col=1)
            fig.update_layout(height=650, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            dy_raw = info.get('dividendYield') or info.get('trailingAnnualDividendYield')
            div_fmt = f"{(dy_raw * 100 if dy_raw and dy_raw < 1.0 else dy_raw or 0):.2f}%" if dy_raw else "0.00%"
            st.markdown(f'<div class="detail-header-text">📊 {info.get("shortName", target)} 기업 핵심 지표</div>', unsafe_allow_html=True)
            # [🛡️ 지표 레이아웃 성역]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("시가총액", f"${info.get('marketCap', 0)/1e9:.1f}B")
            m2.metric("현재 주가", f"${hist['Close'].iloc[-1]:,.2f}") 
            m3.metric("P/E Ratio", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A") 
            m4.metric("EPS (TTM)", f"${info.get('trailingEps', 0):.2f}")
            m5, m6, m7, m8 = st.columns(4)
            m5.metric("52주 최고가", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")
            m6.metric("52주 최저가", f"${info.get('fiftyTwoWeekLow', 0):,.2f}")
            m7.metric("평균 거래량", f"{info.get('averageVolume', 0)/1e6:.1f}M")
            m8.metric("배당률", div_fmt) 
    else: st.info("ℹ️ 분석할 티커를 상단 검색창에 입력해 주세요.")

# 5. 하단 고정 UI
st.sidebar.markdown('<div style="min-height: 40vh;"></div>', unsafe_allow_html=True)
st.sidebar.markdown(f'<div class="market-status-badge">{get_us_market_status()}</div>', unsafe_allow_html=True)
st.sidebar.divider()
st.sidebar.markdown(f"<div style='text-align: center; color: #888; font-size: 0.95rem; font-weight: 600;'>v26.4.24.13 | {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)
