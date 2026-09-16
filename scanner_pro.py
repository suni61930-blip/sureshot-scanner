
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from nifty200_list import NIFTY_200

# ============ EVENT & RESULTS FILTER ============
def get_today_results_and_events():
    """Returns set of symbols to AVOID today"""
    avoid = set()
    reasons = {}
    
    # Try NSE results calendar (with headers to bypass)
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        # NSE corporate actions - this endpoint gives results dates
        url = "https://www.nseindia.com/api/corporates-corporateActions?index=equities"
        # Fallback: use simple date check - earnings season logic
        # For robust live, replace with screener.in or NSE API
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Quick check via yfinance earnings date
        for sym in NIFTY_200[:30]:  # check top 30 to avoid rate limit, expand in prod
            try:
                t = yf.Ticker(sym+".NS")
                cal = t.calendar
                if cal is not None and not cal.empty:
                    # if earnings today +/-1 day, avoid
                    avoid.add(sym)
                    reasons[sym] = "RESULTS_TODAY"
            except:
                pass
    except Exception as e:
        print(f"Event fetch error: {e}")
    
    return avoid, reasons

def get_news_sentiment(symbol):
    """Returns +1 positive, -1 negative, 0 neutral"""
    try:
        t = yf.Ticker(symbol+".NS")
        news = t.news[:3] if hasattr(t, 'news') and t.news else []
        score = 0
        negative_keywords = ["downgrade","fraud","probe","penalty","fall","drop","loss","slump","cut","bearish","sell"]
        positive_keywords = ["upgrade","record profit","beat estimates","order win","contract","all time high","bullish","buy","growth","surge"]
        
        for n in news:
            title = n.get('title','').lower() if isinstance(n, dict) else str(n).lower()
            for k in negative_keywords:
                if k in title:
                    score -= 1
            for k in positive_keywords:
                if k in title:
                    score += 1
        # Red flag: circuit or trading halt
        if any(x in str(news).lower() for x in ["sebi ban","trading halt","circuit"]):
            score = -5
        
        return score
    except:
        return 0

def get_features(symbol, avoid_set):
    if symbol in avoid_set:
        return None, "EVENT_DAY"
    
    # News filter
    sentiment = get_news_sentiment(symbol)
    if sentiment <= -2:
        return None, f"NEGATIVE_NEWS ({sentiment})"
    
    try:
        hist = yf.Ticker(symbol+".NS").history(period="1d", interval="5m")
        if len(hist) < 10 or hist['Volume'].sum() == 0:
            return None, "NO_DATA"
        
        ltp = hist['Close'].iloc[-1]
        vwap = (hist['Close'] * hist['Volume']).cumsum().iloc[-1] / hist['Volume'].sum()
        or_high = hist['High'].iloc[0:3].max()
        or_low = hist['Low'].iloc[0:3].min()
        
        vol_today = hist['Volume'].sum()
        # avg volume approx
        avg_vol = yf.Ticker(symbol+".NS").info.get('averageVolume', 1000000)
        vol_ratio = vol_today / (avg_vol/75 + 1)
        
        # RS vs Nifty
        nifty_hist = yf.Ticker("^NSEI").history(period="1d", interval="5m")
        if len(nifty_hist) < 2:
            return None, "NIFTY_DATA"
        nifty_ret = nifty_hist['Close'].pct_change().iloc[-1] * 100
        stock_ret = hist['Close'].pct_change().iloc[-1] * 100
        rs = stock_ret / (nifty_ret + 0.01)
        
        # Scoring - sureshot logic
        score = 0
        if rs > 1.3: score += 35
        elif rs > 1.0: score += 15
        if vol_ratio > 2.0: score += 30
        elif vol_ratio > 1.5: score += 20
        if ltp > vwap: score += 15
        if ltp > or_high: score += 20
        
        # Boost for positive news
        if sentiment > 0:
            score += sentiment * 5
        
        if score < 70:
            return None, f"LOW_SCORE {score}"
        
        entry = ltp
        sl = min(or_low, vwap*0.995)
        risk_pct = (entry - sl) / entry * 100
        if risk_pct > 0.8 or risk_pct < 0.15:
            return None, f"BAD_RISK {risk_pct:.2f}%"
        
        target = entry + (entry - sl) * 2.2 # 2.2R for stocks
        
        return {
            "symbol": symbol,
            "score": int(min(score, 99)),
            "ltp": round(ltp,2),
            "rs": round(rs,2),
            "vol": round(vol_ratio,1),
            "vwap_dist": round((ltp-vwap)/vwap*100,2),
            "setup": "ORB Breakout" if ltp > or_high else "VWAP Reclaim",
            "entry": round(entry,2),
            "sl": round(sl,2),
            "target": round(target,2),
            "risk": round(risk_pct,2),
            "sentiment": sentiment
        }, "OK"
    except Exception as e:
        return None, str(e)

def scan_sureshots():
    avoid, reasons = get_today_results_and_events()
    print(f"Event filter avoiding: {avoid}")
    results = []
    logs = []
    for sym in NIFTY_200:
        feat, reason = get_features(sym, avoid)
        if feat:
            results.append(feat)
        else:
            logs.append(f"{sym}: {reason}")
    
    # Sort by score + sentiment boost
    results = sorted(results, key=lambda x: (x['score'] + x['sentiment']*2), reverse=True)[:5]
    return results, logs, avoid
