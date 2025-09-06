#!/usr/bin/env python3
"""
Import discovered whales from CSV into the web UI database
"""

import pandas as pd
import sqlite3
import json
from datetime import datetime

def import_whales_to_database():
    """Import whales from discovered_whales.csv into whale_tracker.db"""
    
    print("🐋 Importing discovered whales into web UI database...")
    
    try:
        # Read the discovered whales CSV
        df = pd.read_csv('discovered_whales.csv')
        print(f"📄 Found {len(df)} whales in discovered_whales.csv")
        
        # Connect to the web UI database
        with sqlite3.connect('whale_tracker.db') as conn:
            cursor = conn.cursor()
            
            # Clear existing whale_addresses to avoid duplicates
            cursor.execute('DELETE FROM whale_addresses')
            print("🗑️  Cleared existing whale data")
            
            # Import each whale
            for _, whale in df.iterrows():
                # Parse tokens (remove spaces and split by comma)
                tokens = [t.strip() for t in whale['tokens_traded'].split(',')]
                chains = ['ethereum']  # All discovered whales are from Ethereum
                
                cursor.execute('''
                    INSERT INTO whale_addresses 
                    (address, total_volume_usd, transaction_count, avg_transaction_size,
                     whale_score, chains_active, tokens_traded, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    whale['address'],
                    whale['total_volume_usd'],
                    whale['tx_count'],
                    whale['avg_tx_size_usd'],
                    whale['whale_score'],
                    json.dumps(chains),
                    json.dumps(tokens),
                    datetime.now(),
                    datetime.now()
                ))
                
                print(f"✅ Imported: {whale['address'][:20]}... (Score: {whale['whale_score']})")
            
            conn.commit()
            print(f"💾 Successfully imported {len(df)} whales into database")
            
        return True
        
    except FileNotFoundError:
        print("❌ discovered_whales.csv not found. Run whale-discovery.py first.")
        return False
    except Exception as e:
        print(f"❌ Error importing whales: {e}")
        return False

def verify_import():
    """Verify the import was successful"""
    print("\n🔍 Verifying import...")
    
    try:
        with sqlite3.connect('whale_tracker.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM whale_addresses')
            count = cursor.fetchone()[0]
            
            cursor.execute('SELECT address, whale_score FROM whale_addresses ORDER BY whale_score DESC LIMIT 5')
            top_whales = cursor.fetchall()
            
            print(f"✅ Database now contains {count} whales")
            print("\n🏆 Top 5 whales in database:")
            for i, (address, score) in enumerate(top_whales, 1):
                print(f"   {i}. {address[:20]}... (Score: {score})")
                
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Whale Database Import Tool")
    print("=" * 50)
    
    # Import whales
    success = import_whales_to_database()
    
    if success:
        # Verify import
        verify_import()
        
        print(f"\n🎉 Import Complete!")
        print(f"🌐 Refresh your web UI at http://localhost:5000")
        print(f"📊 The dashboard will now show all {5} discovered whales")
    else:
        print(f"\n❌ Import Failed!")
        print(f"🔧 Make sure discovered_whales.csv exists and try again")