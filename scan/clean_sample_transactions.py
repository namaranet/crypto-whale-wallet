#!/usr/bin/env python3
"""
Clean Sample Transactions
Remove fake/sample transactions from database, keeping only real blockchain transactions
"""

import sqlite3
from datetime import datetime, timedelta

def clean_sample_transactions():
    """Remove sample transactions from database"""
    print("🧹 Cleaning Sample/Fake Transactions from Database")
    print("=" * 55)
    
    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()
        
        # Known sample transaction hashes that were hardcoded
        sample_hashes = [
            '0xa8022293a1bf9123e789f2341567890abcdef123',
            '0xb9133304b2cf0234f890g3452678901bcdefg234'
        ]
        
        print("🔍 Identifying sample transactions to remove...")
        
        # Find transactions with these specific sample hashes
        removed_count = 0
        for sample_hash in sample_hashes:
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE hash = ?', (sample_hash,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"   ❌ Found sample transaction: {sample_hash}")
                cursor.execute('DELETE FROM transactions WHERE hash = ?', (sample_hash,))
                removed_count += count
        
        # Also check for any transactions with suspiciously round values that might be fake
        cursor.execute('''
            SELECT hash, token_symbol, value_usd, from_address, to_address
            FROM transactions 
            WHERE (value_usd = 500000.0 OR value_usd = 643637.5 OR value_usd = 750000.0)
            AND (from_address = to_address OR 
                 hash LIKE '0xa8022293%' OR 
                 hash LIKE '0xb9133304%')
        ''')
        
        suspicious = cursor.fetchall()
        
        if suspicious:
            print(f"\n⚠️  Found {len(suspicious)} potentially fake transactions:")
            for hash_id, symbol, usd, from_addr, to_addr in suspicious:
                print(f"   • {symbol}: ${usd:,.0f} ({hash_id[:20]}...)")
                if from_addr == to_addr:
                    print(f"     ⚠️  Same from/to address - likely fake")
                
                # Remove these suspicious transactions
                cursor.execute('DELETE FROM transactions WHERE hash = ?', (hash_id,))
                removed_count += 1
        
        conn.commit()
        
        # Show final transaction count
        cursor.execute('SELECT COUNT(*) FROM transactions')
        final_count = cursor.fetchone()[0]
        
        print(f"\n✅ Removed {removed_count} sample/fake transactions")
        print(f"📊 Database now contains {final_count} real transactions")
        
        # Show recent transactions to verify they look real
        print(f"\n🔍 Recent transactions (verification):")
        cursor.execute('''
            SELECT hash, token_symbol, value_usd, whale_category
            FROM transactions 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''')
        
        recent = cursor.fetchall()
        for hash_id, symbol, usd, category in recent:
            print(f"   • {symbol}: ${usd:,.2f} {category} ({hash_id[:16]}...)")

if __name__ == "__main__":
    clean_sample_transactions()