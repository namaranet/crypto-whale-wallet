#!/usr/bin/env python3
"""
Whale Address Validator - Verify discovered addresses have real transactions
"""

import requests
import json
import time
from datetime import datetime

# Configuration
ETHERSCAN_API_KEY = "UQBC8ZX5PYJPVI8KXZ92QA5D98P6Z1EI45"
ETHERSCAN_BASE = "https://api.etherscan.io/api"

# Load discovered whales
DISCOVERED_WHALES = [
    "0x3a43aec53490cb9fa922847385d82fe25d0e9de7",
    "0x0a2b94f6871c1d7a32fe58e1ab5e6dea2f114e56", 
    "0x8d90113a1e286a5ab3e496fbd1853f265e5913c6",
    "0x52aa899454998be5b000ad077a46bbe360f4e497",
    "0x365084b05fa7d5028346bd21d842ed0601bab5b8"
]

def validate_address_format(address):
    """Check if address format is valid"""
    if not address.startswith('0x'):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False

def get_eth_balance(address):
    """Get ETH balance for address"""
    url = ETHERSCAN_BASE
    params = {
        "module": "account",
        "action": "balance",
        "address": address,
        "tag": "latest",
        "apikey": ETHERSCAN_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "1":
            balance_wei = int(data["result"])
            balance_eth = balance_wei / (10**18)
            return balance_eth
        else:
            print(f"   ❌ Balance API error: {data.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"   ❌ Balance request failed: {e}")
        return None

def get_transaction_count(address):
    """Get total transaction count for address"""
    url = ETHERSCAN_BASE
    params = {
        "module": "proxy",
        "action": "eth_getTransactionCount",
        "address": address,
        "tag": "latest",
        "apikey": ETHERSCAN_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if "result" in data:
            return int(data["result"], 16)
        else:
            print(f"   ❌ TX count error: {data}")
            return None
            
    except Exception as e:
        print(f"   ❌ TX count request failed: {e}")
        return None

def get_recent_transactions(address, limit=10):
    """Get recent normal transactions"""
    url = ETHERSCAN_BASE
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
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "1":
            return data.get("result", [])
        else:
            print(f"   ❌ Transactions API error: {data.get('message', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"   ❌ Transactions request failed: {e}")
        return []

def get_token_transfers(address, limit=10):
    """Get recent token transfers"""
    url = ETHERSCAN_BASE
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
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "1":
            return data.get("result", [])
        else:
            print(f"   ❌ Token transfers API error: {data.get('message', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"   ❌ Token transfers request failed: {e}")
        return []

def analyze_transaction_activity(transactions, token_transfers):
    """Analyze transaction patterns for legitimacy"""
    analysis = {
        'total_transactions': len(transactions) + len(token_transfers),
        'normal_txs': len(transactions),
        'token_transfers': len(token_transfers),
        'recent_activity': False,
        'large_amounts': False,
        'appears_active': False
    }
    
    # Check for recent activity (last 30 days)
    thirty_days_ago = int(time.time()) - (30 * 24 * 60 * 60)
    
    recent_normal = [tx for tx in transactions if int(tx.get('timeStamp', 0)) > thirty_days_ago]
    recent_tokens = [tx for tx in token_transfers if int(tx.get('timeStamp', 0)) > thirty_days_ago]
    
    analysis['recent_activity'] = len(recent_normal) > 0 or len(recent_tokens) > 0
    
    # Check for large amounts
    for tx in transactions:
        value_wei = int(tx.get('value', 0))
        value_eth = value_wei / (10**18)
        if value_eth > 1:  # More than 1 ETH
            analysis['large_amounts'] = True
            break
    
    for tx in token_transfers:
        try:
            value = int(tx.get('value', 0))
            decimals = int(tx.get('tokenDecimal', 18))
            token_amount = value / (10**decimals)
            # For major tokens, check if amount is significant
            if tx.get('tokenSymbol') in ['USDT', 'USDC'] and token_amount > 1000:
                analysis['large_amounts'] = True
                break
        except:
            continue
    
    # Overall activity assessment
    analysis['appears_active'] = (
        analysis['total_transactions'] > 0 and
        (analysis['recent_activity'] or analysis['total_transactions'] > 10)
    )
    
    return analysis

def validate_whale_address(address):
    """Comprehensive validation of a whale address"""
    print(f"\n🔍 Validating: {address}")
    
    # Check address format
    if not validate_address_format(address):
        print(f"   ❌ Invalid address format")
        return False
    
    print(f"   ✅ Address format valid")
    
    # Get basic info
    eth_balance = get_eth_balance(address)
    tx_count = get_transaction_count(address)
    
    time.sleep(0.2)  # Rate limiting
    
    if eth_balance is not None:
        print(f"   💰 ETH Balance: {eth_balance:.6f} ETH")
    
    if tx_count is not None:
        print(f"   📊 Transaction Count: {tx_count}")
    
    # Get transaction history
    transactions = get_recent_transactions(address, 20)
    time.sleep(0.2)  # Rate limiting
    
    token_transfers = get_token_transfers(address, 20)
    time.sleep(0.2)  # Rate limiting
    
    # Analyze activity
    analysis = analyze_transaction_activity(transactions, token_transfers)
    
    print(f"   📈 Normal Transactions: {analysis['normal_txs']}")
    print(f"   🪙 Token Transfers: {analysis['token_transfers']}")
    print(f"   ⏰ Recent Activity: {'Yes' if analysis['recent_activity'] else 'No'}")
    print(f"   💵 Large Amounts: {'Yes' if analysis['large_amounts'] else 'No'}")
    
    # Show sample transactions
    if transactions:
        print(f"   🔄 Latest Normal TX:")
        latest_tx = transactions[0]
        value_eth = int(latest_tx.get('value', 0)) / (10**18)
        timestamp = datetime.fromtimestamp(int(latest_tx['timeStamp'])).strftime('%Y-%m-%d %H:%M')
        print(f"      {timestamp}: {value_eth:.6f} ETH")
        print(f"      Hash: {latest_tx['hash']}")
    
    if token_transfers:
        print(f"   🪙 Latest Token Transfer:")
        latest_token = token_transfers[0]
        try:
            value = int(latest_token.get('value', 0))
            decimals = int(latest_token.get('tokenDecimal', 18))
            token_amount = value / (10**decimals)
            timestamp = datetime.fromtimestamp(int(latest_token['timeStamp'])).strftime('%Y-%m-%d %H:%M')
            print(f"      {timestamp}: {token_amount:.2f} {latest_token.get('tokenSymbol', 'UNKNOWN')}")
            print(f"      Hash: {latest_token['hash']}")
        except:
            print(f"      Unable to parse token transfer")
    
    # Verdict
    is_legitimate = analysis['appears_active'] and (eth_balance is None or eth_balance >= 0)
    
    if is_legitimate:
        print(f"   ✅ LEGITIMATE: Address shows real blockchain activity")
    else:
        print(f"   ❌ SUSPICIOUS: Limited or no activity detected")
    
    return is_legitimate

def main():
    """Main validation process"""
    print("🔍 Whale Address Validation Report")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Using API Key: {ETHERSCAN_API_KEY[:10]}...")
    print(f"🎯 Validating {len(DISCOVERED_WHALES)} addresses")
    
    legitimate_whales = []
    suspicious_whales = []
    
    for i, address in enumerate(DISCOVERED_WHALES, 1):
        print(f"\n{'='*60}")
        print(f"Whale {i}/{len(DISCOVERED_WHALES)}")
        
        try:
            is_legit = validate_whale_address(address)
            
            if is_legit:
                legitimate_whales.append(address)
            else:
                suspicious_whales.append(address)
                
            # Rate limiting between addresses
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Validation failed: {e}")
            suspicious_whales.append(address)
    
    # Final report
    print(f"\n{'='*60}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    print(f"✅ Legitimate Whales: {len(legitimate_whales)}")
    for addr in legitimate_whales:
        print(f"   • {addr}")
    
    print(f"\n❌ Suspicious Whales: {len(suspicious_whales)}")
    for addr in suspicious_whales:
        print(f"   • {addr}")
    
    print(f"\n📈 Validation Rate: {len(legitimate_whales)}/{len(DISCOVERED_WHALES)} ({len(legitimate_whales)/len(DISCOVERED_WHALES)*100:.1f}%)")
    
    if len(legitimate_whales) < len(DISCOVERED_WHALES):
        print(f"\n⚠️  RECOMMENDATION:")
        print(f"   Remove suspicious addresses from whale tracking")
        print(f"   Focus monitoring on the {len(legitimate_whales)} legitimate addresses")
    else:
        print(f"\n🎉 All discovered whales appear legitimate!")
    
    return legitimate_whales, suspicious_whales

if __name__ == "__main__":
    legit_whales, suspicious_whales = main()
    
    # Save results
    results = {
        'validation_date': datetime.now().isoformat(),
        'legitimate_whales': legit_whales,
        'suspicious_whales': suspicious_whales,
        'validation_rate': len(legit_whales) / len(DISCOVERED_WHALES)
    }
    
    with open('whale_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: whale_validation_results.json")