import requests
import time

# ====== CONFIG ======
ETHERSCAN_API_KEY = "YOUR_ETHERSCAN_API_KEY"  # from https://etherscan.io/myapikey
WALLETS = [
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Example: Bitfinex
    "0x28C6c06298d514Db089934071355E5743bf21d60",  # Example: Binance
    # Add as many as you want
]

#sol addresses
#EGboTiF5aJL31BBHSjq2UoJw6nUFgsDnvahsh2efJHAF
CHECK_INTERVAL = 30  # seconds between checks

# Telegram config
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# Track last seen tx for each wallet
last_seen_tx = {wallet.lower(): None for wallet in WALLETS}

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

print("🚀 Tracking wallets:")
for w in WALLETS:
    print(" -", w)

while True:
    try:
        for wallet in WALLETS:
            txs = get_transactions(wallet)
            wallet_lc = wallet.lower()

            if txs:
                latest_tx = txs[0]
                tx_hash = latest_tx["hash"]

                if tx_hash != last_seen_tx[wallet_lc]:
                    token = latest_tx["tokenSymbol"]
                    value = int(latest_tx["value"]) / (10 ** int(latest_tx["tokenDecimal"]))
                    from_addr = latest_tx["from"]
                    to_addr = latest_tx["to"]

                    direction = "SENT" if from_addr.lower() == wallet_lc else "RECEIVED"

                    msg = (
                        f"🔔 *New Transaction!*\n\n"
                        f"*Wallet:* `{wallet}`\n"
                        f"*Hash:* [{tx_hash}](https://etherscan.io/tx/{tx_hash})\n"
                        f"*Token:* {value} {token}\n"
                        f"*Direction:* {direction}\n"
                        f"*From:* `{from_addr}`\n"
                        f"*To:* `{to_addr}`"
                    )

                    send_telegram(msg)
                    print(f"✅ Alert sent for {wallet}")

                    last_seen_tx[wallet_lc] = tx_hash

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print("Error:", e)
        time.sleep(CHECK_INTERVAL)
