#!/usr/bin/env python3
"""
Import Real Whale Transactions - Fetch actual blockchain transactions for discovered whales
"""

import requests
import sqlite3
import time
from datetime import datetime
import json

# Configuration
ETHERSCAN_API_KEY = "UQBC8ZX5PYJPVI8KXZ92QA5D98P6Z1EI45"
ETHERSCAN_BASE = "https://api.etherscan.io/api"

# Whale thresholds for categorization
WHALE_THRESHOLDS = {
    "ultra": 1000000,    # $1M+
    "mega": 500000,      # $500k+
    "large": 100000,     # $100k+
}

def classify_whale_size(usd_value):
    """Classify whale transaction size"""
    if usd_value >= WHALE_THRESHOLDS["ultra"]:
        return "🐋 ULTRA WHALE"
    elif usd_value >= WHALE_THRESHOLDS["mega"]:
        return "🦈 MEGA WHALE"
    elif usd_value >= WHALE_THRESHOLDS["large"]:
        return "🐳 LARGE WHALE"
    else:
        return "🐠 Regular"

def get_eth_price():
    """Get current ETH price from CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "ethereum", "vs_currencies": "usd"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data["ethereum"]["usd"]
    except:
        return 4275.54  # Fallback price

def get_token_price_estimate(token_symbol, contract_address=None):
    """Get token price estimates with fallback for unknown tokens"""
    # Known stable prices
    stable_prices = {
        "USDT": 1.0,
        "USDC": 1.0,
        "sUSDe": 1.0,
        "crvUSD": 1.0,
        "BUSD": 1.0,
        "DAI": 1.0,
        "FRAX": 1.0,
        "USDS": 1.0,
    }
    
    # Known volatile token prices (should be updated regularly)
    volatile_prices = {
        "WETH": 2400.0,  # Updated estimate
        "ETH": 2400.0,
        "WBTC": 60000.0,  # Updated estimate
        "BTC": 60000.0,
        "autoETH": 2400.0,
        "UNI": 7.0,
        "LINK": 11.0,
        "SKY": 0.08,
        "Mog": 0.00000083665,  # Mog Coin price
    }
    
    # Check stable coins first
    if token_symbol in stable_prices:
        return stable_prices[token_symbol]
    
    # Check known volatile tokens
    if token_symbol in volatile_prices:
        return volatile_prices[token_symbol]
    
    # For unknown tokens, try to get price from simple heuristics
    # If we have a contract address, we could query CoinGecko API here
    if contract_address:
        try:
            # Try to get price from CoinGecko by contract address
            # This is a placeholder - in production you'd make API call
            price = get_coingecko_price_by_contract(contract_address)
            if price and price > 0:
                return price
        except Exception:
            pass
    
    # For completely unknown tokens, use conservative estimate
    # Instead of 1.0, use a very small value to avoid inflated USD amounts
    return 0.000001  # Assume unknown tokens are worth very little

def get_coingecko_price_by_contract(contract_address):
    """Try to get token price from CoinGecko API using contract address"""
    try:
        import requests
        url = f"https://api.coingecko.com/api/v3/simple/token_price/ethereum"
        params = {
            'contract_addresses': contract_address,
            'vs_currencies': 'usd'
        }
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            contract_lower = contract_address.lower()
            if contract_lower in data and 'usd' in data[contract_lower]:
                return data[contract_lower]['usd']
    except Exception as e:
        print(f"   ⚠️  CoinGecko price fetch failed: {e}")
    
    return None

def fetch_normal_transactions(address, limit=50):
    """Fetch normal ETH transactions"""
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "page": 1,
        "offset": limit,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }
    
    try:
        response = requests.get(ETHERSCAN_BASE, params=params, timeout=15)
        data = response.json()
        
        if data.get("status") == "1":
            return data.get("result", [])
        else:
            print(f"   ❌ Normal TX API error: {data.get('message')}")
            return []
            
    except Exception as e:
        print(f"   ❌ Normal TX request failed: {e}")
        return []

def fetch_token_transfers(address, limit=50):
    """Fetch token transfers"""
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "page": 1,
        "offset": limit,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }
    
    try:
        response = requests.get(ETHERSCAN_BASE, params=params, timeout=15)
        data = response.json()
        
        if data.get("status") == "1":
            return data.get("result", [])
        else:
            print(f"   ❌ Token TX API error: {data.get('message')}")
            return []
            
    except Exception as e:
        print(f"   ❌ Token TX request failed: {e}")
        return []

def process_normal_transaction(tx, eth_price):
    """Process a normal ETH transaction"""
    try:
        value_wei = int(tx.get("value", 0))
        value_eth = value_wei / (10**18)
        value_usd = value_eth * eth_price
        
        # Only include transactions with significant value
        if value_usd < 1000:  # Skip small transactions
            return None
        
        return {
            "hash": tx["hash"],
            "chain": "ethereum",
            "from_address": tx["from"],
            "to_address": tx["to"],
            "token_symbol": "ETH",
            "token_address": "",
            "value_native": value_eth,
            "value_usd": value_usd,
            "timestamp": int(tx["timeStamp"]),
            "whale_category": classify_whale_size(value_usd),
            "gas_used": int(tx.get("gasUsed", 0)),
            "gas_price": int(tx.get("gasPrice", 0))
        }
        
    except Exception as e:
        print(f"   ⚠️  Error processing normal TX: {e}")
        return None

def process_token_transfer(tx):
    """Process a token transfer"""
    try:
        value = int(tx.get("value", 0))
        decimals = int(tx.get("tokenDecimal", 18))
        value_native = value / (10**decimals)
        
        token_symbol = tx.get("tokenSymbol", "UNKNOWN")
        contract_address = tx.get("contractAddress", "")
        token_price = get_token_price_estimate(token_symbol, contract_address)
        value_usd = value_native * token_price
        
        # Only include significant transfers
        if value_usd < 1000:  # Skip small transfers
            return None
        
        return {
            "hash": tx["hash"],
            "chain": "ethereum",
            "from_address": tx["from"],
            "to_address": tx["to"],
            "token_symbol": token_symbol,
            "token_address": tx.get("contractAddress", ""),
            "value_native": value_native,
            "value_usd": value_usd,
            "timestamp": int(tx["timeStamp"]),
            "whale_category": classify_whale_size(value_usd),
            "gas_used": int(tx.get("gasUsed", 0)) if tx.get("gasUsed") else None,
            "gas_price": int(tx.get("gasPrice", 0)) if tx.get("gasPrice") else None
        }
        
    except Exception as e:
        print(f"   ⚠️  Error processing token TX: {e}")
        return None

def import_whale_transactions(address):
    """Import transactions for a specific whale address"""
    print(f"\n🔍 Fetching transactions for: {address[:20]}...")
    
    # Get ETH price
    eth_price = get_eth_price()
    
    # Fetch transactions
    normal_txs = fetch_normal_transactions(address, 30)
    time.sleep(0.2)  # Rate limiting
    
    token_txs = fetch_token_transfers(address, 50)
    time.sleep(0.2)  # Rate limiting
    
    print(f"   📊 Found {len(normal_txs)} normal + {len(token_txs)} token transactions")
    
    # Process transactions
    processed_transactions = []
    
    # Process normal transactions
    for tx in normal_txs:
        processed_tx = process_normal_transaction(tx, eth_price)
        if processed_tx:
            processed_transactions.append(processed_tx)
    
    # Process token transfers
    for tx in token_txs:
        processed_tx = process_token_transfer(tx)
        if processed_tx:
            processed_transactions.append(processed_tx)
    
    # Sort by timestamp (newest first)
    processed_transactions.sort(key=lambda x: x["timestamp"], reverse=True)
    
    print(f"   ✅ Processed {len(processed_transactions)} significant transactions")
    
    return processed_transactions

def store_transactions_in_db(transactions):
    """Store transactions in the web UI database"""
    if not transactions:
        return 0
    
    with sqlite3.connect("whale_tracker.db") as conn:
        cursor = conn.cursor()
        
        stored_count = 0
        
        for tx in transactions:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO transactions
                    (hash, chain, from_address, to_address, token_symbol, token_address,
                     value_native, value_usd, timestamp, whale_category, gas_used, gas_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tx["hash"], tx["chain"], tx["from_address"], tx["to_address"],
                    tx["token_symbol"], tx["token_address"], tx["value_native"],
                    tx["value_usd"], tx["timestamp"], tx["whale_category"],
                    tx["gas_used"], tx["gas_price"]
                ))
                
                if cursor.rowcount > 0:
                    stored_count += 1
                    
            except Exception as e:
                print(f"   ⚠️  Error storing transaction {tx['hash']}: {e}")
                continue
        
        conn.commit()
        return stored_count

def main():
    """Main import process"""
    print("🐋 Importing Real Whale Transactions")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get whale addresses from database
    with sqlite3.connect("whale_tracker.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT address FROM whale_addresses ORDER BY whale_score DESC")
        whale_addresses = [row[0] for row in cursor.fetchall()]
    
    print(f"🎯 Found {len(whale_addresses)} whales to process")
    
    total_transactions = 0
    
    # Clear existing transactions to avoid duplicates
    with sqlite3.connect("whale_tracker.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        conn.commit()
        print("🗑️  Cleared existing transaction data")
    
    # Process each whale
    for i, address in enumerate(whale_addresses, 1):
        print(f"\n{'='*60}")
        print(f"Processing Whale {i}/{len(whale_addresses)}")
        
        try:
            # Import transactions
            transactions = import_whale_transactions(address)
            
            if transactions:
                # Store in database
                stored_count = store_transactions_in_db(transactions)
                total_transactions += stored_count
                
                print(f"   💾 Stored {stored_count} transactions in database")
                
                # Show sample transactions
                print(f"   🔥 Sample transactions:")
                for tx in transactions[:3]:  # Show top 3
                    timestamp = datetime.fromtimestamp(tx["timestamp"]).strftime('%m/%d %H:%M')
                    print(f"      • {timestamp}: ${tx['value_usd']:,.0f} {tx['token_symbol']} ({tx['whale_category']})")
            else:
                print(f"   ⚠️  No significant transactions found")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Failed to process whale {address}: {e}")
            continue
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"📊 IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Total Transactions Imported: {total_transactions}")
    print(f"🐋 Whales Processed: {len(whale_addresses)}")
    print(f"📈 Average Transactions per Whale: {total_transactions/len(whale_addresses):.1f}")
    
    if total_transactions > 0:
        print(f"\n🎉 Import Complete!")
        print(f"🌐 Refresh your web UI at http://localhost:5000")
        print(f"📊 All whale detail pages now show real transaction history")
    else:
        print(f"\n⚠️  No transactions were imported")
        print(f"🔧 Check API keys and whale addresses")

if __name__ == "__main__":
    main()