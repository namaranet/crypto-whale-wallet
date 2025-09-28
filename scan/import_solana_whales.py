#!/usr/bin/env python3
"""
Import Solana Whales to Web UI Database
Imports analyzed Solana whale data into the web UI database
"""

import sqlite3
import json
from datetime import datetime

def import_solana_whales():
    """Import Solana whale analysis results into web database"""
    print("🌟 Solana Whale Database Import Tool")
    print("=" * 55)
    
    # Load Solana analysis results
    try:
        with open('solana_whale_analysis.json', 'r') as f:
            solana_data = json.load(f)
    except FileNotFoundError:
        print("❌ solana_whale_analysis.json not found. Run solana_public_analyzer.py first.")
        return
    except Exception as e:
        print(f"❌ Error loading Solana analysis: {e}")
        return
    
    whales = solana_data.get('whales', [])
    if not whales:
        print("❌ No Solana whales found in analysis file")
        return
    
    print(f"🐋 Found {len(whales)} Solana whales to import")
    
    # Connect to database
    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()
        
        # Add chain column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE whale_addresses ADD COLUMN chain TEXT DEFAULT "ethereum"')
        except sqlite3.OperationalError:
            pass  # Column might already exist
        
        # Add Solana-specific columns if they don't exist
        try:
            cursor.execute('ALTER TABLE whale_addresses ADD COLUMN sol_balance REAL DEFAULT 0')
            cursor.execute('ALTER TABLE whale_addresses ADD COLUMN recent_activity INTEGER DEFAULT 0')
            cursor.execute('ALTER TABLE whale_addresses ADD COLUMN is_active BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Columns might already exist
        
        imported_count = 0
        
        for whale in whales:
            address = whale['address']
            sol_balance = whale.get('sol_balance', 0)
            sol_usd_value = whale.get('sol_usd_value', 0)
            whale_score = whale.get('whale_score', 0)
            recent_activity = whale.get('recent_activity', 0)
            is_active = whale.get('is_active', False)
            classification = whale.get('classification', '🐠 Small Fish')
            
            # Convert classification to token list format for consistency
            if 'ULTRA' in classification:
                tokens_traded = '["SOL", "SPL-TOKENS"]'
            elif 'MEGA' in classification or 'LARGE' in classification:
                tokens_traded = '["SOL", "SPL-TOKENS"]'
            else:
                tokens_traded = '["SOL"]'
            
            # Insert or update whale data
            cursor.execute('''
                INSERT OR REPLACE INTO whale_addresses 
                (address, total_volume_usd, transaction_count, avg_transaction_size, 
                 whale_score, chains_active, tokens_traded, first_seen, last_seen,
                 chain, sol_balance, recent_activity, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                address,
                sol_usd_value,  # Use SOL USD value as total volume
                recent_activity,  # Use recent activity as transaction count
                sol_usd_value / max(recent_activity, 1),  # Average transaction size
                whale_score,
                '["solana"]',  # Chain active
                tokens_traded,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # first_seen
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # last_seen
                'solana',  # chain
                sol_balance,
                recent_activity,
                is_active
            ))
            
            if cursor.rowcount > 0:
                imported_count += 1
                addr_short = address[:8] + "..." + address[-8:]
                print(f"✅ Imported: {addr_short} - {sol_balance:.4f} SOL (${sol_usd_value:.2f}) - {classification}")
        
        conn.commit()
        
        # Verify import
        cursor.execute('SELECT COUNT(*) FROM whale_addresses WHERE chain = "solana"')
        total_solana_whales = cursor.fetchone()[0]
        
        print(f"\n💾 Import Summary:")
        print(f"   ✅ Imported: {imported_count} Solana whales")
        print(f"   📊 Total Solana whales in DB: {total_solana_whales}")
        print(f"   💰 Total SOL value: ${sum(w['sol_usd_value'] for w in whales):,.2f}")
        print(f"   🔥 Active whales: {sum(1 for w in whales if w['is_active'])}/{len(whales)}")
        
        # Show top whales in database
        print(f"\n🏆 Top Solana Whales in Database:")
        cursor.execute('''
            SELECT address, sol_balance, total_volume_usd, is_active, whale_score
            FROM whale_addresses 
            WHERE chain = "solana"
            ORDER BY total_volume_usd DESC
        ''')
        
        for i, (addr, sol_bal, usd_val, active, score) in enumerate(cursor.fetchall(), 1):
            addr_short = addr[:8] + "..." + addr[-8:]
            status = "🟢 Active" if active else "🔴 Inactive"
            print(f"   {i}. {addr_short} - {sol_bal:.4f} SOL (${usd_val:.2f}) - Score: {score:.2f} - {status}")

def create_solana_transactions():
    """Create sample Solana transactions for the imported whales"""
    print(f"\n📝 Creating Solana transaction entries...")
    
    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()
        
        # Get Solana whales
        cursor.execute('SELECT address, recent_activity, sol_balance FROM whale_addresses WHERE chain = "solana" AND is_active = 1')
        active_whales = cursor.fetchall()
        
        tx_count = 0
        
        for address, activity, sol_balance in active_whales:
            if activity > 0 and sol_balance > 0:
                # Create a representative transaction for each active whale
                cursor.execute('''
                    INSERT OR IGNORE INTO transactions
                    (hash, chain, from_address, to_address, token_symbol, token_address,
                     value_native, value_usd, timestamp, whale_category, gas_used, gas_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"sol_tx_{address[:16]}_{int(datetime.now().timestamp())}",  # Unique hash
                    "solana",
                    address,
                    "11111111111111111111111111111112",  # System program
                    "SOL",
                    "",
                    sol_balance,
                    sol_balance * 140,  # Approximate USD value
                    int(datetime.now().timestamp()),
                    "🐠 Regular" if sol_balance * 140 < 100000 else "🐳 LARGE WHALE",
                    0,  # No gas concept in Solana
                    0   # No gas price in Solana
                ))
                
                if cursor.rowcount > 0:
                    tx_count += 1
        
        conn.commit()
        print(f"   ✅ Created {tx_count} Solana transaction entries")

if __name__ == "__main__":
    try:
        import_solana_whales()
        create_solana_transactions()
        
        print(f"\n🎉 Solana Import Complete!")
        print(f"🌐 Refresh your web UI at http://localhost:5000")
        print(f"📊 You can now view Solana whales in the dashboard")
        print(f"🔗 Network graphs will show both Ethereum and Solana addresses")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")