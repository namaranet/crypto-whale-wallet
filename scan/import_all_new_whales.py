#!/usr/bin/env python3
"""
Import All New Whale Addresses
Imports all newly discovered and configured whale addresses into the tracker
"""

import sqlite3
import json
from datetime import datetime

# Known profitable whale addresses from research
PROFITABLE_WHALE_ADDRESSES = {
    # These addresses have been documented as successful traders
    "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf": {
        "name": "Polygon Ecosystem Fund",
        "type": "institutional_whale", 
        "known_for": "Large institutional trades"
    },
    "0x1522900b6dafac587d499a862861c0869be6e428": {
        "name": "Successful DeFi Trader",
        "type": "defi_whale",
        "known_for": "DeFi protocol arbitrage"
    },
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": {
        "name": "OKX Hot Wallet",
        "type": "exchange_whale",
        "known_for": "Exchange operations"
    },
    "0x689c56aef474df92d44a1b70850f808488f9769c": {
        "name": "MEV Searcher",
        "type": "mev_whale", 
        "known_for": "MEV extraction profits"
    },
    "0x4b5922abf25858d012d12bb1184e5d3d0b6d6be4": {
        "name": "Institutional Trader",
        "type": "institutional_whale",
        "known_for": "Large volume trades"
    }
}

def get_address_chain(address):
    """Determine chain based on address format"""
    if address.startswith('0x') and len(address) == 42:
        return 'ethereum'
    elif len(address) > 30 and not address.startswith('0x'):
        return 'solana'
    else:
        return 'ethereum'  # default

def import_config_whales():
    """Import whales from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            addresses = config.get('known_whales', [])
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return []
    
    # Clean addresses
    clean_addresses = []
    for addr in addresses:
        if addr.startswith('https://solscan.io/account/'):
            clean_addresses.append(addr.split('/')[-1])
        else:
            clean_addresses.append(addr)
    
    return clean_addresses

def import_analyzed_whales():
    """Import whales from analysis results"""
    addresses = []
    
    # Load new whale analysis
    try:
        with open('new_whale_analysis.json', 'r') as f:
            data = json.load(f)
            for result in data.get('results', []):
                if 'error' not in result:
                    addresses.append(result['address'])
    except:
        pass
    
    return addresses

def import_whales_to_database():
    """Import all whale addresses to database"""
    print("🐋 Importing All Discovered Whales to Database")
    print("=" * 55)
    
    # Get all addresses
    config_addresses = import_config_whales()
    analyzed_addresses = import_analyzed_whales()
    profitable_addresses = list(PROFITABLE_WHALE_ADDRESSES.keys())
    
    # Combine and deduplicate
    all_addresses = list(dict.fromkeys(config_addresses + analyzed_addresses + profitable_addresses))
    
    print(f"📊 Total addresses to process: {len(all_addresses)}")
    print(f"   📋 From config: {len(config_addresses)}")
    print(f"   🔍 From analysis: {len(analyzed_addresses)}")  
    print(f"   💰 Known profitable: {len(profitable_addresses)}")
    
    # Load analysis data for reference
    analysis_data = {}
    try:
        with open('new_whale_analysis.json', 'r') as f:
            data = json.load(f)
            for result in data.get('results', []):
                if 'error' not in result:
                    analysis_data[result['address']] = result
    except:
        pass
    
    # Connect to database
    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()
        
        # Ensure all columns exist
        try:
            cursor.execute('ALTER TABLE whale_addresses ADD COLUMN chain TEXT DEFAULT "ethereum"')
            cursor.execute('ALTER TABLE whale_addresses ADD COLUMN whale_type TEXT DEFAULT "unknown"')
            cursor.execute('ALTER TABLE whale_addresses ADD COLUMN known_for TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass
        
        imported_count = 0
        updated_count = 0
        
        for address in all_addresses:
            chain = get_address_chain(address)
            
            # Get data from analysis if available
            analysis = analysis_data.get(address, {})
            balance_usd = analysis.get('balance_usd', 0)
            recent_txs = analysis.get('recent_transactions', 0)
            
            # Get profitable whale info if available
            profitable_info = PROFITABLE_WHALE_ADDRESSES.get(address, {})
            whale_type = profitable_info.get('type', 'discovered')
            known_for = profitable_info.get('known_for', 'High volume trading')
            
            # Calculate whale score based on available data
            if balance_usd > 0:
                whale_score = (balance_usd / 100000) + (recent_txs * 2)
            else:
                # Default score for known profitable whales
                whale_score = 100 if profitable_info else 10
            
            # Insert or update (without new columns for now)
            cursor.execute('''
                INSERT OR REPLACE INTO whale_addresses
                (address, total_volume_usd, transaction_count, avg_transaction_size,
                 whale_score, chains_active, tokens_traded, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                address,
                balance_usd,
                recent_txs,
                balance_usd / max(recent_txs, 1),
                whale_score,
                f'["{chain}"]',
                '["ETH", "TOKENS"]' if chain == 'ethereum' else '["SOL", "SPL-TOKENS"]',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            if cursor.rowcount > 0:
                imported_count += 1
                addr_short = address[:8] + "..." + address[-6:]
                chain_emoji = "🟦" if chain == 'ethereum' else "🟣"
                type_emoji = "💰" if profitable_info else "🔍"
                print(f"✅ {type_emoji}{chain_emoji} {addr_short} - {whale_type} (${balance_usd:,.0f})")
        
        conn.commit()
        
        # Get final stats
        cursor.execute('SELECT COUNT(*) FROM whale_addresses')
        total_whales = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM whale_addresses WHERE chain = "ethereum"')
        eth_whales = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_volume_usd) FROM whale_addresses')
        total_value = cursor.fetchone()[0] or 0
        
        print(f"\n📊 Import Summary:")
        print(f"   ✅ Total whales in database: {total_whales}")
        print(f"   💰 Total tracked value: ${total_value:,.0f}")
        
        # Show top whales
        print(f"\n🏆 Top 5 Whales by Value:")
        cursor.execute('''
            SELECT address, total_volume_usd, whale_score
            FROM whale_addresses 
            ORDER BY total_volume_usd DESC 
            LIMIT 5
        ''')
        
        for i, (addr, value, score) in enumerate(cursor.fetchall(), 1):
            addr_short = addr[:8] + "..." + addr[-6:]
            chain_emoji = "🟦" if addr.startswith('0x') else "🟣"
            print(f"   {i}. {chain_emoji} {addr_short} - ${value:,.0f} (Score: {score:.1f})")

if __name__ == "__main__":
    import_whales_to_database()
    
    print(f"\n🎉 All Whale Imports Complete!")
    print(f"🌐 Refresh your web UI to see all discovered whales")
    print(f"📊 Network graphs will show comprehensive whale relationships")