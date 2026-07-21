import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import os
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

# 1. PAGE CONFIGURATION & DARK NEON TERMINAL STYLING
st.set_page_config(
    page_title="Jio AI-Trading Super Terminal | Yogendra",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    .main { background-color: #030712; }
    body { color: #f9fafb; font-family: 'Inter', sans-serif; }
    
    .header-card {
        background: linear-gradient(135deg, #090d16 0%, #1e1b4b 50%, #0369a1 100%);
        border: 1px solid #38bdf8;
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(3, 105, 161, 0.3);
        margin-bottom: 25px;
    }
    
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="header-card">
        <h1 style="margin:0; font-size: 32px; font-weight: 800; color: #ffffff;">🤖 JIO AI-TRADING SUPER-PRECISION ENGINE</h1>
        <p style="margin:6px 0 0 0; font-size: 14px; color: #bae6fd;">Institutional Smart Money Concepts | Anti-Top Buy & Anti-Bottom Sell Protection | Dev: Yogendra Kumar</p>
    </div>
    """,
    unsafe_allow_html=True
)

st_autorefresh(interval=30000, key="jio_super_precision_clock")

def send_telegram_alert(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try: requests.post(url, json=payload, timeout=5)
        except Exception: pass

# 🧠 SUPER INSTITUTIONAL PRECISION ENGINE
def calculate_institutional_signal(df_5m):
    if len(df_5m) < 35: return 0, "INSUFFICIENT_DATA", 50, 0, False, 0, None, None
    
    last_candle_time = df_5m.index[-2]
    now_utc = datetime.now(timezone.utc)
    if last_candle_time.tzinfo is None:
        last_candle_time = last_candle_time.tz_localize('UTC')
        
    time_diff_minutes = (now_utc - last_candle_time).total_seconds() / 60.0
    is_fresh = time_diff_minutes <= 12.0  # Strict Freshness Guard
    
    c5 = pd.Series(df_5m['Close'].values.flatten(), index=df_5m.index)
    h5 = pd.Series(df_5m['High'].values.flatten(), index=df_5m.index)
    l5 = pd.Series(df_5m['Low'].values.flatten(), index=df_5m.index)
    v5 = pd.Series(df_5m['Volume'].values.flatten(), index=df_5m.index)
    
    # 1. RSI (14) Momentum Indicator
    delta = c5.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean() + 1e-10
    rsi = 100 - (100 / (1 + (gain / loss)))
    cur_rsi = float(rsi.iloc[-2])
    
    # 2. EMAs (Fast 9, Slow 21)
    ema9 = c5.ewm(span=9, adjust=False).mean()
    ema21 = c5.ewm(span=21, adjust=False).mean()
    
    # 3. ATR (14) for Dynamic Wiggle-Room SL & TP
    tr = pd.DataFrame([h5 - l5, abs(h5 - c5.shift(1)), abs(l5 - c5.shift(1))]).max()
    atr = float(tr.rolling(14).mean().iloc[-2])
    
    # 4. Volume Trend Check
    vol_avg = float(v5.rolling(20).mean().iloc[-2])
    cur_vol = float(v5.iloc[-2])
    is_high_volume = cur_vol > (vol_avg * 1.1)
    
    ema9_val = float(ema9.iloc[-2])
    ema21_val = float(ema21.iloc[-2])
    
    signal = 0
    reason = "Analyzing Market Structure..."
    
    # 🚨 STRICT INSTITUTIONAL FILTER LOGIC
    if ema9_val > ema21_val:
        if cur_rsi > 68:
            reason = "🛑 BUY BLOCKED: Overbought Top Zone (RSI > 68). High Risk of Sudden Dump!"
        elif cur_rsi < 42:
            reason = "⚠️ BUY BLOCKED: Low Momentum Divergence (RSI < 42)."
        elif not is_high_volume:
            reason = "⚠️ BUY BLOCKED: Low Volume Fakeout (No Whale Backing)."
        else:
            signal = 1
            reason = "🚀 SUPER ACCURATE BUY: High Volume Bullish Pullback Confirmed!"
            
    elif ema9_val < ema21_val:
        if cur_rsi < 32:
            reason = "🛑 SELL BLOCKED: Oversold Bottom Zone (RSI < 32). High Risk of Sudden Bounce!"
        elif cur_rsi > 58:
            reason = "⚠️ SELL BLOCKED: Bearish Momentum Fading (RSI > 58)."
        elif not is_high_volume:
            reason = "⚠️ SELL BLOCKED: Low Volume Drift."
        else:
            signal = -1
            reason = "💥 SUPER ACCURATE SELL: Heavy Volume Breakdown Confirmed!"
            
    return signal, reason, cur_rsi, atr, is_fresh, time_diff_minutes, ema9, ema21

ASSET_UNIVERSE = {
    "Solana (SOL)": "SOL-USD",
    "Bitcoin (BTC)": "BTC-USD",
    "XRP": "XRP-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Shiba Inu (SHIB)": "SHIB-USD",
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK"
}

if 'broadcasted_signals_history' not in st.session_state: 
    st.session_state.broadcasted_signals_history = {}
if 'selected_focus_asset' not in st.session_state:
    st.session_state.selected_focus_asset = "SOL-USD"

st.markdown("### 📡 24/7 Automated Multi-Asset Radar")

radar_data = {}
cols = st.columns(len(ASSET_UNIVERSE))

for idx, (asset_name, symbol) in enumerate(ASSET_UNIVERSE.items()):
    try:
        df_raw = yf.download(tickers=symbol, period="2d", interval="5m", progress=False)
        if df_raw is not None and not df_raw.empty and len(df_raw) > 35:
            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw.columns = df_raw.columns.get_level_values(0)
                
            sig, reason, rsi_val, atr_val, is_fresh, candle_age, ema9, ema21 = calculate_institutional_signal(df_raw)
            c_price = float(df_raw['Close'].values.flatten()[-1])
            p_fmt = ",.8f" if symbol == "SHIB-USD" else ",.2f"
            
            radar_data[symbol] = {
                "df": df_raw, "sig": sig, "reason": reason, "rsi": rsi_val, 
                "atr": atr_val, "is_fresh": is_fresh, "price": c_price, 
                "fmt": p_fmt, "ema9": ema9, "ema21": ema21, "name": asset_name
            }
            
            # AUTOMATED TELEGRAM SIGNAL BROADCASTING
            if is_fresh and sig != 0:
                action_type = "BUY" if sig == 1 else "SELL"
                sl = c_price - (2.2 * atr_val) if sig == 1 else c_price + (2.2 * atr_val)
                tp = c_price + (4.4 * atr_val) if sig == 1 else c_price - (4.4 * atr_val)
                candle_time_str = str(df_raw.index[-2])
                signal_unique_key = f"{symbol}{action_type}{candle_time_str}"
                
                if st.session_state.broadcasted_signals_history.get(symbol) != signal_unique_key:
                    st.balloons()
                    icon = "🚀" if sig == 1 else "💥"
                    msg = (
                        f"{icon} JIO SUPER AI-PRECISION {action_type} ALERT\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 Asset: {asset_name}\n"
                        f"🟩 Spot Entry: {c_price:{p_fmt}}\n"
                        f"🛑 Dynamic SL: {sl:{p_fmt}}\n"
                        f"🎯 Target (1:2.0): {tp:{p_fmt}}\n"
                        f"📈 RSI Value: {rsi_val:.1f}\n"
                        f"⏰ Generated: Just now ({candle_age:.1f}m ago)\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🤖 Smart Money Institutional Radar Engine"
                    )
                    send_telegram_alert(msg)
                    st.session_state.broadcasted_signals_history[symbol] = signal_unique_key

            badge = "🟢 BUY" if (is_fresh and sig == 1) else ("🔴 SELL" if (is_fresh and sig == -1) else "⚖️ NEUTRAL")
            with cols[idx]:
                if st.button(f"{asset_name}\n{c_price:{p_fmt}}\n{badge}", key=f"btn_grid_{symbol}", use_container_width=True):
                    st.session_state.selected_focus_asset = symbol
    except Exception:
        pass

st.markdown("---")

# SECTION 2: DETAILED TECHNICAL CHARTS & RISK MANAGEMENT TERMINAL
focus_sym = st.session_state.selected_focus_asset
if focus_sym in radar_data:
    item = radar_data[focus_sym]
    st.markdown(f"## 📊 Technical Analysis Terminal: {item['name']}")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Spot Price", f"{item['price']:{item['fmt']}}")
    m2.metric("RSI (14) Index", f"{item['rsi']:.1f}")
    
    if item['is_fresh'] and item['sig'] != 0:
        sl_val = item['price'] - (2.2 * item['atr']) if item['sig'] == 1 else item['price'] + (2.2 * item['atr'])
        tp_val = item['price'] + (4.4 * item['atr']) if item['sig'] == 1 else item['price'] - (4.4 * item['atr'])
        
        m3.metric("🛑 Smart StopLoss", f"{sl_val:{item['fmt']}}")
        m4.metric("🎯 Institutional Target", f"{tp_val:{item['fmt']}}")
        
        if item['sig'] == 1:
            st.success(f"🚀 *SUPER BUY SIGNAL ACTIVE* | Reason: {item['reason']}")
        else:
            st.error(f"💥 *SUPER SELL SIGNAL ACTIVE* | Reason: {item['reason']}")
    else:
        m3.metric("🛑 Smart StopLoss", "Scanning...")
        m4.metric("🎯 Institutional Target", "Scanning...")
        st.info(f"🛡️ *System Status:* {item['reason']}")

    # Interactive Plotly Candlestick Chart with Volume
    df_chart = item['df'].tail(60).copy()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
    
    fig.add_trace(go.Candlestick(
        x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
        low=df_chart['Low'], close=df_chart['Close'], name="Candle"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df_chart.index, y=item['ema9'].tail(60), line=dict(color='#38bdf8', width=1.5), name="EMA 9"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_chart.index, y=item['ema21'].tail(60), line=dict(color='#f59e0b', width=1.5), name="EMA 21"), row=1, col=1)
    
    colors = ['#22c55e' if c >= o else '#ef4444' for c, o in zip(df_chart['Close'], df_chart['Open'])]
    fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name="Volume"), row=2, col=1)
    
    fig.update_layout(
        template="plotly_dark", height=520, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_rangeslider_visible=False, paper_bgcolor="#030712", plot_bgcolor="#030712"
    )
    
    st.plotly_chart(fig, use_container_width=True)
