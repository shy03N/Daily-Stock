import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import hashlib

# 1. 라이브 갱신 설정 (15초 자동 새로고침)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="live_refresh")
except ImportError:
    st.sidebar.error("💡 'pip install streamlit-autorefresh'가 필요합니다.")

# 페이지 설정
st.set_page_config(page_title="미국 주식 시그니처 터미널 v26.4.22.15", layout="wide", initial_sidebar_state="expanded")

# 2. 통합 CSS 스타일링 (여백 압축, 블러 박멸, 일체형 UI)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    
    /* 갱신 시 블러 무력화 */
    [data-stale="true"], [data-stale="false"], 
    [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
        opacity: 1 !important; filter: none !important; transition: none !important;
    }

    /* 화면 상단 극한 밀착 (Lift-up) */
    .main .block-container { 
        padding-top: 0.2rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 98% !important; 
    }

    .main-title {
        font-size: 2.5rem !important; font-weight: 800 !important;
        margin-top: -75px !important; margin-bottom: 10px !important;
        color: #ffffff; letter-spacing: -1px;
    }

    /* 사이드바 메뉴 폰트 확대 및 점 제거 */
    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] .stRadio p {
        font-size: 1.55rem !important; 
        font-weight: 800 !important;
        padding: 12px 0px !important;
    }

    .section-header {
        font-size: 1.4rem !important; font-weight: 700 !important;
        margin-top: 2px !important; margin-bottom: 10px !important;
        color: #ffffff;
    }
    
    /* 🔍 버튼 디자인: 우측 끝 벽면 밀착 */
    div.stButton { width: 100% !important; display: flex !important; }
    button[kind="primary"] {
        width: 100% !important; height: 222px !important; 
        background-color: rgba(128, 128, 128, 0.1) !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 16px !important; margin: 0 !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        color: #fff !important; transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover { background-color: rgba(52, 199, 89, 0.2) !important; border-color: #34c759 !important; }
    button[kind="primary"] p { font-size: 2.8rem !important; margin: 0 !important; }

    [data-testid="column"] { padding-left: 4px !important; padding-right: 4px !important; }

    /* 통합 카드 디자인 */
    .custom-card {
        background-color: rgba(128, 128, 128, 0.1); 
        border-radius: 16px; padding: 22px 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        display: flex; flex-direction: column; height: 135px; justify-content: center;
        border: 1px solid rgba(128, 128, 128, 0.1);
    }
    .metric-val { font-size: 2.1rem !important; font-weight: 700; color: #ffffff; display: flex; overflow: hidden; height: 2.8rem; line-height: 2.8rem; white-space: nowrap; }

    .wide-mini-card {
        background-color: rgba(128, 128, 128, 0.1); 
        border: 1px solid rgba(128, 128, 128, 0.05);
        border-radius: 12px; padding: 0 25px; 
        margin-top: 10px; margin-bottom: 5px;
        display: flex; flex-direction: row; align-items: center; width: 100%; height: 75px; box-sizing: border-box;
    }
    .wide-mini-card-label { color:#aaa; font-size:1.05rem; font-weight:600; margin-right:15px; }

    /* 상세 분석 텍스트 디자인 (상자 제거 버전) */
    .detail-header-text { 
        font-size: 1.35rem !important; 
        font-weight: 700; 
        color: #ffffff; 
        padding-bottom: 12px;
        margin-top: 25px !important;
        margin-bottom: 15px !important;
        border-bottom: 1px solid rgba(255,255,255,0.08); 
    }
    
    .custom-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.95rem !important; color: #ddd; }
    .custom-table td { padding: 12px 15px; border-bottom: 1px solid rgba(128, 128, 128, 0.08); }
    .pos-val { color: #34c759 !important; font-weight: 600; } 
    .neg-val { color: #ff3b30 !important; font-weight: 600; }

    /* 통화 버튼 정중앙 보정 및 격리 디자인 */
    [data-testid="column"] div[data-baseweb="select"] {
        background-color: rgba(128, 128, 128, 0.1) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 12px !important; height: 38px !important;
        display: flex !important; justify-content: center !important; align-items: center !important;
    }
    [data-testid="column"] div[data-baseweb="select"] > div:first-child { padding-right: 0 !important; justify-content: center !important; }
    [data-testid="column"] div[data-baseweb="select"] svg { display: none !important; }
    [data-testid="column"] div[data-baseweb="select"] * {
        text-align: center !important; font-weight: 700 !important; color: #ffffff !important;
        font-size: 0.95rem !important; line-height: 1 !important; padding: 0 !important;
    }

    :root { --primary-color: #34c759 !important; }
    hr { margin: 1px 0 !important; opacity: 0.02; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 엔진
DB_FILE = "portfolio.csv"
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        return df.rename(columns={'ticker': 'Ticker', 'price': 'Price', 'quantity': 'Quantity', '평단가': 'Price', '수량': 'Quantity'})
    return pd.DataFrame(columns=["Ticker", "Price", "Quantity"])

def save_data(df): df.to_csv(DB_FILE, index=False)

# 롤링 애니메이션 엔진 (사용자님이 만족하신 v26.4.22.3 핵심 로직 그대로)
def create_animated_card_html(label, current_val, formatted_val, sub_str, diff_color, is_int=True):
    uid = hashlib.md5(label.encode()).hexdigest()[:8]
    prev_key = f"prev_metric_{label}"; prev_val = st.session_state.get(prev_key, current_val); st.session_state[prev_key] = current_val
    frac = "0" if is_int else "1"
    js_code = f"""
    var el = document.getElementById('val-{uid}');
    if(el && !el.dataset.animated) {{
        el.dataset.animated = 'true';
        var start = {float(prev_val)}; var end = {float(current_val)};
        var duration = 1800; var startTime = performance.now();
        var finalStr = "{formatted_val}";
        if(Math.abs(start - end) > 0.001) {{
            el.classList.add('is-rolling'); el.style.color = end > start ? '#34c759' : '#ff3b30';
            function update(time) {{
                var elapsed = time - startTime; if(elapsed > duration) elapsed = duration;
                var progress = 1 - Math.pow(1 - (elapsed/duration), 3);
                var current = start + (end - start) * progress;
                if(elapsed < duration) {{ el.style.filter = 'blur(0.5px)'; }} else {{ el.style.filter = 'none'; }}
                var displayNum = current.toLocaleString(undefined, {{ minimumFractionDigits: {frac}, maximumFractionDigits: {frac} }});
                var match = finalStr.match(/([^0-9,.]*)([0-9,.]+)([^0-9,.]*)/);
                if(match) {{ el.innerText = match[1] + displayNum + match[3]; }} else {{ el.innerText = displayNum; }}
                if(elapsed < duration) {{ requestAnimationFrame(update); }}
                else {{ el.innerText = finalStr; setTimeout(() => {{ el.style.color = '#ffffff'; }}, 500); }}
            }}
            requestAnimationFrame(update);
        }} else {{ el.innerText = finalStr; }}
    }}
    """
    js_code_clean = js_code.replace('\n', ' ').replace('"', '&quot;')
    return f"""<div class="custom-card"><div class="metric-title" style="color:#aaa; font-size:0.95rem;">{label}</div><div class="metric-val" id="val-{uid}">{formatted_val}</div><div style="color: {diff_color}; font-size:0.95rem;">{sub_str}</div><img src="x" style="display:none;" onerror="{js_code_clean}"></div>"""

@st.cache_data(ttl=10, show_spinner=False)
def get_market_full_data():
    tickers = {'나스닥': '^IXIC', 'S&P500': '^GSPC', '다우존스': '^DJI', '미 국채 10년물': '^TNX', '미 국채 2년물': '^IRX', '달러인덱스': 'DX-Y.NYB', '반도체': '^SOX', 'VIX': '^VIX', '금': 'GC=F', '오일': 'CL=F', '비트코인': 'BTC-USD', '이더리움': 'ETH-USD', 'USDKRW': 'USDKRW=X', 'USDEUR': 'USDEUR=X', 'USDJPY': 'USDJPY=X'}
    metrics, charts, fx_rates, krw_pct = {}, {}, {'USD': 1.0, 'KRW': 1350.0, 'EUR': 0.92, 'JPY': 150.0}, 0
    for name, tk in tickers.items():
        try:
            data = yf.download(tk, period="3mo", interval="1d", progress=False)
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            if name in ['USDKRW', 'USDEUR', 'USDJPY']:
                cur_key = name.replace('USD', ''); fx_rates[cur_key] = float(data['Close'].iloc[-1].item())
                if name == 'USDKRW' and len(data) >= 2: 
                    curr_krw, prev_krw = float(data['Close'].iloc[-1].item()), float(data['Close'].iloc[-2].item())
                    krw_pct = (curr_krw - prev_krw) / prev_krw * 100
                continue
            curr, prev = float(data['Close'].iloc[-1].item()), float(data['Close'].iloc[-2].item())
            metrics[name] = {'val': curr, 'diff': curr - prev, 'pct': (curr - prev) / prev * 100}; charts[name] = data
        except: pass
    return metrics, charts, fx_rates, krw_pct

@st.cache_data(ttl=10, show_spinner=False)
def get_stock_info(ticker):
    try:
        tk = yf.Ticker(ticker); hist = tk.history(period="2d")
        if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
        curr, prev = float(hist['Close'].iloc[-1].item()), float(hist['Close'].iloc[-2].item())
        return {'price': curr, 'prev_close': prev, 'sector': tk.info.get('sector', '기타'), 'div': float(tk.info.get('dividendRate', 0) or 0)}
    except: return None

@st.cache_data(ttl=600, show_spinner=False)
def get_chart_and_news(ticker):
    try:
        tk = yf.Ticker(ticker); hist = tk.history(period="6mo", interval="1d")
        if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
        return hist, yf.Ticker(ticker).news
    except: return pd.DataFrame(), []

market_metrics, market_charts, fx_rates, krw_pct = get_market_full_data()

# 4. 메뉴 구성
st.sidebar.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>미국 주식 터미널</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("", ["📍 시장 주요 지표", "💰 내 자산 관리", "📊 종목 정밀 분석"], label_visibility="collapsed")

if menu == "📍 시장 주요 지표":
    st.markdown('<div class="main-title">📍 시장 주요 지표</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📈 미국 3대 지수</div>', unsafe_allow_html=True)
    c_idx = st.columns(3)
    for i, name in enumerate(['나스닥', 'S&P500', '다우존스']):
        with c_idx[i]:
            if name in market_metrics:
                m = market_metrics[name]; st.markdown(create_animated_card_html(name, m['val'], f"{m['val']:,.0f}", f"{m['diff']:+.1f} ({m['pct']:+.1f}%)", "#34c759" if m['diff']>0 else "#ff3b30"), unsafe_allow_html=True)
                fig = go.Figure(data=[go.Candlestick(x=market_charts[name].index, open=market_charts[name]['Open'], high=market_charts[name]['High'], low=market_charts[name]['Low'], close=market_charts[name]['Close'], increasing_line_color='#34c759', decreasing_line_color='#ff3b30')])
                fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=180, xaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div class="section-header" style="margin-top:20px !important;">📊 매크로 지표</div>', unsafe_allow_html=True)
    macro_keys = ['미 국채 10년물', '미 국채 2년물', '달러인덱스', '반도체', 'VIX', '금', '오일', 'USDKRW', '비트코인', '이더리움']
    macro_html = '<div class="macro-grid" style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-top:10px;">'
    for key in macro_keys:
        if key == "USDKRW": macro_html += create_animated_card_html("실시간 환율", fx_rates['KRW'], f"₩{fx_rates['KRW']:,.0f}", f"{krw_pct:+.1f}%", "#34c759" if krw_pct > 0 else "#ff3b30")
        elif key in market_metrics:
            m = market_metrics[key]; val_fmt = f"{m['val']:.2f}%" if '국채' in key else f"${m['val']:,.0f}"
            macro_html += create_animated_card_html(key, m['val'], val_fmt, f"{m['pct']:+.1f}%", "#34c759" if m['diff']>0 else "#ff3b30")
    st.markdown(macro_html + '</div>', unsafe_allow_html=True)

elif menu == "💰 내 자산 관리":
    portfolio_df = load_data()
    st.markdown('<div class="main-title">💰 내 자산 관리</div>', unsafe_allow_html=True)
    c_head, c_select = st.columns([9.4, 0.6])
    with c_head: st.markdown('<div class="section-header">💳 내 자산 포트폴리오 요약</div>', unsafe_allow_html=True)
    with c_select: st.session_state.currency = st.selectbox("", ["USD", "KRW", "EUR", "JPY"], index=["USD", "KRW", "EUR", "JPY"].index(st.session_state.get('currency', 'USD')), label_visibility="collapsed")
    
    cur = st.session_state.get('currency', 'USD'); rate = fx_rates.get(cur, 1.0); sym = {'USD': '$', 'KRW': '₩', 'EUR': '€', 'JPY': '¥'}[cur]

    total_v, total_inv, total_prev_day, total_d, res_list = 0, 0, 0, 0, []
    if not portfolio_df.empty:
        for _, row in portfolio_df.iterrows():
            info = get_stock_info(row['Ticker'])
            if info:
                v_usd, p_usd = info['price'] * row['Quantity'], row['Price'] * row['Quantity']
                total_v += v_usd; total_inv += p_usd; total_prev_day += info['prev_close'] * row['Quantity']; total_d += (info['div'] * row['Quantity'])
                res_list.append({**row.to_dict(), 'Sector': info['sector'], 'Val': v_usd, 'Profit': round((info['price'] - row['Price']) / row['Price'] * 100, 1), 'DayPct': round((info['price'] - info['prev_close']) / info['prev_close'] * 100, 1)})

    total_v_conv, total_ret_conv = total_v * rate, (total_v - total_inv) * rate
    total_d_conv, day_chg_conv = total_d * rate, (total_v - total_prev_day) * rate
    ret_pct, day_pct = round(((total_v - total_inv) / total_inv * 100) if total_inv > 0 else 0, 1), round(((total_v - total_prev_day) / total_prev_day * 100) if total_prev_day > 0 else 0, 1)

    c1, c2, c3 = st.columns([4.7, 4.7, 0.6])
    with c1:
        st.markdown(create_animated_card_html("현재 총 자산 현황", total_v_conv, f"{sym}{total_v_conv:,.0f}", f"실시간 {cur} 합계", "#888"), unsafe_allow_html=True)
        st.markdown(f'<div class="wide-mini-card"><span class="wide-mini-card-label">🔥 총 누적 수익:</span><span class="wide-mini-card-value" style="color:{"#34c759" if total_ret_conv>=0 else "#ff3b30"};">{sym}{total_ret_conv:,.0f} ({ret_pct:+.1f}%)</span></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(create_animated_card_html("연간 예상 배당금 현황", total_d_conv, f"{sym}{total_d_conv:,.0f}", "세전 연간 합계", "#888"), unsafe_allow_html=True)
        st.markdown(f'<div class="wide-mini-card"><span class="wide-mini-card-label">📊 전일 대비 손익:</span><span class="wide-mini-card-value" style="color:{"#34c759" if day_chg_conv>=0 else "#ff3b30"};">{sym}{day_chg_conv:,.0f} ({day_pct:+.1f}%)</span></div>', unsafe_allow_html=True)
    with c3:
        if st.button("🔍", key="unified_btn", type="primary"): st.session_state.show_portfolio_detail = not st.session_state.get('show_portfolio_detail', False)

    # 🔥 [v26.4.22.15 핵심] 상자 제거 및 배경 일체형 상세 분석
    if st.session_state.get('show_portfolio_detail', False) and not portfolio_df.empty:
        st.markdown(f'<div class="detail-header-text">🔍 포트폴리오 통합 상세 분석 ({cur})</div>', unsafe_allow_html=True)
        df_display = pd.DataFrame(res_list); col_p, col_t = st.columns([1.1, 2.4])
        with col_p:
            fig_pie = px.pie(df_display, values='Val', names='Sector', hole=0.5, color_discrete_sequence=px.colors.sequential.Greens_r)
            fig_pie.update_layout(margin=dict(l=0,r=0,t=20,b=20), height=280, showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_t:
            table_html = "<table class='custom-table'><thead><tr><th>종목</th><th>섹터</th><th>수량</th><th>수익률</th><th>평가액</th></tr></thead><tbody>"
            for _, r in df_display.iterrows():
                p_cls = "pos-val" if r['Profit'] > 0 else "neg-val"
                table_html += f"<tr><td><b>{r['Ticker']}</b></td><td>{r['Sector']}</td><td>{r['Quantity']:,.1f}</td><td class='{p_cls}'>{r['Profit']:+.1f}%</td><td><b>{sym}{r['Val']*rate:,.0f}</b></td></tr>"
            st.markdown(table_html + "</tbody></table>", unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
    with st.expander("⚙️ 종목 관리 메뉴 (추가/삭제)", expanded=portfolio_df.empty):
        e1, e2, e3 = st.columns(3); t_in = e1.text_input("티커").upper(); p_in = e2.number_input("평단가(USD)", 0.0); q_in = e3.number_input("보유수량", 0.0)
        if st.button("내 포트폴리오에 저장"):
            if t_in: save_data(pd.concat([portfolio_df, pd.DataFrame([{'Ticker': t_in, 'Price': p_in, 'Quantity': q_in}])], ignore_index=True)); st.rerun()
        if not portfolio_df.empty:
            del_t = st.selectbox("삭제 종목", portfolio_df['Ticker'].tolist())
            if st.button("삭제"): save_data(portfolio_df[portfolio_df['Ticker'] != del_t]); st.rerun()

    if not portfolio_df.empty:
        st.markdown('<hr style="margin: 2px 0; opacity: 0.02;">', unsafe_allow_html=True) 
        st.markdown(f'<div class="section-header" style="margin-top:-5px !important; margin-bottom: 5px !important;">🗺️ 섹터별 자산 비중 & 일일 등락 ({cur})</div>', unsafe_allow_html=True)
        df_tree = pd.DataFrame(res_list); df_tree['Val_Conv'] = df_tree['Val'] * rate
        fig_tree = px.treemap(df_tree, path=[px.Constant("Portfolio"), 'Sector', 'Ticker'], values='Val_Conv', color='DayPct', color_continuous_scale='RdYlGn', color_continuous_midpoint=0, custom_data=['DayPct', 'Val_Conv'])
        fig_tree.update_traces(texttemplate=f"<b>%{{label}}</b><br>{sym}%{{customdata[1]:,.0f}}<br><b>%{{customdata[0]:+.1f}}%</b>", textfont=dict(size=22, color="white"), insidetextfont=dict(size=22))
        fig_tree.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0), height=380, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_tree, use_container_width=True)

elif menu == "📊 종목 정밀 분석":
    st.markdown('<div class="main-title">📊 종목 정밀 분석</div>', unsafe_allow_html=True)
    portfolio = load_data(); target = st.selectbox("분석 종목", portfolio['Ticker'].tolist() if not portfolio.empty else ["AAPL"], label_visibility="collapsed")
    hist, news = get_chart_and_news(target)
    if not hist.empty:
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#34c759', decreasing_line_color='#ff3b30')])
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    if news:
        st.markdown(f"### 📰 {target} 뉴스")
        for n in news[:5]: st.markdown(f"🔗 [{n.get('link')}]({n.get('link')})"); st.write("---")

# 5. 하단 고정 최신 업데이트 표시
st.sidebar.markdown('<div style="min-height: 40vh;"></div>', unsafe_allow_html=True)
st.sidebar.divider()
st.sidebar.markdown(f"<div style='text-align: center; color: #888; font-size: 0.95rem; font-weight: 600;'>최신 업데이트: {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)
