#!/usr/bin/env python3
"""
Demo script showing the whale tracker in action
"""

import json
from datetime import datetime
from database_analytics import WhaleDatabase, WhaleTransaction

def demo_whale_tracker():
    print("🐋 Crypto Whale Tracker Demo")
    print("=" * 50)
    
    # Initialize database
    print("📊 Initializing whale database...")
    db = WhaleDatabase()
    
    # Add some demo whale transactions
    print("💰 Adding demo whale transactions...")
    
    demo_transactions = [
        {
            "hash": "0x1234567890abcdef1234567890abcdef12345678",
            "chain": "ethereum",
            "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "to": "0x8484Ef722627bf18ca5Ae6BcF031c23E6e922B30",
            "token": "USDT",
            "value": 250000,
            "category": "🦈 MEGA WHALE"
        },
        {
            "hash": "0x2345678901bcdefg2345678901bcdefg23456789",
            "chain": "ethereum", 
            "from": "0x28C6c06298d514Db089934071355E5743bf21d60",
            "to": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "token": "WETH",
            "value": 1500000,
            "category": "🐋 ULTRA WHALE"
        },
        {
            "hash": "0x3456789012cdefgh3456789012cdefgh34567890",
            "chain": "polygon",
            "from": "0x8484Ef722627bf18ca5Ae6BcF031c23E6e922B30",
            "to": "0x28C6c06298d514Db089934071355E5743bf21d60",
            "token": "MATIC",
            "value": 150000,
            "category": "🐳 LARGE WHALE"
        }
    ]
    
    # Add transactions to database
    for i, tx_data in enumerate(demo_transactions, 1):
        tx = WhaleTransaction(
            hash=tx_data["hash"],
            chain=tx_data["chain"],
            from_address=tx_data["from"],
            to_address=tx_data["to"],
            token_symbol=tx_data["token"],
            token_address="",
            value_native=tx_data["value"],
            value_usd=tx_data["value"],
            timestamp=int(datetime.now().timestamp()) - (i * 3600),  # Spread over hours
            whale_category=tx_data["category"]
        )
        
        success = db.add_transaction(tx)
        print(f"   ✅ Added {tx_data['category']} transaction: ${tx_data['value']:,}")
    
    print("\n📈 Generating whale analytics...")
    
    # Get top whales
    top_whales = db.get_top_whales(10)
    print(f"\n🏆 Top {len(top_whales)} Whales by Score:")
    for i, whale in enumerate(top_whales, 1):
        print(f"   {i}. {whale['address'][:20]}...")
        print(f"      Score: {whale['whale_score']}")
        print(f"      Volume: ${whale['total_volume_usd']:,.2f}")
        print(f"      Transactions: {whale['transaction_count']}")
        print(f"      Chains: {whale['chains_active']}")
        print()
    
    # Get whale transactions for top whale
    if top_whales:
        top_whale_addr = top_whales[0]['address']
        print(f"📊 Recent transactions for top whale {top_whale_addr[:20]}...:")
        
        whale_txs = db.get_whale_transactions(top_whale_addr, 5)
        for tx in whale_txs:
            print(f"   • {tx['whale_category']} - {tx['token_symbol']}: ${tx['value_usd']:,.2f}")
            print(f"     Hash: {tx['hash'][:20]}...")
            print(f"     Chain: {tx['chain'].upper()}")
            print()
    
    # Generate network analysis
    if top_whales:
        print("🕸️ Network Analysis:")
        network = db.get_address_network(top_whales[0]['address'])
        if network and 'network_size' in network:
            print(f"   Network Size: {network['network_size']} connected addresses")
            print(f"   Direct Connections: {len(network['edges'])}")
    
    # Daily report
    print("📅 Daily Report:")
    daily_report = db.generate_daily_report()
    print(f"   Date: {daily_report['date']}")
    print(f"   Total Volume: ${daily_report['total_volume_usd']:,.2f}")
    print(f"   Total Transactions: {daily_report['total_transactions']}")
    
    if daily_report['chain_breakdown']:
        print("   Chain Breakdown:")
        for chain_data in daily_report['chain_breakdown']:
            print(f"     {chain_data['chain'].upper()}: {chain_data['transactions']} txs, ${chain_data['volume_usd']:,.2f}")
    
    print(f"\n🎯 Demo Complete!")
    print(f"💾 Database saved as: whale_tracker.db")
    print(f"🔍 You can now run: python whale_tracker_main.py --mode report")

if __name__ == "__main__":
    demo_whale_tracker()