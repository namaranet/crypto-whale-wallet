import requests
import time
import csv
import os
from datetime import datetime

# ====== CONFIG ======
ETHERSCAN_API_KEY = "UQBC8ZX5PYJPVI8KXZ92QA5D98P6Z1EI45"
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

WALLETS = [
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Bitfinex
    "0x28C6c06298d514Db089934071355E5743bf21d60",  # Binance
    "0x365084b05fa7d5028346bd21d842ed0601bab5b8",  # Discovered whale 1
    "0x70bf6634ee8cb27d04478f184b9b8bb13e5f4710",  # Discovered whale 2
]

# Whale detection thresholds
WHALE_THRESHOLDS = {
    "large": 100000,     # $100k+
    "mega": 500000,      # $500k+
    "ultra": 1000000,    # $1M+
}

CHECK_INTERVAL = 30
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
CSV_FILE = "whale_transactions.csv"

last_seen_tx = {wallet.lower(): None for wallet in WALLETS}

# Price cache to avoid API spam
price_cache = {}
price_cache_timestamp = 0
PRICE_CACHE_DURATION = 300  # 5 minutes

def get_token_price(token_address):
    """Get token price in USD from CoinGecko"""
    global price_cache, price_cache_timestamp
    
    current_time = time.time()
    if current_time - price_cache_timestamp > PRICE_CACHE_DURATION:
        price_cache = {}
        price_cache_timestamp = current_time
    
    if token_address in price_cache:
        return price_cache[token_address]
    
    try:
        # Handle common tokens
        token_mapping = {
            "0xA0b86a33E6441D316e51581DeF8A6b1c4c4d4D6E": "ethereum",  # ETH
            "0xdAC17F958D2ee523a2206206994597C13D831ec7": "tether",     # USDT
            "0xA0b86a33E6441D316e51581DeF8A6b1c4c4d4D6E": "usd-coin",   # USDC
        }
        
        coin_id = token_mapping.get(token_address, f"ethereum-{token_address}")
        
        url = f"{COINGECKO_API_BASE}/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if coin_id in data:
            price = data[coin_id]["usd"]
            price_cache[token_address] = price
            return price
        else:
            # Fallback: try to get price by contract address
            url = f"{COINGECKO_API_BASE}/simple/token_price/ethereum"
            params = {"contract_addresses": token_address, "vs_currencies": "usd"}
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if token_address.lower() in data:
                price = data[token_address.lower()]["usd"]
                price_cache[token_address] = price
                return price
                
    except Exception as e:
        print(f"Error fetching price for {token_address}: {e}")
    
    return None

def get_transactions(address):
    """Fetch recent transactions from Etherscan"""
    url = f"https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "page": 1,
        "offset": 10,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("result", [])
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return []

def classify_whale_size(usd_value):
    """Classify transaction size"""
    if usd_value >= WHALE_THRESHOLDS["ultra"]:
        return "🐋 ULTRA WHALE"
    elif usd_value >= WHALE_THRESHOLDS["mega"]:
        return "🦈 MEGA WHALE"
    elif usd_value >= WHALE_THRESHOLDS["large"]:
        return "🐳 LARGE WHALE"
    else:
        return "🐠 Regular"

def send_telegram(message):
    """Send alert to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def log_to_csv(row):
    """Log transaction to CSV file"""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "wallet", "hash", "token", "token_address",
                "value", "usd_value", "whale_size", "direction", "from", "to"
            ])
        writer.writerow(row)

def discover_whale_addresses(tx_data):
    """Identify potential whale addresses from transaction data"""
    whale_addresses = set()
    
    for tx in tx_data:
        try:
            value = int(tx["value"]) / (10 ** int(tx["tokenDecimal"]))
            token_address = tx["contractAddress"]
            
            price = get_token_price(token_address)
            if price:
                usd_value = value * price
                
                if usd_value >= WHALE_THRESHOLDS["large"]:
                    whale_addresses.add(tx["from"])
                    whale_addresses.add(tx["to"])
                    
        except Exception as e:
            continue
    
    return whale_addresses

print("🚀 Enhanced Whale Tracker Starting...")
print(f"💰 Thresholds: Large: ${WHALE_THRESHOLDS['large']:,} | Mega: ${WHALE_THRESHOLDS['mega']:,} | Ultra: ${WHALE_THRESHOLDS['ultra']:,}")
print("📊 Tracking wallets:")
for w in WALLETS:
    print(f"   - {w}")

discovered_whales = set()

while True:
    try:
        for wallet in WALLETS:
            txs = get_transactions(wallet)
            wallet_lc = wallet.lower()
            
            # Discover new whale addresses
            new_whales = discover_whale_addresses(txs)
            for whale in new_whales:
                if whale not in discovered_whales and whale.lower() != wallet_lc:
                    discovered_whales.add(whale)
                    print(f"🎯 New whale discovered: {whale}")

            if txs:
                latest_tx = txs[0]
                tx_hash = latest_tx["hash"]

                if tx_hash != last_seen_tx[wallet_lc]:
                    try:
                        token = latest_tx["tokenSymbol"]
                        token_address = latest_tx["contractAddress"]
                        value = int(latest_tx["value"]) / (10 ** int(latest_tx["tokenDecimal"]))
                        from_addr = latest_tx["from"]
                        to_addr = latest_tx["to"]
                        timestamp = datetime.fromtimestamp(int(latest_tx["timeStamp"])).strftime("%Y-%m-%d %H:%M:%S")

                        direction = "SENT" if from_addr.lower() == wallet_lc else "RECEIVED"
                        
                        # Get USD value
                        price = get_token_price(token_address)
                        usd_value = value * price if price else 0
                        whale_size = classify_whale_size(usd_value)
                        
                        # Only alert for significant transactions
                        should_alert = usd_value >= WHALE_THRESHOLDS["large"] or price is None
                        
                        if should_alert:
                            usd_display = f"${usd_value:,.2f}" if price else "Price unavailable"
                            
                            msg = (
                                f"{whale_size} *Alert!*\n\n"
                                f"*Wallet:* `{wallet}`\n"
                                f"*Hash:* [{tx_hash[:16]}...](https://etherscan.io/tx/{tx_hash})\n"
                                f"*Token:* {value:,.4f} {token}\n"
                                f"*USD Value:* {usd_display}\n"
                                f"*Direction:* {direction}\n"
                                f"*From:* `{from_addr[:10]}...`\n"
                                f"*To:* `{to_addr[:10]}...`\n"
                                f"*Time:* {timestamp} UTC"
                            )

                            send_telegram(msg)
                            print(f"🚨 {whale_size} alert sent for {wallet}: {usd_display}")

                        # Log all transactions
                        log_to_csv([
                            timestamp, wallet, tx_hash, token, token_address,
                            value, usd_value, whale_size, direction, from_addr, to_addr
                        ])

                        last_seen_tx[wallet_lc] = tx_hash
                        
                    except Exception as e:
                        print(f"Error processing transaction {tx_hash}: {e}")

        # Print status
        print(f"✅ Scan complete. Discovered whales: {len(discovered_whales)}")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"Main loop error: {e}")
        time.sleep(CHECK_INTERVAL)