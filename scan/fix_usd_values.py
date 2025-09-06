#!/usr/bin/env python3
"""
Fix USD Values in Transaction Database
Recalculates USD values for all transactions using correct token prices
"""

import sqlite3
import requests
import json
from datetime import datetime

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
    
    # For unknown tokens, try to get price from CoinGecko
    if contract_address:
        try:
            price = get_coingecko_price_by_contract(contract_address)
            if price and price > 0:
                return price
        except Exception:
            pass
    
    # For completely unknown tokens, use conservative estimate
    return 0.000001  # Assume unknown tokens are worth very little

def get_coingecko_price_by_contract(contract_address):
    """Try to get token price from CoinGecko API using contract address"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/token_price/ethereum"
        params = {
            'contract_addresses': contract_address,
            'vs_currencies': 'usd'
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            contract_lower = contract_address.lower()
            if contract_lower in data and 'usd' in data[contract_lower]:
                return data[contract_lower]['usd']
    except Exception as e:
        print(f"   ⚠️  CoinGecko price fetch failed: {e}")
    
    return None

def classify_whale_size(usd_value):
    """Classify whale size by USD value"""
    if usd_value >= 1000000:
        return "🐋 ULTRA WHALE"
    elif usd_value >= 500000:
        return "🦈 MEGA WHALE" 
    elif usd_value >= 100000:
        return "🐳 LARGE WHALE"
    elif usd_value >= 50000:
        return "🐟 MEDIUM WHALE"
    else:
        return "🐠 Regular"

def fix_transaction_usd_values():
    """Fix USD values for all transactions in database"""
    print("🔧 Fixing USD Values in Transaction Database")
    print("=" * 60)
    
    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()
        
        # Get all transactions that need fixing
        cursor.execute('''
            SELECT hash, token_symbol, token_address, value_native, value_usd
            FROM transactions
            ORDER BY value_usd DESC
        ''')
        
        transactions = cursor.fetchall()
        print(f"📊 Found {len(transactions)} transactions to check")
        
        fixed_count = 0
        price_cache = {}
        
        for i, (hash_id, token_symbol, token_address, value_native, current_usd) in enumerate(transactions):
            if i % 20 == 0:
                print(f"🔍 Processing transaction {i+1}/{len(transactions)}")
            
            # Get correct token price
            cache_key = f"{token_symbol}:{token_address}"
            if cache_key in price_cache:
                token_price = price_cache[cache_key]
            else:
                token_price = get_token_price_estimate(token_symbol, token_address)
                price_cache[cache_key] = token_price
            
            # Calculate correct USD value
            correct_usd = value_native * token_price
            new_whale_category = classify_whale_size(correct_usd)
            
            # Only update if there's a significant difference (>10% or >$1000)
            if abs(correct_usd - current_usd) > max(current_usd * 0.1, 1000):
                cursor.execute('''
                    UPDATE transactions 
                    SET value_usd = ?, whale_category = ?
                    WHERE hash = ?
                ''', (correct_usd, new_whale_category, hash_id))
                
                fixed_count += 1
                
                if fixed_count <= 10:  # Show first 10 fixes
                    print(f"   ✅ Fixed {token_symbol}: ${current_usd:,.0f} → ${correct_usd:,.2f}")
        
        conn.commit()
        
        print(f"\n🎉 Fixed {fixed_count} transactions with incorrect USD values")
        
        # Show some examples of the fixes
        print(f"\n🔍 Verification - checking problem transaction:")
        cursor.execute('''
            SELECT hash, token_symbol, value_native, value_usd, whale_category
            FROM transactions 
            WHERE hash = '0x2c2539b777a9fb41c46b77e5dc135a6fd0bd40d7c061e1e4b10729fdbe0f845d'
        ''')
        
        result = cursor.fetchone()
        if result:
            hash_id, symbol, native, usd, category = result
            print(f"   Transaction: {hash_id}")
            print(f"   Token: {symbol}")
            print(f"   Native Amount: {native:,.2f}")
            print(f"   USD Value: ${usd:,.2f}")
            print(f"   Category: {category}")
        
        return fixed_count

if __name__ == "__main__":
    try:
        fixed = fix_transaction_usd_values()
        print(f"\n✅ Successfully fixed USD values for {fixed} transactions!")
        print("🌐 Refresh your web UI to see the corrected values")
        
    except Exception as e:
        print(f"❌ Error fixing USD values: {e}")