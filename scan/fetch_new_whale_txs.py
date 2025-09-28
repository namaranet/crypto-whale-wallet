#!/usr/bin/env python3
"""
Fetch Transaction Data for New Whales
Direct API calls to get recent transactions for newly discovered whale addresses
"""

import requests
import json
import sqlite3
import time
from datetime import datetime

# New whale addresses discovered
NEW_WHALES = [
    "0xa69babef1ca67a37ffaf7a485dfff3382056e78c",
    "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
    "0x6427fc587266813b6993ae4c8de672640cb3b43f",
    "0x000000000004444c5dc75cb358380d2e3de08a90",
    "0xf6bfec3bdf5098dfac0e671ebce06cbead7a958e",
    "0x00c600b30fb0400701010f4b080409018b9006e0",
    "0xadc0a53095a0af87f3aa29fe0715b5c28016364e"
]

ETHERSCAN_API_KEY = "UQBC8ZX5PYJPVI8KXZ92QA5D98P6Z1EI45"

def get_address_transactions(address, max_results=20):
    """Get recent transactions for an address using Etherscan API"""

    print(f"🔍 Fetching transactions for {address[:10]}...")

    url = f"https://api.etherscan.io/api"
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': address,
        'startblock': 0,
        'endblock': 99999999,
        'page': 1,
        'offset': max_results,
        'sort': 'desc',
        'apikey': ETHERSCAN_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data['status'] == '1':
            transactions = data['result']
            print(f"   ✅ Found {len(transactions)} transactions")
            return transactions
        else:
            print(f"   ⚠️ No transactions found or API error: {data.get('message', 'Unknown error')}")
            return []

    except Exception as e:
        print(f"   ❌ Error fetching transactions: {e}")
        return []

def get_erc20_transactions(address, max_results=20):
    """Get ERC20 token transactions for an address"""

    print(f"🪙 Fetching ERC20 transfers for {address[:10]}...")

    url = f"https://api.etherscan.io/api"
    params = {
        'module': 'account',
        'action': 'tokentx',
        'address': address,
        'startblock': 0,
        'endblock': 99999999,
        'page': 1,
        'offset': max_results,
        'sort': 'desc',
        'apikey': ETHERSCAN_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data['status'] == '1':
            transactions = data['result']
            print(f"   ✅ Found {len(transactions)} ERC20 transfers")
            return transactions
        else:
            print(f"   ⚠️ No ERC20 transfers found")
            return []

    except Exception as e:
        print(f"   ❌ Error fetching ERC20 transfers: {e}")
        return []

def save_transactions_to_db(transactions, address):
    """Save transactions to database"""

    if not transactions:
        return 0

    saved_count = 0

    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()

        for tx in transactions:
            try:
                # Extract transaction data
                tx_hash = tx['hash']
                from_addr = tx['from'].lower()
                to_addr = tx['to'].lower()
                value_wei = int(tx['value']) if tx['value'] else 0
                timestamp = int(tx['timeStamp'])

                # Convert Wei to ETH
                value_eth = value_wei / 1e18

                # Estimate USD value (simplified - using $2400 ETH price)
                value_usd = value_eth * 2400

                # Only save transactions > $1000
                if value_usd > 1000:
                    cursor.execute('''
                        INSERT OR IGNORE INTO transactions
                        (hash, chain, from_address, to_address, token_symbol,
                         value_native, value_usd, timestamp, whale_category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        tx_hash, 'ethereum', from_addr, to_addr, 'ETH',
                        value_eth, value_usd, timestamp, 'WHALE'
                    ))
                    saved_count += 1

            except Exception as e:
                print(f"   ⚠️ Error saving transaction {tx.get('hash', 'unknown')}: {e}")
                continue

        conn.commit()

    return saved_count

def save_erc20_transactions_to_db(transactions, address):
    """Save ERC20 transactions to database"""

    if not transactions:
        return 0

    saved_count = 0

    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()

        for tx in transactions:
            try:
                # Extract transaction data
                tx_hash = tx['hash']
                from_addr = tx['from'].lower()
                to_addr = tx['to'].lower()
                token_symbol = tx['tokenSymbol']
                token_decimals = int(tx['tokenDecimal']) if tx['tokenDecimal'] else 18
                value_raw = int(tx['value']) if tx['value'] else 0
                timestamp = int(tx['timeStamp'])

                # Convert raw value to token amount
                value_tokens = value_raw / (10 ** token_decimals)

                # Estimate USD value based on token
                if token_symbol in ['USDT', 'USDC', 'DAI']:
                    value_usd = value_tokens  # Stablecoins ~= $1
                elif token_symbol == 'WBTC':
                    value_usd = value_tokens * 95000  # Approximate BTC price
                elif token_symbol == 'WETH':
                    value_usd = value_tokens * 2400   # Approximate ETH price
                else:
                    value_usd = value_tokens * 1  # Default estimation

                # Only save transactions > $1000
                if value_usd > 1000:
                    cursor.execute('''
                        INSERT OR IGNORE INTO transactions
                        (hash, chain, from_address, to_address, token_symbol,
                         value_native, value_usd, timestamp, whale_category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        tx_hash, 'ethereum', from_addr, to_addr, token_symbol,
                        value_tokens, value_usd, timestamp, 'WHALE'
                    ))
                    saved_count += 1

            except Exception as e:
                print(f"   ⚠️ Error saving ERC20 transaction {tx.get('hash', 'unknown')}: {e}")
                continue

        conn.commit()

    return saved_count

def main():
    """Main function to fetch and save whale transaction data"""

    print("🐋 Fetching Transaction Data for New Whales")
    print("=" * 50)

    total_saved = 0

    for address in NEW_WHALES:
        print(f"\n📊 Processing whale: {address}")

        # Get regular ETH transactions
        eth_txs = get_address_transactions(address, 20)
        saved_eth = save_transactions_to_db(eth_txs, address)

        # Small delay to avoid rate limiting
        time.sleep(0.2)

        # Get ERC20 token transactions
        erc20_txs = get_erc20_transactions(address, 20)
        saved_erc20 = save_erc20_transactions_to_db(erc20_txs, address)

        total_whale_saved = saved_eth + saved_erc20
        total_saved += total_whale_saved

        print(f"   💾 Saved {total_whale_saved} transactions ({saved_eth} ETH + {saved_erc20} ERC20)")

        # Small delay between addresses
        time.sleep(0.5)

    print(f"\n✅ Processing Complete!")
    print(f"💾 Total transactions saved: {total_saved}")

    # Show database stats
    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM transactions')
        total_txs = cursor.fetchone()[0]
        print(f"📊 Total transactions in database: {total_txs}")

if __name__ == '__main__':
    main()