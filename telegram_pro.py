
import requests
from datetime import datetime
import os
BOT_TOKEN = os.getenv("BOT_TOKEN", "8871104656:AAGFT-aNaX5u5LhKdyEof6i9pQUAoWGlrLA")
CHAT_ID = os.getenv("CHAT_ID", "1914750448")

#BOT_TOKEN = "8871104656:AAGFT-aNaX5u5LhKdyEof6i9pQUAoWGlrLA"
#CHAT_ID = "1914750448" # e.g. @your_sureshot_channel or your numeric id

def push_sureshots(stocks, avoided):
    if not BOT_TOKEN.startswith("YOUR") and stocks:
        for i, s in enumerate(stocks, 1):
            sentiment_emoji = "🟢" if s['sentiment']>0 else "⚪"
            msg = f"""🚀 SURESHOT #{i} - {s['symbol']} {sentiment_emoji} (Score: {s['score']}/100)
Setup: {s['setup']} | RS: {s['rs']} | Vol: {s['vol']}x
Entry: {s['entry']} | SL: {s['sl']} (-{s['risk']}%) | TGT: {s['target']} (2.2R)
VWAP: +{s['vwap_dist']}% | Sentiment: {'+ve' if s['sentiment']>0 else 'Neutral'}
Invalidation: Below VWAP / OR Low
Time: {datetime.now().strftime('%d-%b %H:%M IST')}

⚠️ Not financial advice. Trade with risk management.
"""
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            print(f"Pushed {s['symbol']}: {r.status_code}")
    
    # Daily summary if nothing
    if not stocks:
        msg = f"""📊 Sureshot Scan - {datetime.now().strftime('%d-%b')}
No high-conviction setups today (Score >70).
Avoided due to events: {', '.join(list(avoided)[:5]) if avoided else 'None'}
Market may be choppy. Capital protection > trading.
"""
        if not BOT_TOKEN.startswith("YOUR"):
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg})

if __name__ == "__main__":
    from scanner_pro import scan_sureshots
    stocks, logs, avoided = scan_sureshots()
    print(f"Found: {stocks}")
    push_sureshots(stocks, avoided)
