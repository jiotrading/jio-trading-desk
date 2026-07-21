import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import os
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="Jio AI-Trading 24/7 Auto-Scanner (Yogendra)", layout="wide")

st.markdown(
    """
    <div style="background: linear-gradient(135deg, #020617 0%, #0369a1 100%); padding: 20px; border-radius: 10px; text-align: center; color: white; margin-bottom: 20px;">
        <h1 style="margin:0; font-size: 30px;">⚡ JIO AI-TRADING AUTOMATIC 24/7 MULTI-SCANNER</h1>
        <p style="margin:5px 0 0 0; font-size: 13px; color: #bae6fd;">Automatic Background Multi-Asset Radar | Zero-Click Telegram Alert System</p>
    </div>
    """, unsafe_allow_html=True
)

# 🔄 Automate page reload every 30 seconds for background scanning
st_autorefresh(interval=30000, key="jio_autoscanner_30s_clock")

def send_telegram_alert(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try: requests.post(url, json=payload, timeout=5)
        except Exception: pass

# 🧠 REALTIME SIGNAL EVALUATOR (WITH 10-MIN FRESHNESS GUARD)
def calculate_precision_signal(df_5m):
    if len(df_5m) < 30: return 0, "INSUFFICIENT_DATA", 50, 0, False, 0
    
    # Extract timestamp of the last closed 5-minute candle
    last_candle_time = df_5m.index[-2]
    now_utc = datetime.now(timezone.utc)
    if last_candle_time.tzinfo is None:
        last_candle_time = last_candle_time.tz_localize('UTC')
        
    time_diff_minutes = (now_utc - last_candle_time).total_seconds() / 60.0
    
    # Strict freshness check: Signal must be from a candle closed <= 10 minutes ago
    is_fresh = time_diff_minutes <= 10.0
    
    c5 = pd.Series(df_5m['Close'].values.flatten(), index=df_5m.index)
    h5 = pd.Series(df_5m['High'].values.flatten(), index=df_5m.index)
    l5 = pd.Series(df_5m['Low'].values.flatten(), index=df_5m.index)
    
    # RSI (14)
    delta = c5.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean() + 1e-10
    rsi = 100 - (100 / (1 + (gain / loss)))
    cur_rsi = float(rsi.iloc[-2])
    
    # EMA 9 & 21
    ema9 = c5.ewm(span=9, adjust=False).mean()
    ema21 = c5.ewm(span=21, adjust=False).mean()
    
    # ATR (14)
    tr = pd.DataFrame([h5 - l5, abs(h5 - c5.shift(1)), abs(l5 - c5.shift(1))]).max()
    atr = float(tr.rolling(14).mean().iloc[-2])
    
    ema9_val = float(ema9.iloc[-2])
    ema21_val = float(ema21.iloc[-2])
    
    signal = 0
    reason = "Scanning..."
    
    if ema9_val > ema21_val:
        if cur_rsi > 68:
            reason = "🛑 BUY BLOCKED: Overbought Top Zone (RSI > 68)"
        elif cur_rsi < 40:
            reason = "⚠️ BUY BLOCKED: Low Momentum"
        else:
            signal = 1
            reason = "✅ FRESH HIGH-PRECISION BUY SIGNAL!"
            
    elif ema9_val < ema21_val:
        if cur_rsi < 32:
            reason = "🛑 SELL BLOCKED: Oversold Bottom Zone (RSI < 32)"
        elif cur_rsi > 60:
            reason = "⚠️ SELL BLOCKED: Low Bearish Momentum"
        else:
            signal = -1
            reason = "✅ FRESH HIGH-PRECISION SELL SIGNAL!"
            
    return signal, reason, cur_rsi, atr, is_fresh, time_diff_minutes

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

st.markdown("### 📡 24/7 Background Radar Live Status")

# 🔄 BACKGROUND MULTI-ASSET SCANNING LOOP (SCANS ALL ASSETS AUTOMATED)
scan_results = []

for asset_name, symbol in ASSET_UNIVERSE.items():
    try:
        df_raw = yf.download(tickers=symbol, period="2d", interval="5m", progress=False)
        if df_raw is not None and not df_raw.empty and len(df_raw) > 30:
            if isinstance(df_raw.columns, pd.MultiIndex): 
                df_raw.columns = df_raw.columns.get_level_values(0)
                
            sig, reason, rsi_val, atr_val, is_fresh, candle_age = calculate_precision_signal(df_raw)
            c_price = float(df_raw['Close'].values.flatten()[-1])
            p_fmt = ",.8f" if symbol == "SHIB-USD" else ",.2f"
            
            status_tag = "⚖️ NEUTRAL"
            
            # AUTOMATIC TELEGRAM BROADCAST FOR ANY ASSET WITHOUT CLICKING!
            if is_fresh and sig != 0:
                action_type = "BUY" if sig == 1 else "SELL"
                sl = c_price - (2.0 * atr_val) if sig == 1 else c_price + (2.0 * atr_val)
                tp = c_price + (4.0 * atr_val) if sig == 1 else c_price - (4.0 * atr_val)
                
                # Unique ID using candle timestamp to prevent duplicate alerts
                candle_time_str = str(df_raw.index[-2])
                signal_unique_key = f"{symbol}{action_type}{candle_time_str}"
                
                if st.session_state.broadcasted_signals_history.get(symbol) != signal_unique_key:
                    st.balloons()
                    icon = "🚀" if sig == 1 else "💥"
                    msg = (
                        f"{icon} AUTOMATED REALTIME {action_type} ALERT\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 Asset: {asset_name}\n"
                        f"🟩 Spot Entry: {c_price:{p_fmt}}\n"
                        f"🛑 StopLoss: {sl:{p_fmt}}\n"
                        f"🎯 Target: {tp:{p_fmt}}\n"
                        f"📈 RSI: {rsi_val:.1f}\n"
                        f"⏰ Generated: Just now ({candle_age:.1f}m ago)\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🤖 Automated Background Radar Engine"
                    )
                    send_telegram_alert(msg)
                    st.session_state.broadcasted_signals_history[symbol] = signal_unique_key
                    
                status_tag = f"🟢 LIVE {action_type}"
                
            elif not is_fresh and sig != 0:
                status_tag = "⌛ EXPIRED SIGNAL (IGNORED)"
            else:
                status_tag = f"🛡️ {reason}"
                
            scan_results.append({
                "Asset": asset_name,
                "Price": f"{c_price:{p_fmt}}",
                "RSI": f"{rsi_val:.1f}",
                "Status / Signal": status_tag,
                "Candle Age": f"{candle_age:.1f} min ago"
            })
    except Exception:
        scan_results.append({"Asset": asset_name, "Price": "ERR", "RSI": "-", "Status / Signal": "Data Fetch Error", "Candle Age": "-"})

# Display Live Background Radar Table
if scan_results:
    st.table(pd.DataFrame(scan_results))
