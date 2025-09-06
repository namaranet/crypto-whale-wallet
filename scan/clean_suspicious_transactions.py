#!/usr/bin/env python3
"""
Clean Suspicious Transactions
Identifies and flags potentially erroneous transaction data
"""

import sqlite3
from datetime import datetime

def clean_suspicious_transactions():
    """Identify and optionally remove suspicious transactions"""
    print("🧹 Cleaning Suspicious Transaction Data")
    print("=" * 50)
    
    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()
        
        # Find transactions with suspiciously high USD values
        print("🔍 Finding suspiciously high-value transactions...")
        cursor.execute('''
            SELECT hash, token_symbol, value_native, value_usd, whale_category
            FROM transactions 
            WHERE value_usd > 1000000000
            ORDER BY value_usd DESC
        ''')
        
        suspicious = cursor.fetchall()
        
        if suspicious:
            print(f"⚠️  Found {len(suspicious)} suspicious transactions:")
            
            for hash_id, symbol, native, usd, category in suspicious:
                print(f"   • {symbol}: {native:,.0f} tokens = ${usd:,.0f}")
                print(f"     Hash: {hash_id[:20]}...")
            
            # Ask user what to do (in a real scenario)
            print(f"\n🤔 These transactions seem suspiciously large.")
            print(f"   Options:")
            print(f"   1. Keep them (they might be legitimate)")
            print(f"   2. Delete them (they might be API errors)")
            print(f"   3. Flag them for manual review")
            
            # For now, let's flag them for manual review
            print(f"\n✅ Flagging {len(suspicious)} transactions for manual review...")
            
            for hash_id, symbol, native, usd, category in suspicious:
                cursor.execute('''
                    UPDATE transactions 
                    SET whale_category = ? 
                    WHERE hash = ?
                ''', (f"{category} [FLAGGED]", hash_id))
            
            conn.commit()
            print(f"🏷️  Flagged {len(suspicious)} transactions with [FLAGGED] tag")
        else:
            print("✅ No suspicious transactions found")
        
        # Show current transaction value distribution
        print(f"\n📊 Transaction Value Distribution:")
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN value_usd >= 1000000 THEN '$1M+'
                    WHEN value_usd >= 100000 THEN '$100K-1M'
                    WHEN value_usd >= 10000 THEN '$10K-100K'
                    WHEN value_usd >= 1000 THEN '$1K-10K'
                    ELSE '<$1K'
                END as range,
                COUNT(*) as count,
                AVG(value_usd) as avg_usd
            FROM transactions
            GROUP BY range
            ORDER BY avg_usd DESC
        ''')
        
        distribution = cursor.fetchall()
        for range_name, count, avg_usd in distribution:
            print(f"   {range_name}: {count} transactions (avg: ${avg_usd:,.0f})")

if __name__ == "__main__":
    clean_suspicious_transactions()