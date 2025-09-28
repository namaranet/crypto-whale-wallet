#!/usr/bin/env python3
"""
Update Profitable Traders Database
Saves profitable trader analysis results to database for web UI display
"""

import sqlite3
from profitable_trader_analyzer import ProfitableTraderAnalyzer
from datetime import datetime

def update_profitable_traders_database():
    """Update the profitable traders database with latest analysis"""

    print("🔄 Updating profitable traders database...")

    # Initialize analyzer
    analyzer = ProfitableTraderAnalyzer()

    # Get all profitable traders
    profitable_traders = analyzer.find_top_profitable_traders(50)

    print(f"📊 Found {len(profitable_traders)} profitable traders to save")

    # Save to database
    with sqlite3.connect("whale_tracker.db") as conn:
        cursor = conn.cursor()

        # Create profitable_traders table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profitable_traders (
                wallet_address TEXT PRIMARY KEY,
                total_profit REAL,
                win_rate REAL,
                trade_count INTEGER,
                avg_profit_per_trade REAL,
                profitability_score REAL,
                tier TEXT,
                trading_strategy TEXT,
                last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert or update each profitable trader
        traders_saved = 0
        for trader in profitable_traders:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO profitable_traders
                    (wallet_address, total_profit, win_rate, trade_count, avg_profit_per_trade,
                     profitability_score, tier, trading_strategy, last_analyzed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trader['wallet_address'],
                    trader['metrics']['total_profit'],
                    trader['metrics']['win_rate'],
                    trader['session_count'],
                    trader['metrics']['avg_profit_per_trade'],
                    trader['profitability_score'],
                    trader['tier'],
                    trader['pattern']['primary_strategy'],
                    datetime.now()
                ))
                traders_saved += 1

                print(f"✅ Saved: {trader['wallet_address'][:10]}... (Score: {trader['profitability_score']:.1f}, Tier: {trader['tier']})")

            except Exception as e:
                print(f"❌ Error saving {trader['wallet_address']}: {e}")

        conn.commit()
        print(f"\n💾 Successfully saved {traders_saved} profitable traders to database")

        # Display summary statistics
        cursor.execute('''
            SELECT
                COUNT(*) as total_traders,
                AVG(profitability_score) as avg_score,
                SUM(total_profit) as total_profits,
                AVG(win_rate) as avg_win_rate,
                MAX(profitability_score) as highest_score
            FROM profitable_traders
        ''')

        stats = cursor.fetchone()
        print(f"\n📈 Database Summary:")
        print(f"   Total Profitable Traders: {stats[0]}")
        print(f"   Average Score: {stats[1]:.1f}")
        print(f"   Total Profits Tracked: ${stats[2]:,.0f}")
        print(f"   Average Win Rate: {stats[3]:.1%}")
        print(f"   Highest Score: {stats[4]:.1f}")

        # Show tier distribution
        cursor.execute('''
            SELECT tier, COUNT(*) as count
            FROM profitable_traders
            GROUP BY tier
            ORDER BY
                CASE tier
                    WHEN 'ELITE' THEN 1
                    WHEN 'ADVANCED' THEN 2
                    WHEN 'PROFICIENT' THEN 3
                    WHEN 'EMERGING' THEN 4
                END
        ''')

        print(f"\n🏆 Tier Distribution:")
        for tier, count in cursor.fetchall():
            print(f"   {tier}: {count} traders")

if __name__ == '__main__':
    update_profitable_traders_database()