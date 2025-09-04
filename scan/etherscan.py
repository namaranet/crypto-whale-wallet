import requests
import time

# ====== CONFIG ======
ETHERSCAN_API_KEY = "YOUR_ETHERSCAN_API_KEY"  # from https://etherscan.io/myapikey
WALLET_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # example Bitfinex wallet
CHECK_INTERVAL = 30  # seconds between checks
#addresses
#0x15b325660a1C4a9582a7d834C31119C0CB9e3A42



# Telegram config
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# Track the last seen transaction hash
last_seen_tx = None

def get_transactions(address):
    url = f"https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "page": 1,
        "offset": 5,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }
    r = requests.get(url, params=params)
    data = r.json()
    return data.get("result", [])

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

print(f"🚀 Tracking wallet: {WALLET_ADDRESS}")

while True:
    try:
        txs = get_transactions(WALLET_ADDRESS)

        if txs:
            latest_tx = txs[0]
            tx_hash = latest_tx["hash"]

            if tx_hash != last_seen_tx:
                token = latest_tx["tokenSymbol"]
                value = int(latest_tx["value"]) / (10 ** int(latest_tx["tokenDecimal"]))
                from_addr = latest_tx["from"]
                to_addr = latest_tx["to"]

                direction = "SENT" if from_addr.lower() == WALLET_ADDRESS.lower() else "RECEIVED"
                
                msg = (
                    f"🔔 *New Transaction Detected!*\n\n"
                    f"*Hash:* [{tx_hash}](https://etherscan.io/tx/{tx_hash})\n"
                    f"*Token:* {value} {token}\n"
                    f"*Direction:* {direction}\n"
                    f"*From:* `{from_addr}`\n"
                    f"*To:* `{to_addr}`"
                )

                send_telegram(msg)
                print("✅ Sent alert to Telegram.")

                last_seen_tx = tx_hash

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print("Error:", e)
        time.sleep(CHECK_INTERVAL)
