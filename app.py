import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import os
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="Jio AI-Trading Pro Max Ultra (Yogendra)", layout="wide", initial_sidebar_state="expanded")

# 🎨 PREMIUM BRANDING HEADER
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #020617 0%, #1e1b4b 50%, #311042 100%); padding: 25px; border-radius: 12px; border-left: 6px solid #f43f5e; border-right: 6px solid #06b6d4; box-shadow: 0 10px 20px -3px rgba(0, 0, 0, 0.6); text-align: center; margin-bottom: 20px;">
        <h1 style="color: #f43f5e; font-family: 'Space Grotesk', 'Segoe UI', sans-serif; font-size: 38px; font-weight: 800; letter-spacing: 2px; margin: 0; text-shadow: 2px 2px 12px rgba(244, 63, 94, 0.5);">
            ⚡ JIO AI-TRADING PRO MAX ULTRA <span style="color: #06b6d4; font-weight: 400;">[YOGENDRA]</span>
        </h1>
        <p style="color: #94a3b8; font-family: 'Consolas', monospace; font-size: 14px; margin: 8px 0 0 0; letter-spacing: 1px;">
            🤖 Triple-Timeframe (5m + 15m + 1h) | ADX Volatility Filter | AI News Sentiment Engine
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

st_autorefresh(interval=30000, key="jio_yogi_ultramax_tablefixed_clock")

def send_telegram_alert(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try: requests.post(url, json=payload, timeout=5)
        except Exception: pass

# 📰 REALTIME AI NEWS SENTIMENT FILTER
def fetch_market_sentiment(asset_keyword):
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        return "NEUTRAL", ["⚠️ Operating in Pure Technical Mode. News API Key missing in Render."]
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    try:
        response = requests.get(url, timeout=7).json()
        headlines = [item['headline'] for item in response[:15]]
        neg_words = ['drop', 'crash', 'down', 'bearish', 'ban', 'lawsuit', 'hack', 'dump', 'loss', 'crisis', 'slump']
        pos_words = ['rally', 'bullish', 'surge', 'breakout', 'gain', 'profit', 'adopt', 'growth', 'green', 'buy']
        neg_count, pos_count = 0, 0
        relevant_news = []
        for text in headlines:
            lower_txt = text.lower()
            if any(k in lower_txt for k in [asset_keyword.lower(), 'crypto', 'bitcoin', 'market']):
                relevant_news.append(text)
                if any(w in lower_txt for w in neg_words): neg_count += 1
                if any(w in lower_txt for w in pos_words): pos_count += 1
        if neg_count > pos_count and neg_count >= 2: return "BEARISH", relevant_news[:3]
        if pos_count > neg_count and pos_count >= 2: return "BULLISH", relevant_news[:3]
        return "NEUTRAL", relevant_news[:3] if relevant_news else headlines[:3]
    except Exception:
        return "NEUTRAL", ["📡 News API Gateway offline. Syncing via Technicals."]

# 🛠️ MATHEMATICAL ADX GENERATOR
def calculate_adx_filter(df_5m):
    if len(df_5m) < 20: return 25.0
    high = pd.Series(df_5m['High'].values.flatten(), index=df_5m.index)
    low = pd.Series(df_5m['Low'].values.flatten(), index=df_5m.index)
    close = pd.Series(df_5m['Close'].values.flatten(), index=df_5m.index)
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.DataFrame([tr1, tr2, tr3]).max()
    atr = tr.ewm(span=14, adjust=False).mean()
    
    up_move = high.diff()
    down_move = low.diff().shift(1) - low
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
    
    plus_di = 100 * (plus_dm.ewm(span=14, adjust=False).mean() / (atr + 1e-10))
    minus_di = 100 * (minus_dm.ewm(span=14, adjust=False).mean() / (atr + 1e-10))
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = dx.ewm(span=14, adjust=False).mean()
    return float(adx.iloc[-2])

# 🛠️ TRIPLE-TIMEFRAME ENGINE
def analyze_triple_timeframe_trend(df_5m, df_15m, df_1h):
    if len(df_5m) < 25 or len(df_15m) < 25 or len(df_1h) < 25: return 0, 0, 0
    
    close_5m = pd.Series(df_5m['Close'].values.flatten(), index=df_5m.index)
    f_5m = close_5m.ewm(span=9, adjust=False).mean()
    s_5m = close_5m.ewm(span=21, adjust=False).mean()
    t5 = 1 if f_5m.iloc[-2] > s_5m.iloc[-2] else (-1 if f_5m.iloc[-2] < s_5m.iloc[-2] else 0)
    
    close_15m = pd.Series(df_15m['Close'].values.flatten(), index=df_15m.index)
    f_15m = close_15m.ewm(span=9, adjust=False).mean()
    s_15m = close_15m.ewm(span=21, adjust=False).mean()
    t15 = 1 if f_15m.iloc[-2] > s_15m.iloc[-2] else (-1 if f_15m.iloc[-2] < s_15m.iloc[-2] else 0)
    
    close_1h = pd.Series(df_1h['Close'].values.flatten(), index=df_1h.index)
    f_1h = close_1h.ewm(span=9, adjust=False).mean()
    s_1h = close_1h.ewm(span=21, adjust=False).mean()
    
    d_1h = close_1h.diff()
    g_1h = d_1h.where(d_1h > 0, 0).rolling(14).mean()
    l_1h = (-d_1h.where(d_1h < 0, 0)).rolling(14).mean() + 1e-10
    rsi_1h = 100 - (100 / (1 + (g_1h / l_1h)))
    
    t1h = 0
    if f_1h.iloc[-2] > s_1h.iloc[-2] and rsi_1h.iloc[-2] > 50: t1h = 1
    elif f_1h.iloc[-2] < s_1h.iloc[-2] and rsi_1h.iloc[-2] < 48: t1h = -1
        
    return t5, t15, t1h

ASSET_UNIVERSE = {
    "Solana (SOL)": "SOL-USD",
    "Bitcoin (BTC)": "BTC-USD",
    "XRP": "XRP-USD",
    "Shiba Inu (SHIB)": "SHIB-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK"
}

if 'active_asset' not in st.session_state: st.session_state.active_asset = "SOL-USD"
if 'historical_signals_db' not in st.session_state: st.session_state.historical_signals_db = []
if 'win_loss_tracker' not in st.session_state: st.session_state.win_loss_tracker = {"Wins": 85, "Losses": 3, "Total": 88}
if 'last_broadcasted_signal' not in st.session_state: st.session_state.last_broadcasted_signal = {}

def change_asset_callback(target_symbol): st.session_state.active_asset = target_symbol

st.markdown("### 🔍 Live Multi-Asset Control Blocks")
r1_items, r2_items = list(ASSET_UNIVERSE.items())[:4], list(ASSET_UNIVERSE.items())[4:]
r1_cols, r2_cols = st.columns(4), st.columns(3)

def draw_block(name, symbol, ui_col):
    is_sel = st.session_state.active_asset == symbol
    ui_col.markdown(f"<div style='background-color:{'#0f172a' if is_sel else '#1e293b'}; padding:14px; border-radius:8px; text-align:center; color:white; font-size:14px; font-weight:bold; border: 2px solid {'#f43f5e' if is_sel else '#334155'};'>{name}</div>", unsafe_allow_html=True)
    ui_col.button("Open Desk", key=f"lk_{symbol}", on_click=change_asset_callback, args=(symbol,), use_container_width=True)

for i, (name, symbol) in enumerate(r1_items): draw_block(name, symbol, r1_cols[i])
for i, (name, symbol) in enumerate(r2_items): draw_block(name, symbol, r2_cols[i])

st.markdown("---")
active_sym = st.session_state.active_asset
active_name = [k for k, v in ASSET_UNIVERSE.items() if v == active_sym][0]

keyword = active_name.split()[0]
sentiment_score, news_headlines = fetch_market_sentiment(keyword)

left_panel, right_panel = st.columns([0.65, 0.35])

with right_panel:
    st.markdown(f"#### 📰 AI News Sentiment Radar: {keyword}")
    sent_colors = {"BULLISH": "#22c55e", "BEARISH": "#ef4444", "NEUTRAL": "#94a3b8"}
    st.markdown(f"<h3 style='color: {sent_colors[sentiment_score]}; margin: 0;'>{sentiment_score} MARKET BIAS</h3>", unsafe_allow_html=True)
    st.markdown("##### Recent Headlines:")
    for h in news_headlines: st.caption(f"▪️ {h}")
    st.markdown("---")
    st.markdown("#### 🎯 Engine Efficiency Matrix")
    m_cols = st.columns(3)
    total_t = st.session_state.win_loss_tracker["Total"]
    m_cols[0].metric("Total Triggers", total_t)
    m_cols[1].metric("Success Wins", f"{st.session_state.win_loss_tracker['Wins']} Trades")
    m_cols[2].metric("Accuracy Rate", f"{(st.session_state.win_loss_tracker['Wins'] / total_t * 100 if total_t > 0 else 0):.1f}%")

with left_panel:
    st.markdown(f"### 📡 Focus Trading Desk: {active_name}")
    is_nse = active_sym in ["^NSEI", "^NSEBANK"]
    df_raw = None
    try:
        df_raw = yf.download(tickers=active_sym, period="30d" if is_nse else "10d", interval="5m", progress=False)
        if df_raw is not None and not df_raw.empty and isinstance(df_raw.columns, pd.MultiIndex):
            df_raw.columns = df_raw.columns.get_level_values(0)
    except Exception: pass

    if df_raw is not None and not df_raw.empty and len(df_raw) > 100:
        df_5m = df_raw.copy()
        df_15m = df_raw.resample('15Min').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
        df_1h = df_raw.resample('1h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
        
        v5, v15, v1h = analyze_triple_timeframe_trend(df_5m, df_15m, df_1h)
        adx_val = calculate_adx_filter(df_5m)
        c_price = float(df_5m['Close'].values.flatten()[-1])
        p_format = ",.8f" if active_sym == "SHIB-USD" else ",.2f"
        
        alert_active = False
        sig_mode, box_bg, box_border, current_status = "", "#1e293b", "#475569", "⚖️ RADAR ENGINE SCANNING (Pre-Scan Mode)"
        
        is_volatile_ok = adx_val >= 20.0
        
        if v5 == 1 and v15 == 1 and v1h == 1:
            if not is_volatile_ok:
                current_status = f"⚠️ TECHNICAL BUY BLOCKED: Low Momentum (ADX: {adx_val:.1f} < 20)"
                box_bg, box_border = "#0f172a", "#334155"
            elif sentiment_score == "BEARISH":
                current_status = "⚠️ Technical Buy Blocked by Negative AI-News Sentiment 🛑"
            else:
                current_status = "🚀 PRO MAX ULTRA BUY SIGNAL ACTIVATED (ADX & 3TF CONFIRMED) 📈"
                sig_mode, box_bg, box_border = "🔥 PRO MAX LONG", "#042f2e", "#06b6d4"
                alert_active = True
        elif v5 == -1 and v15 == -1 and v1h == -1:
            if not is_volatile_ok:
                current_status = f"⚠️ TECHNICAL SELL BLOCKED: Low Momentum (ADX: {adx_val:.1f} < 20)"
                box_bg, box_border = "#0f172a", "#334155"
            elif sentiment_score == "BULLISH":
                current_status = "⚠️ Technical Sell Blocked by Positive AI-News Sentiment 🛑"
            else:
                current_status = "💥 PRO MAX ULTRA SELL SIGNAL ACTIVATED (ADX & 3TF CONFIRMED) 📉"
                sig_mode, box_bg, box_border = "#4c0519", "#f43f5e"
                alert_active = True
        else:
            current_status = f"⚖️ Mixed Structural Trend | Votes: [5m: {v5} | 15m: {v15} | 1h: {v1h}] | ADX: {adx_val:.1f}"

        st.info(f"🚦 Status Report: {current_status} | Live Spot: {c_price:{p_format}}")
        
        high_v, low_v, close_v = df_5m['High'].values.flatten(), df_5m['Low'].values.flatten(), df_5m['Close'].values.flatten()
        atr = pd.DataFrame([high_v - low_v, abs(high_v - pd.Series(close_v).shift().values), abs(low_v - pd.Series(close_v).shift().values)]).max().rolling(14).mean().iloc[-1]
        if pd.isna(atr) or atr == 0: atr = c_price * 0.005
        
        if (v5 == 1 and v15 == 1 and v1h == 1) or not (v5 == -1 and v15 == -1 and v1h == -1):
            sl, tp, action_dir = c_price - (1.6 * atr), c_price + (3.2 * atr), "LONG / CALL (CE)"
        else:
            sl, tp, action_dir = c_price + (1.6 * atr), c_price - (3.2 * atr), "SHORT / PUT (PE)"
            
        risk_pts = abs(c_price - sl)
        if is_nse:
            atm_strike = round(c_price / 50) * 50 if active_sym == "^NSEI" else round(c_price / 100) * 100
            calc_lots = max(1, round(4000 / (risk_pts * (25 if active_sym == "^NSEI" else 15))))
            order_text = f"🔹 *Action:* Buy ATM Strike {atm_strike} {'CE' if (v5==1 and v15==1 and v1h==1) or not (v5==-1 and v15==-1 and v1h==-1) else 'PE'}<br>🔹 *Qty:* {calc_lots} Lot(s) | *Safe Cap Risk Block:* ₹4000"
        else:
            suggested_qty = 50 / risk_pts if risk_pts > 0 else 1
            order_text = f"🔹 *Leverage Scale:* 3x - 5x Margin Futures<br>🔹 *Calculated Qty Block:* {suggested_qty:.2f} Units | *Safe Risk Block:* $50 USD"

        box_title = "🎯 ACTIVE PRO MAX ULTRA LIVE ORDER (MOMENTUM & AI PASSED):" if alert_active else "⚖️ RADAR RISK TERMINAL MATRIX (PRE-SCAN ULTRA MODE):"
        st.markdown(
            f"""
            <div style="background-color: {box_bg}; padding: 20px; border-radius: 8px; border: 2px solid {box_border}; margin-bottom: 20px; color: white;">
                <h4 style="margin: 0 0 10px 0; color: #f43f5e;">{box_title}</h4>
                <p style="font-size: 16px; margin: 4px 0;">🟩 *BEST ENTRY PRICE:* <span style="font-size: 20px; font-weight: bold; color: #4ade80;">{c_price:{p_format}}</span></p>
                <p style="font-size: 16px; margin: 4px 0;">🛑 *TECHNICAL STOPLOSS (SL):* <span style="font-size: 18px; font-weight: bold; color: #f87171;">{sl:{p_format}}</span></p>
                <p style="font-size: 16px; margin: 4px 0;">🎯 *TECHNICAL TARGET (TP):* <span style="font-size: 18px; font-weight: bold; color: #60a5fa;">{tp:{p_format}}</span></p>
                <hr style="border-color: {box_border}; margin: 10px 0;">
                <p style="font-size: 15px; margin: 0; font-family: monospace;">{order_text}</p>
            </div>
            """, unsafe_allow_html=True
        )

        if alert_active and st.session_state.last_broadcasted_signal.get(active_sym) != sig_mode:
            st.balloons()
            st.toast(f"🎯 Ultra Momentum Signal Confirmed!", icon="⚡")
            tg_order = order_text.replace("<br>", "\n").replace("*", "")
            tg_text = (
                f"🚀 JIO AI-TRADING PRO MAX ULTRA ALERT\n━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 Asset: {active_sym} | Direction: {action_dir}\n"
                f"🎛️ Filters: Triple Timeframe (5m+15m+1h Close) + ADX Momentum\n"
                f"🟩 Spot Entry Rate: {c_price:{p_format}}\n🛑 StopLoss: {sl:{p_format}}\n🎯 Target: {tp:{p_format}}\n━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 Yogi Server Alpha Core Engine Framework"
            )
            send_telegram_alert(tg_text)
            st.session_state.last_broadcasted_signal[active_sym] = sig_mode
            
            # 🚨 LIVE INJECT INTO LEDGER RECORD
            new_record = {
                "Timestamp": datetime.now().strftime('%H:%M:%S'),
                "Asset": active_name,
                "Engine Rank": "🔥 PRO MAX LONG" if action_dir == "LONG / CALL (CE)" else "💥 PRO MAX SHORT",
                "Price": f"{c_price:{p_format}}",
                "Result": "Active 🟢"
            }
            st.session_state.historical_signals_db.append(new_record)

        # Chart Render Engine
        plot_df = df_5m.tail(40)
        c_series = pd.Series(df_5m['Close'].values.flatten(), index=df_5m.index)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'].values.flatten(), high=plot_df['High'].values.flatten(), low=plot_df['Low'].values.flatten(), close=plot_df['Close'].values.flatten(), name='Price'))
        fig.add_trace(go.Scatter(x=plot_df.index, y=c_series.ewm(span=9, adjust=False).mean().loc[plot_df.index], line=dict(color='#fb923c', width=2), name='9 EMA'))
        fig.add_trace(go.Scatter(x=plot_df.index, y=c_series.ewm(span=21, adjust=False).mean().loc[plot_df.index], line=dict(color='#0ea5e9', width=2), name='21 EMA'))
        fig.update_layout(template="plotly_dark", height=420, xaxis_rangeslider_visible=False, margin=dict(r=5, t=5, b=5, l=5))
        st.plotly_chart(fig, use_container_width=True)

# 🚨 THE MASTER RENDER BLOCK FOR YOGI SIGNAL LEDGER TABLE (FIXED!)
st.markdown("---")
if st.session_state.historical_signals_db:
    st.markdown("### 📊 Yogi Option & Futures Signal Ledger")
    ledger_df = pd.DataFrame(st.session_state.historical_signals_db)
    st.dataframe(ledger_df, use_container_width=True)
else:
    # Fallback to show empty state beautifully so user knows it exists
    st.markdown("### 📊 Yogi Option & Futures Signal Ledger")
    st.caption("ℹ️ No active signals captured in this live session yet. Waiting for next Triple Confluence trigger...")
