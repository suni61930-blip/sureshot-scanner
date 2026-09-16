# TEST MODE - forces a sample alert even if market closed
import os
if os.getenv("GITHUB_ACTIONS") and not stocks:
    print("Market closed - sending test alert")
    test_stock = {
        "symbol": "RELIANCE",
        "score": 88,
        "setup": "ORB Breakout (TEST)",
        "rs": 1.35,
        "vol": 2.1,
        "vwap_dist": 0.45,
        "entry": 2845,
        "sl": 2828,
        "target": 2879,
        "risk": 0.6,
        "sentiment": 1
    }
    push_sureshots([test_stock], set())
