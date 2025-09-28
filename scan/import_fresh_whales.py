#!/usr/bin/env python3
"""
Import Fresh Whale Discoveries
Import the newly discovered whales from the latest scan into the database
"""

import pandas as pd
import sqlite3
import json
from datetime import datetime

def import_fresh_whale_discoveries():
    """Import fresh whale discoveries from the latest scan"""

    print("🔄 Importing Fresh Whale Discoveries...")

    # Read the discovered whales CSV
    try:
        df = pd.read_csv('discovered_whales.csv')
        print(f"📊 Found {len(df)} whales in discovered_whales.csv")
    except FileNotFoundError:
        print("❌ No discovered_whales.csv found")
        return

    # Connect to database
    with sqlite3.connect('whale_tracker.db') as conn:
        cursor = conn.cursor()

        imported_count = 0

        for _, row in df.iterrows():
            address = row['address']
            whale_score = row['whale_score']
            total_volume = row['total_volume_usd']
            daily_volume = row['daily_volume_usd']
            tx_count = row['tx_count']
            avg_tx_size = row['avg_tx_size_usd']
            tokens_traded = row['tokens_traded']
            days_active = row['days_active']

            # Check if whale already exists
            cursor.execute('SELECT address FROM whale_addresses WHERE address = ?', (address,))
            if cursor.fetchone():
                print(f"⚠️  {address[:10]}... already exists, updating...")
                # Update existing whale
                cursor.execute('''
                    UPDATE whale_addresses
                    SET total_volume_usd = ?, transaction_count = ?, avg_transaction_size = ?,
                        whale_score = ?, tokens_traded = ?, last_seen = ?
                    WHERE address = ?
                ''', (total_volume, tx_count, avg_tx_size, whale_score,
                      json.dumps([tokens_traded]), datetime.now(), address))
            else:
                print(f"✅ Importing NEW whale: {address[:10]}... (Score: {whale_score:.1f}, Volume: ${total_volume:,.0f})")
                # Insert new whale
                cursor.execute('''
                    INSERT INTO whale_addresses
                    (address, total_volume_usd, transaction_count, avg_transaction_size,
                     whale_score, chains_active, tokens_traded, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (address, total_volume, tx_count, avg_tx_size, whale_score,
                      json.dumps(["ethereum"]), json.dumps([tokens_traded]),
                      datetime.now(), datetime.now()))
                imported_count += 1

        conn.commit()
        print(f"\n💾 Successfully imported {imported_count} new whales")

        # Show updated stats
        cursor.execute('SELECT COUNT(*) FROM whale_addresses')
        total_whales = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(total_volume_usd) FROM whale_addresses')
        total_value = cursor.fetchone()[0] or 0

        print(f"📊 Updated Database Stats:")
        print(f"   Total Whales: {total_whales}")
        print(f"   Total Value: ${total_value:,.0f}")

        # Show top 5 by score
        cursor.execute('''
            SELECT address, whale_score, total_volume_usd
            FROM whale_addresses
            ORDER BY whale_score DESC
            LIMIT 5
        ''')

        print(f"\n🏆 Top 5 Whales by Score:")
        for i, (addr, score, volume) in enumerate(cursor.fetchall(), 1):
            print(f"   {i}. {addr[:10]}... - Score: {score:.1f}, Volume: ${volume:,.0f}")

if __name__ == '__main__':
    import_fresh_whale_discoveries()