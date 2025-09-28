#!/usr/bin/env python3
"""
Solana Public Analyzer
Analyzes Solana whale addresses using public APIs and RPC
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class SolanaPublicAnalyzer:
    def __init__(self):
        # Using public Solana RPC endpoint
        self.rpc_url = "https://api.mainnet-beta.solana.com"
        # Using public Solscan API (no auth required for basic info)
        self.solscan_url = "https://api.solscan.io"
        
    def get_account_balance(self, address: str) -> float:
        """Get SOL balance using RPC"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }
            
            response = requests.post(self.rpc_url, json=payload, timeout=15)
            data = response.json()
            
            if "result" in data:
                lamports = data["result"]["value"]
                sol_balance = lamports / 1_000_000_000  # Convert from lamports
                return sol_balance
            
            return 0.0
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
            return 0.0
    
    def get_account_info_public(self, address: str) -> Dict:
        """Get account info using public Solscan API"""
        try:
            url = f"{self.solscan_url}/account?address={address}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  Public API status: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error with public API: {e}")
            return {}
    
    def get_token_holdings(self, address: str) -> List[Dict]:
        """Get token holdings using public API"""
        try:
            # Try multiple public endpoints
            endpoints = [
                f"https://api.solscan.io/account/tokens?address={address}",
                f"https://api.solscan.io/account?address={address}"
            ]
            
            for url in endpoints:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and "tokenAccounts" in data:
                            return data["tokenAccounts"]
                        elif isinstance(data, list):
                            return data
                except:
                    continue
            
            return []
        except Exception as e:
            print(f"❌ Error getting token holdings: {e}")
            return []
    
    def get_recent_transactions_rpc(self, address: str, limit: int = 10) -> List[Dict]:
        """Get recent transaction signatures using RPC"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    address,
                    {"limit": limit}
                ]
            }
            
            response = requests.post(self.rpc_url, json=payload, timeout=15)
            data = response.json()
            
            if "result" in data:
                return data["result"]
            
            return []
        except Exception as e:
            print(f"❌ Error getting transactions: {e}")
            return []
    
    def analyze_solana_whale(self, address: str) -> Dict:
        """Analyze a Solana whale address"""
        print(f"🔍 Analyzing Solana whale: {address[:8]}...{address[-8:]}")
        
        # Get SOL balance
        sol_balance = self.get_account_balance(address)
        sol_price = 140.0  # Approximate SOL price
        sol_usd_value = sol_balance * sol_price
        
        # Get public account info
        account_info = self.get_account_info_public(address)
        
        # Get recent transaction activity
        recent_txs = self.get_recent_transactions_rpc(address, 20)
        
        # Calculate activity metrics
        recent_activity = len([tx for tx in recent_txs if tx.get("blockTime")])
        
        # Try to get token holdings
        token_holdings = self.get_token_holdings(address)
        
        # Estimate total portfolio value
        total_token_value = 0
        top_tokens = []
        
        # Basic portfolio estimation
        if sol_usd_value > 1000:  # Significant SOL holding
            top_tokens.append({
                "symbol": "SOL",
                "amount": sol_balance,
                "usd_value": sol_usd_value
            })
        
        total_portfolio_value = sol_usd_value + total_token_value
        
        # Calculate whale score
        whale_score = (total_portfolio_value / 10000) + (recent_activity * 2)
        
        # Classification
        if total_portfolio_value >= 10_000_000:
            classification = "🐋 ULTRA WHALE"
        elif total_portfolio_value >= 5_000_000:
            classification = "🦈 MEGA WHALE"
        elif total_portfolio_value >= 1_000_000:
            classification = "🐳 LARGE WHALE"
        elif total_portfolio_value >= 100_000:
            classification = "🐟 MEDIUM WHALE"
        else:
            classification = "🐠 Small Fish"
        
        return {
            "address": address,
            "sol_balance": sol_balance,
            "sol_usd_value": sol_usd_value,
            "total_portfolio_value": total_portfolio_value,
            "whale_score": whale_score,
            "classification": classification,
            "recent_activity": recent_activity,
            "top_tokens": top_tokens,
            "analysis_timestamp": datetime.now().isoformat(),
            "is_active": recent_activity > 0
        }

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
    print("🌟 Solana Public Whale Analyzer")
    print("=" * 50)
    
    # Load addresses
    addresses = load_solana_addresses_from_config()
    if not addresses:
        print("❌ No Solana addresses found in config")
        return
    
    print(f"🔍 Found {len(addresses)} Solana addresses to analyze")
    
    # Initialize analyzer
    analyzer = SolanaPublicAnalyzer()
    
    # Analyze each address
    whale_data = []
    
    for i, address in enumerate(addresses, 1):
        print(f"\n🐋 Analyzing whale {i}/{len(addresses)}:")
        
        try:
            analysis = analyzer.analyze_solana_whale(address)
            
            print(f"   💰 SOL Balance: {analysis['sol_balance']:.4f} SOL")
            print(f"   💵 SOL USD Value: ${analysis['sol_usd_value']:,.2f}")
            print(f"   🏆 Whale Score: {analysis['whale_score']:.2f}")
            print(f"   📊 Classification: {analysis['classification']}")
            print(f"   🔄 Recent Activity: {analysis['recent_activity']} signatures")
            print(f"   ✅ Status: {'Active' if analysis['is_active'] else 'Inactive'}")
            
            whale_data.append(analysis)
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ Error analyzing {address}: {e}")
            continue
    
    # Sort by portfolio value
    whale_data.sort(key=lambda x: x["total_portfolio_value"], reverse=True)
    
    # Save results
    results = {
        "generated_at": datetime.now().isoformat(),
        "analyzer_type": "public_api",
        "total_whales": len(whale_data),
        "whales": whale_data,
        "summary": {
            "total_sol_value": sum(w["sol_usd_value"] for w in whale_data),
            "active_whales": len([w for w in whale_data if w["is_active"]]),
            "average_whale_score": sum(w["whale_score"] for w in whale_data) / len(whale_data) if whale_data else 0
        }
    }
    
    with open('solana_whale_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n🎉 Solana Analysis Complete!")
    print(f"📊 Analyzed {len(whale_data)} Solana whales")
    print(f"💰 Total SOL Value: ${sum(w['sol_usd_value'] for w in whale_data):,.2f}")
    print(f"🔥 Active Whales: {len([w for w in whale_data if w['is_active']])}/{len(whale_data)}")
    print(f"💾 Results saved to: solana_whale_analysis.json")
    
    # Show summary
    if whale_data:
        print(f"\n🏆 Solana Whale Rankings:")
        for i, whale in enumerate(whale_data, 1):
            addr_short = whale["address"][:8] + "..." + whale["address"][-8:]
            status = "🟢" if whale["is_active"] else "🔴"
            print(f"   {i}. {status} {addr_short} - {whale['sol_balance']:.2f} SOL (${whale['sol_usd_value']:,.0f}) - {whale['classification']}")

if __name__ == "__main__":
    main()