#!/usr/bin/env python3
"""
Solana Whale Analyzer
Analyzes Solana whale addresses using Solscan API
"""

import requests
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import csv

@dataclass
class SolanaTransaction:
    signature: str
    block_time: int
    from_address: str
    to_address: str
    amount: float
    token_symbol: str
    token_address: str
    value_usd: float
    transaction_type: str

class SolanaWhaleAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pro-api.solscan.io/v2.0"
        self.headers = {
            "token": api_key,
            "accept": "application/json"
        }
    
    def get_account_info(self, address: str) -> Dict:
        """Get basic account information"""
        try:
            url = f"{self.base_url}/account/{address}"
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  Account info error for {address}: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error fetching account info: {e}")
            return {}
    
    def get_account_transactions(self, address: str, limit: int = 50) -> List[Dict]:
        """Get recent transactions for an account"""
        try:
            url = f"{self.base_url}/account/transaction"
            params = {
                "address": address,
                "limit": limit,
                "before": "",
                "remove_spam": "true"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                print(f"⚠️  Transaction error for {address}: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching transactions: {e}")
            return []
    
    def get_token_transfers(self, address: str, limit: int = 50) -> List[Dict]:
        """Get token transfer history"""
        try:
            url = f"{self.base_url}/account/transfer"
            params = {
                "address": address,
                "limit": limit,
                "remove_spam": "true"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                print(f"⚠️  Transfer error for {address}: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching transfers: {e}")
            return []
    
    def get_token_balance(self, address: str) -> Dict:
        """Get token balances for an address"""
        try:
            url = f"{self.base_url}/account/token"
            params = {
                "address": address,
                "page_size": 20
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                print(f"⚠️  Balance error for {address}: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching balances: {e}")
            return []
    
    def analyze_whale_address(self, address: str) -> Dict:
        """Comprehensive analysis of a single whale address"""
        print(f"🔍 Analyzing Solana address: {address}")
        
        # Get basic account info
        account_info = self.get_account_info(address)
        sol_balance = account_info.get("balance", 0) / 1_000_000_000  # Convert from lamports
        
        # Get transactions
        transactions = self.get_account_transactions(address, 100)
        transfers = self.get_token_transfers(address, 100)
        balances = self.get_token_balance(address)
        
        # Calculate metrics
        total_transactions = len(transactions) + len(transfers)
        
        # Calculate USD values (simplified - would need real-time prices)
        sol_price = 140.0  # Approximate SOL price
        total_sol_value = sol_balance * sol_price
        
        # Analyze token holdings
        token_values = []
        total_token_value = 0
        
        for balance in balances[:10]:  # Top 10 tokens
            token_info = balance.get("token_account", {})
            amount = float(balance.get("amount", 0))
            decimals = int(balance.get("decimals", 0))
            symbol = balance.get("token_symbol", "UNKNOWN")
            
            if decimals > 0:
                adjusted_amount = amount / (10 ** decimals)
            else:
                adjusted_amount = amount
            
            # Estimate USD value (simplified)
            if symbol == "USDC" or symbol == "USDT":
                usd_value = adjusted_amount
            elif symbol == "WSOL":
                usd_value = adjusted_amount * sol_price
            else:
                usd_value = adjusted_amount * 0.1  # Conservative estimate
            
            if usd_value > 1000:  # Only significant holdings
                token_values.append({
                    "symbol": symbol,
                    "amount": adjusted_amount,
                    "usd_value": usd_value
                })
                total_token_value += usd_value
        
        # Recent transaction analysis
        recent_large_txs = []
        for tx in transactions[:20]:  # Analyze recent 20 transactions
            if tx.get("block_time"):
                timestamp = datetime.fromtimestamp(tx["block_time"])
                if (datetime.now() - timestamp).days <= 7:  # Last 7 days
                    recent_large_txs.append({
                        "signature": tx.get("tx_hash", ""),
                        "timestamp": timestamp.isoformat(),
                        "type": tx.get("activity_type", "unknown")
                    })
        
        # Calculate whale score
        total_portfolio_value = total_sol_value + total_token_value
        transaction_frequency = len(recent_large_txs)
        whale_score = (total_portfolio_value / 10000) + (transaction_frequency * 5)
        
        return {
            "address": address,
            "sol_balance": sol_balance,
            "sol_usd_value": total_sol_value,
            "token_portfolio_value": total_token_value,
            "total_portfolio_value": total_portfolio_value,
            "whale_score": whale_score,
            "total_transactions": total_transactions,
            "recent_activity": len(recent_large_txs),
            "top_tokens": token_values,
            "recent_transactions": recent_large_txs,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def classify_whale_size(self, portfolio_value: float) -> str:
        """Classify whale by portfolio size"""
        if portfolio_value >= 10_000_000:
            return "🐋 ULTRA WHALE"
        elif portfolio_value >= 5_000_000:
            return "🦈 MEGA WHALE"
        elif portfolio_value >= 1_000_000:
            return "🐳 LARGE WHALE"
        elif portfolio_value >= 100_000:
            return "🐟 MEDIUM WHALE"
        else:
            return "🐠 Small Fish"

def load_solana_addresses_from_config() -> List[str]:
    """Load Solana addresses from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            addresses = []
            
            for addr in config.get('known_whales', []):
                if addr.startswith('https://solscan.io/account/'):
                    # Extract Solana address from URL
                    solana_addr = addr.split('/')[-1]
                    addresses.append(solana_addr)
                elif len(addr) > 30 and not addr.startswith('0x'):
                    # Looks like a Solana address
                    addresses.append(addr)
            
            return addresses
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return []

def main():
    print("🌟 Solana Whale Analyzer")
    print("=" * 50)
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            solscan_api_key = config.get('api_keys', {}).get('solscan')
            
            if not solscan_api_key or solscan_api_key == "YOUR_SOLSCAN_API_KEY":
                print("❌ No Solscan API key found in config.json")
                return
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Load addresses
    addresses = load_solana_addresses_from_config()
    if not addresses:
        print("❌ No Solana addresses found in config")
        return
    
    print(f"🔍 Found {len(addresses)} Solana addresses to analyze")
    
    # Initialize analyzer
    analyzer = SolanaWhaleAnalyzer(solscan_api_key)
    
    # Analyze each address
    whale_data = []
    
    for i, address in enumerate(addresses, 1):
        print(f"\n🐋 Analyzing whale {i}/{len(addresses)}: {address[:8]}...")
        
        try:
            analysis = analyzer.analyze_whale_address(address)
            whale_class = analyzer.classify_whale_size(analysis["total_portfolio_value"])
            
            print(f"   💰 Portfolio Value: ${analysis['total_portfolio_value']:,.2f}")
            print(f"   🏆 Whale Score: {analysis['whale_score']:.2f}")
            print(f"   📊 Classification: {whale_class}")
            print(f"   🔄 Recent Activity: {analysis['recent_activity']} transactions (7 days)")
            
            analysis["classification"] = whale_class
            whale_data.append(analysis)
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ Error analyzing {address}: {e}")
            continue
    
    # Sort by portfolio value
    whale_data.sort(key=lambda x: x["total_portfolio_value"], reverse=True)
    
    # Save results
    with open('solana_whale_analysis.json', 'w') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_whales": len(whale_data),
            "whales": whale_data
        }, f, indent=2)
    
    print(f"\n🎉 Analysis Complete!")
    print(f"📊 Analyzed {len(whale_data)} Solana whales")
    print(f"💾 Results saved to: solana_whale_analysis.json")
    
    # Show summary
    if whale_data:
        print(f"\n🏆 Top Solana Whales:")
        for i, whale in enumerate(whale_data[:5], 1):
            addr_short = whale["address"][:8] + "..." + whale["address"][-8:]
            print(f"   {i}. {addr_short} - ${whale['total_portfolio_value']:,.0f} ({whale['classification']})")

if __name__ == "__main__":
    main()