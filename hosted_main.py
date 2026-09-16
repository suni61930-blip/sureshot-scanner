
import schedule
import time
from datetime import datetime
from scanner_pro import scan_sureshots
from telegram_pro import push_sureshots

def job():
    # Only market hours IST 9:30-15:30
    now = datetime.now()
    if not (9 <= now.hour <= 15):
        return
    if now.weekday() >= 5: # no weekend
        return
    print(f"\n=== SCAN {now} ===")
    stocks, logs, avoided = scan_sureshots()
    print(f"Top picks: {[s['symbol'] for s in stocks]}")
    push_sureshots(stocks, avoided)

# Hosted schedule - runs every 30 min in market
schedule.every().day.at("09:35").do(job)
schedule.every().day.at("10:05").do(job)
schedule.every().day.at("11:00").do(job)
schedule.every().day.at("13:30").do(job)
schedule.every().day.at("14:00").do(job)

print("Hosted Sureshot Scanner LIVE - Nifty 200 + Event Filter")
print("Waiting for market hours...")
job() # run once at start

while True:
    schedule.run_pending()
    time.sleep(20)
