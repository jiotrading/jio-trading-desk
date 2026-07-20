import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Page Layout configuration
st.set_page_config(page_title="Yogi Trading Platform", layout="wide", initial_sidebar_state="expanded")
st.title("🤖 Best Trading Earning Platform (Yogi) - Live Dual-Core Control Desk")

# ⚡ SYSTEM REFRESH CLOCK: 2 second updates
refresh_count = st_autorefresh(interval=2000, key="yogi_master_split_clock")

# 📢 AUDIO ENGINE: Local background audio alert
def play_alert_sound(frequency=950, duration=0.8):
    sound_html = f"""
    <script>
    var context = new (window.AudioContext || window.webkitAudioContext)();
    var oscillator = context.createOscillator();
    var gain = context.createGain();
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.type = 'sine';
    oscillator.frequency.value = {frequency};
    gain.gain.setValueAtTime(1, context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + {duration});
    oscillator.start(context.currentTime);
    oscillator.stop(context.currentTime + {duration});
    </script>
    """
    st.components.v1.html(sound_html, height=0, width=0)

# 📲 TELEGRAM PUSH ENGINE: Sends locked signals to user's mobile instantly
def send_telegram_notification(message):
    # Fetches from Cloud Environment Variables securely
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            pass

# 🏢 Session State Management for Dual-Core P&L Tracking
if 'crypto_trades' not in st.session_state: st.session_state.crypto_trades = 0
if 'crypto_tp' not in st.session_state: st.session_state.crypto_tp = 0
if 'crypto_sl' not in st.session_state: st.session_state.crypto_sl = 0

if 'indian_trades' not in st.session_state: st.session_state.indian_trades = 0
if 'indian_tp' not in st.session_state: st.session_state.indian_tp = 0
if 'indian_sl' not in st.session_state: st.session_state.indian_sl = 0

if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'active_futures_asset' not in st.session_state: st.session_state.active_futures_asset = "SOL-USD"
if 'last_signal_tracker' not in st.session_state: st.session_state.last_signal_tracker = "HOLD"
if 'last_soft_state' not in st.session_state: st.session_state.last_soft_state = "HOLD"

asset_options = {
    "Solana (SOL)": "SOL-USD",
    "Bitcoin (BTC)": "BTC-USD",
    "XRP": "XRP-USD",
    "Shiba Inu (SHIB)": "SHIB-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Dogecoin (DOGE)": "DOGE-USD",
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK"
}

# --- 🎯 LIVE WATCHLIST PAIRS SELECTOR ---
st.markdown("### 📊 Live Watchlist Pairs Selector")
cols = st.columns(len(asset_options))
for idx, (name, symbol) in enumerate(asset_options.items()):
    btn_label = f"🎯 {name.split(' ')[0]}" if st.session_state.active_futures_asset == symbol else f"⚪ {name.split(' ')[0]}"
    if cols[idx].button(btn_label, key=f"bar_btn_{symbol}", use_container_width=True):
        st.session_state.active_futures_asset = symbol
        st.session_state.last_signal_tracker = "HOLD"
        st.session_state.last_soft_state = "HOLD"
        st.rerun()

ticker = st.session_state.active_futures_asset
is_indian_market = ticker in ["^NSEI", "^NSEBANK"]
core_mode_label = "🇮🇳 INDIAN F&O MODE" if is_indian_market else "🪙 CRYPTO FUTURES MODE"

# --- 🎯 TRADING SETUP MODE CONFIGURATOR ---
st.sidebar.header("🎯 Trading Setup Mode")

if is_indian_market:
    strategy_profile = st.sidebar.radio(
        "Choose Stock F&O Profile:",
        ["⚡ Stock Intraday F&O (Same-Day Exit)", "📈 Stock Positional Options (Hold 2-5 Days)"]
    )
    if "Intraday" in strategy_profile:
        timeframe, period, chart_view_range = "5m", "5d", "Show Last 50 Candles"
        st.sidebar.info("🇮🇳 Auto-Configured: 5-Min Intraday grid calibrated for NSE market hours volume.")
    else:
        timeframe, period, chart_view_range = "1h", "1mo", "Show Last 100 Candles"
        st.sidebar.info("📊 Auto-Configured: 1-Hour swing chart optimized for Option Buying/Writing trends.")
else:
    strategy_profile = st.sidebar.radio(
        "Choose Crypto Profile:",
        ["⚡ Crypto High-Speed Scalping (Quick Pips)", "🐋 Crypto Whale Position (Macro Swing)"]
    )
    if "Scalping" in strategy_profile:
        timeframe, period, chart_view_range = "5m", "1d", "Show Last 50 Candles"
        st.sidebar.info("🪙 Auto-Configured: 5-Min high-speed ticks for micro breakouts with 10x+ leverage.")
    else:
        timeframe, period, chart_view_range = "1h", "1mo", "Show Last 100 Candles"
        st.sidebar.info("🐋 Auto-Configured: 1-Hour macro trend tracking for spot accumulation or long swings.")

st.sidebar.markdown(f"---")
st.sidebar.markdown(f"### 🎛️ Active Engine Core:<br><span style='color:#38bdf8; font-weight:bold;'>{core_mode_label}</span>", unsafe_allow_html=True)

# Fetch data
df = yf.download(tickers=ticker, period=period, interval=timeframe, progress=False)
higher_tf = "1h" if timeframe in ["1m", "5m", "15m"] else "1d"
df_higher = yf.download(tickers=ticker, period="5d", interval=higher_tf, progress=False)

if df is not None and len(df) > 20 and df_higher is not None and len(df_higher) > 5:
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
    if isinstance(df_higher.columns, pd.MultiIndex): df_higher.columns = df_higher.columns.droplevel(1)

    # Math Technical Engine Calculations
    df['EMA_Fast'] = df['Close'].ewm(span=9, adjust=False).mean().squeeze()
    df['EMA_Slow'] = df['Close'].ewm(span=21, adjust=False).mean().squeeze()
    
    delta = df['Close'].diff().squeeze()
    df['RSI'] = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / ((-delta.where(delta < 0, 0)).rolling(14).mean() + 1e-10))))
    df['ATR'] = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1).rolling(14).mean()
    df['Vol_MA'] = df['Volume'].rolling(window=20).mean().squeeze()
    
    df_higher['EMA_Trend'] = df_higher['Close'].ewm(span=50, adjust=False).mean().squeeze()
    macro_trend = "BULLISH" if df_higher['Close'].iloc[-1] > df_higher['EMA_Trend'].iloc[-1] else "BEARISH"

    current_status = "HOLD"
    en, sl, tg = 0.0, 0.0, 0.0
    
    lot_size = "25 (1 Lot)" if ticker == "^NSEI" else "15 (1 Lot)" if ticker == "^NSEBANK" else "N/A"
    recommended_leverage = "15x - 20x" if "BTC" in ticker else "10x - 12x" if ("SOL" in ticker or "ETH" in ticker) else "3x - 5x" if ("SHIB" in ticker or "DOGE" in ticker) else "10x"

    i = -1 
    latest_price = float(df['Close'].iloc[i])
    current_atr = float(df['ATR'].iloc[i]) if not pd.isna(df['ATR'].iloc[i]) else latest_price * 0.002
    current_vol = float(df['Volume'].iloc[i])
    avg_vol = float(df['Vol_MA'].iloc[i])
    
    is_high_volume = current_vol > (avg_vol * 0.98) if is_indian_market else current_vol > (avg_vol * 0.99)

    rsi_long_cutoff = 51 if is_indian_market else 52
    rsi_short_cutoff = 46 if is_indian_market else 44

    is_long_valid = (df['EMA_Fast'].iloc[i] > df['EMA_Slow'].iloc[i]) and (df['RSI'].iloc[i] > rsi_long_cutoff) and (macro_trend == "BULLISH") and is_high_volume
    is_short_valid = (df['EMA_Fast'].iloc[i] < df['EMA_Slow'].iloc[i]) and (df['RSI'].iloc[i] < rsi_short_cutoff) and (macro_trend == "BEARISH") and is_high_volume

    # Soft Alert logic
    soft_state = "ALERT" if (df['EMA_Fast'].iloc[i] > df['EMA_Slow'].iloc[i] and df['RSI'].iloc[i] > rsi_long_cutoff) or (df['EMA_Fast'].iloc[i] < df['EMA_Slow'].iloc[i] and df['RSI'].iloc[i] < rsi_short_cutoff) else "HOLD"
    if soft_state == "ALERT" and st.session_state.last_soft_state == "HOLD" and not (is_long_valid or is_short_valid):
        play_alert_sound(frequency=600, duration=0.2)
        st.session_state.last_soft_state = "ALERT"
    elif soft_state == "HOLD":
        st.session_state.last_soft_state = "HOLD"

    if is_long_valid:
        current_status = "LONG 🚀" if not is_indian_market else "CALL OPTION (CE) 📈"
        en = latest_price
        sl = latest_price - (1.0 * current_atr if is_indian_market else 1.2 * current_atr)
        tg = latest_price + (2.0 * current_atr if is_indian_market else 2.5 * current_atr)
    elif is_short_valid:
        current_status = "SHORT 📉" if not is_indian_market else "PUT OPTION (PE) 📉"
        en = latest_price
        sl = latest_price + (1.0 * current_atr if is_indian_market else 1.2 * current_atr)
        tg = latest_price - (2.0 * current_atr if is_indian_market else 2.5 * current_atr)
    else:
        current_status = "HOLD"
        en, sl, tg = 0.0, 0.0, 0.0

    # Settlement logic
    if st.session_state.active_trade is not None:
        at = st.session_state.active_trade
        if at['ticker'] == ticker:
            is_bullish_type = "LONG" in at['type'] or "CALL" in at['type']
            if is_bullish_type:
                if latest_price >= at['target']:
                    if is_indian_market: st.session_state.indian_tp += 1
                    else: st.session_state.crypto_tp += 1
                    send_telegram_notification(f"🎯 TARGET HIT WIN! \nAsset: {ticker}\nExit Price: {latest_price}")
                    st.session_state.active_trade = None
                elif latest_price <= at['sl']:
                    if is_indian_market: st.session_state.indian_sl += 1
                    else: st.session_state.crypto_sl += 1
                    send_telegram_notification(f"🔴 STOP LOSS HIT PROTECTION! \nAsset: {ticker}\nExit Price: {latest_price}")
                    st.session_state.active_trade = None
            else:
                if latest_price <= at['target']:
                    if is_indian_market: st.session_state.indian_tp += 1
                    else: st.session_state.crypto_tp += 1
                    send_telegram_notification(f"🎯 SHORT TARGET HIT WIN! \nAsset: {ticker}\nExit Price: {latest_price}")
                    st.session_state.active_trade = None
                elif latest_price >= at['sl']:
                    if is_indian_market: st.session_state.indian_sl += 1
                    else: st.session_state.crypto_sl += 1
                    send_telegram_notification(f"🔴 SHORT STOP LOSS HIT! \nAsset: {ticker}\nExit Price: {latest_price}")
                    st.session_state.active_trade = None

    # Main Broadcast logic + Mobile Push Trigger
    if current_status != "HOLD" and en > 0:
        if st.session_state.last_signal_tracker != current_status:
            if is_indian_market: st.session_state.indian_trades += 1
            else: st.session_state.crypto_trades += 1
            st.session_state.active_trade = {
                "ticker": ticker, "type": current_status, "entry": en, "sl": sl, "target": tg
            }
            play_alert_sound(frequency=950, duration=0.8)
            st.balloons()
            
            # 🚀 MOBILE PUSH ALERT MESSAGE
            tg_msg = f"🔥 NEW YOGI SIGNAL DETECTED!\n\n📊 Asset: {ticker}\n🚦 Action: {current_status}\n🟢 Entry: {en:,.2f}\n🔴 StopLoss: {sl:,.2f}\n🎯 Target (TP): {tg:,.2f}"
            send_telegram_notification(tg_msg)
            
            st.session_state.last_signal_tracker = current_status
    elif current_status == "HOLD":
        st.session_state.last_signal_tracker = "HOLD"

    currency_symbol = "₹" if is_indian_market else "$"
    currency_suffix = " PTS" if is_indian_market else " USDT"
    fmt_str = "{:,.2f}" if (is_indian_market or latest_price > 1) else "{:,.4f}" if latest_price > 0.1 else "{:,.6f}"
    price_text = f"{currency_symbol}{fmt_str.format(latest_price)}{currency_suffix}"

    left_layout_pane, right_layout_pane = st.columns([0.62, 0.38])

    with left_layout_pane:
        st.markdown(f"##### 📈 लाइव कैंडलस्टिक प्रोग्रेस चार्ट ({ticker})")
        plot_df = df.tail(50)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name='Candles'))
        fig.add_trace(go.Scatter(x=plot_df.index, y=df['EMA_Fast'].loc[plot_df.index], line=dict(color='#fb923c', width=1.8), name='9 Fast EMA'))
        fig.add_trace(go.Scatter(x=plot_df.index, y=df['EMA_Slow'].loc[plot_df.index], line=dict(color='#3b82f6', width=1.8), name='21 Slow EMA'))
        fig.add_hline(y=latest_price, line_dash="dash", line_color="#fb7185", annotation_text=f"◀️ {price_text}", annotation_position="right")
        fig.update_layout(template="plotly_dark", height=580, xaxis_rangeslider_visible=False, margin=dict(r=130, t=10, b=10, l=10), uirevision=ticker)
        st.plotly_chart(fig, use_container_width=True)

    with right_layout_pane:
        st.markdown("##### 📊 Live Performance Strategy Tracker")
        t_trades = st.session_state.indian_trades if is_indian_market else st.session_state.crypto_trades
        t_tp = st.session_state.indian_tp if is_indian_market else st.session_state.crypto_tp
        t_sl = st.session_state.indian_sl if is_indian_market else st.session_state.crypto_sl
        win_rate = (t_tp / t_trades * 100) if t_trades > 0 else 0.0
        
        pl_cols = st.columns(4)
        pl_cols[0].metric("Total Signals", t_trades)
        pl_cols[1].metric("🎯 Target Hit", t_tp)
        pl_cols[2].metric("🔴 SL Protections", t_sl, delta_color="inverse")
        pl_cols[3].metric("Win Rate %", f"{win_rate:.1f}%")
        
        st.markdown("---")
        st.markdown("##### 📋 लाइव टेक्निकल गाइडेंस स्कैनर")
        ema_state = "🟢 तेजी (BULLISH)" if df['EMA_Fast'].iloc[-1] > df['EMA_Slow'].iloc[-1] else "🔴 मंदी (BEARISH)"
        vol_state = "🔥 Volumetric Momentum Pass" if is_high_volume else "⏳ Low Activity Volume"
        trend_state = f"📈 Macro Upward" if macro_trend == "BULLISH" else f"📉 Macro Downward"
        
        scanner_df = pd.DataFrame({
            "फिल्टर पैरामीटर": ["Trend MA", "Volume Check", "Macro Filter", "RSI State"],
            "करंट स्टेटस": [ema_state, vol_state, trend_state, f"{df['RSI'].iloc[-1]:,.2f}"],
            "STATE VERIFICATION": [
                "Passed 🟢" if is_long_valid or is_short_valid else "Scanning...",
                "🟢 High Volume Pass" if is_high_volume else "⏳ Low Dynamic Volume Filter",
                "🟢 Trend Aligned" if (macro_trend == "BULLISH" and (is_long_valid)) or (macro_trend == "BEARISH" and (is_short_valid)) else "Macro Filter Block Active",
                "Strong Execution Momentum" if df['RSI'].iloc[-1] > rsi_long_cutoff or df['RSI'].iloc[-1] < rsi_short_cutoff else "Sideways Chop Trap Protection"
            ]
        })
        st.dataframe(scanner_df, hide_index=True, use_container_width=True)
        
        st.markdown(f"⏱️ *लाइव प्राइस:* {price_text} | *सिंक टाइम:* {datetime.now().strftime('%H:%M:%S')}")
        st.markdown("##### 🎯 Intelligent Execution Control")
        
        if current_status != "HOLD" and en > 0:
            en_txt = f"{currency_symbol}{fmt_str.format(en)}{currency_suffix}"
            sl_txt = f"{currency_symbol}{fmt_str.format(sl)}{currency_suffix}"
            tg_txt = f"{currency_symbol}{fmt_str.format(tg)}{currency_suffix}"
            
            st.markdown(f"<div style='background-color:#065f46; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center; color:white; font-size:16px;'><b>🟢 SIGNAL ACTIVE: {current_status}</b><br><span style='font-size:22px; font-weight:bold;'>{en_txt}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background-color:#991b1b; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center; color:white; font-size:16px;'><b>🔴 STOP LOSS (SL)</b><br><span style='font-size:22px; font-weight:bold;'>{sl_txt}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background-color:#065f46; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center; color:white; font-size:16px;'><b>🎯 PROFIT TARGET (TP)</b><br><span style='font-size:22px; font-weight:bold;'>{tg_txt}</span></div>", unsafe_allow_html=True)
        else:
            st.info("⏳ *Dynamic Monitoring Active...* Cloud backend is scanning.")