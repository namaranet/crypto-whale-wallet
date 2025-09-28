#!/usr/bin/env python3
"""
Analyze New Config Whale Addresses
Analyzes the newly added whale addresses from config.json
"""

import json
import requests
from datetime import datetime
import time

# Load existing analyzed addresses to avoid duplicates
def get_existing_addresses():
    """Get addresses we've already analyzed"""
    existing = set()
    try:
        # Check Ethereum whales
        with open('discovered_whales.csv', 'r') as f:
            for line in f:
                if line.startswith('0x'):
                    existing.add(line.split(',')[0].strip())
    except:
        pass
    
    try:
        # Check Solana whales  
        with open('solana_whale_analysis.json', 'r') as f:
            data = json.load(f)
            for whale in data.get('whales', []):
                existing.add(whale['address'])
    except:
        pass
    
    return existing

def get_address_info(address):
    """Get basic info about an address"""
    if address.startswith('0x'):
        return analyze_eth_address(address)
    else:
        return analyze_solana_address(address)

def analyze_eth_address(address):
    """Analyze Ethereum address"""
    try:
        # Use Etherscan API
        api_key = "UQBC8ZX5PYJPVI8KXZ92QA5D98P6Z1EI45"
        
        # Get ETH balance
        balance_url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
        response = requests.get(balance_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1':
                wei_balance = int(data.get('result', 0))
                eth_balance = wei_balance / (10**18)
                
                # Get recent transactions
                tx_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=10&sort=desc&apikey={api_key}"
                tx_response = requests.get(tx_url, timeout=10)
                
                tx_count = 0
                if tx_response.status_code == 200:
                    tx_data = tx_response.json()
                    if tx_data.get('status') == '1':
                        tx_count = len(tx_data.get('result', []))
                
                return {
                    'address': address,
                    'chain': 'ethereum',
                    'balance': eth_balance,
                    'balance_usd': eth_balance * 2400,  # Approximate ETH price
                    'recent_transactions': tx_count,
                    'analysis_time': datetime.now().isoformat()
                }
        
        return {'address': address, 'chain': 'ethereum', 'error': 'API error'}
        
    except Exception as e:
        return {'address': address, 'chain': 'ethereum', 'error': str(e)}

def analyze_solana_address(address):
    """Analyze Solana address"""
    try:
        # Use Solana RPC
        rpc_url = "https://api.mainnet-beta.solana.com"
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }
        
        response = requests.post(rpc_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                lamports = data["result"]["value"]
                sol_balance = lamports / 1_000_000_000
                
                # Get transaction signatures
                sig_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignaturesForAddress",
                    "params": [address, {"limit": 10}]
                }
                
                sig_response = requests.post(rpc_url, json=sig_payload, timeout=10)
                tx_count = 0
                if sig_response.status_code == 200:
                    sig_data = sig_response.json()
                    if "result" in sig_data:
                        tx_count = len(sig_data["result"])
                
                return {
                    'address': address,
                    'chain': 'solana',
                    'balance': sol_balance,
                    'balance_usd': sol_balance * 140,  # Approximate SOL price
                    'recent_transactions': tx_count,
                    'analysis_time': datetime.now().isoformat()
                }
        
        return {'address': address, 'chain': 'solana', 'error': 'RPC error'}
        
    except Exception as e:
        return {'address': address, 'chain': 'solana', 'error': str(e)}

def main():
    print("🔍 Analyzing New Whale Addresses from Config")
    print("=" * 50)
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            all_addresses = config.get('known_whales', [])
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Clean up addresses (remove URLs)
    clean_addresses = []
    for addr in all_addresses:
        if addr.startswith('https://solscan.io/account/'):
            clean_addresses.append(addr.split('/')[-1])
        else:
            clean_addresses.append(addr)
    
    # Remove duplicates
    clean_addresses = list(dict.fromkeys(clean_addresses))
    
    print(f"📊 Found {len(clean_addresses)} addresses in config")
    
    # Get existing addresses to identify new ones
    existing = get_existing_addresses()
    new_addresses = [addr for addr in clean_addresses if addr not in existing]
    
    print(f"🆕 New addresses to analyze: {len(new_addresses)}")
    
    if not new_addresses:
        print("✅ All addresses already analyzed")
        return
    
    # Analyze new addresses
    results = []
    
    for i, address in enumerate(new_addresses, 1):
        print(f"\n🔍 Analyzing {i}/{len(new_addresses)}: {address[:10]}...")
        
        result = get_address_info(address)
        results.append(result)
        
        if 'error' not in result:
            chain_emoji = "🟦" if result['chain'] == 'ethereum' else "🟣"
            print(f"   {chain_emoji} Chain: {result['chain'].title()}")
            print(f"   💰 Balance: {result['balance']:.4f} {result['chain'].upper()}")
            print(f"   💵 USD Value: ${result['balance_usd']:,.2f}")
            print(f"   📊 Recent TXs: {result['recent_transactions']}")
        else:
            print(f"   ❌ Error: {result['error']}")
        
        time.sleep(1)  # Rate limiting
    
    # Save results
    output = {
        'analyzed_at': datetime.now().isoformat(),
        'new_addresses_count': len(new_addresses),
        'results': results
    }
    
    with open('new_whale_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Analysis Summary:")
    print(f"   🔍 Analyzed: {len(results)} new addresses")
    
    # Group by chain
    eth_results = [r for r in results if r.get('chain') == 'ethereum' and 'error' not in r]
    sol_results = [r for r in results if r.get('chain') == 'solana' and 'error' not in r]
    
    if eth_results:
        total_eth = sum(r['balance'] for r in eth_results)
        total_eth_usd = sum(r['balance_usd'] for r in eth_results)
        print(f"   🟦 Ethereum: {len(eth_results)} addresses, {total_eth:.2f} ETH (${total_eth_usd:,.0f})")
    
    if sol_results:
        total_sol = sum(r['balance'] for r in sol_results)
        total_sol_usd = sum(r['balance_usd'] for r in sol_results)
        print(f"   🟣 Solana: {len(sol_results)} addresses, {total_sol:.2f} SOL (${total_sol_usd:,.0f})")
    
    print(f"💾 Results saved to: new_whale_analysis.json")

if __name__ == "__main__":
    main()