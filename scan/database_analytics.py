import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class WhaleTransaction:
    hash: str
    chain: str
    from_address: str
    to_address: str
    token_symbol: str
    token_address: str
    value_native: float
    value_usd: float
    timestamp: int
    whale_category: str
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None

class WhaleDatabase:
    def __init__(self, db_path: str = "whale_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE NOT NULL,
                    chain TEXT NOT NULL,
                    from_address TEXT NOT NULL,
                    to_address TEXT NOT NULL,
                    token_symbol TEXT NOT NULL,
                    token_address TEXT,
                    value_native REAL NOT NULL,
                    value_usd REAL NOT NULL,
                    timestamp INTEGER NOT NULL,
                    whale_category TEXT NOT NULL,
                    gas_used INTEGER,
                    gas_price INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_from_address ON transactions(from_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_to_address ON transactions(to_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON transactions(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_value_usd ON transactions(value_usd)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chain ON transactions(chain)')
            
            # Whale addresses table with analytics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whale_addresses (
                    address TEXT PRIMARY KEY,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP,
                    total_volume_usd REAL DEFAULT 0,
                    transaction_count INTEGER DEFAULT 0,
                    avg_transaction_size REAL DEFAULT 0,
                    chains_active TEXT DEFAULT '[]',
                    tokens_traded TEXT DEFAULT '[]',
                    whale_score REAL DEFAULT 0,
                    labels TEXT DEFAULT '[]',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Daily statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT,
                    chain TEXT,
                    transaction_count INTEGER,
                    total_volume_usd REAL,
                    unique_addresses INTEGER,
                    avg_transaction_size REAL,
                    PRIMARY KEY (date, chain)
                )
            ''')
            
            # Address relationships (who transacts with whom)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS address_relationships (
                    from_address TEXT,
                    to_address TEXT,
                    interaction_count INTEGER DEFAULT 1,
                    total_volume_usd REAL DEFAULT 0,
                    last_interaction TIMESTAMP,
                    PRIMARY KEY (from_address, to_address)
                )
            ''')
            
            conn.commit()
    
    def add_transaction(self, tx: WhaleTransaction) -> bool:
        """Add a transaction to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO transactions 
                    (hash, chain, from_address, to_address, token_symbol, token_address,
                     value_native, value_usd, timestamp, whale_category, gas_used, gas_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tx.hash, tx.chain, tx.from_address, tx.to_address,
                    tx.token_symbol, tx.token_address, tx.value_native, tx.value_usd,
                    tx.timestamp, tx.whale_category, tx.gas_used, tx.gas_price
                ))
                
                # Update whale addresses analytics
                self.update_address_analytics(tx.from_address, tx)
                self.update_address_analytics(tx.to_address, tx)
                
                # Update address relationships
                self.update_address_relationship(tx.from_address, tx.to_address, tx.value_usd)
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False
    
    def update_address_analytics(self, address: str, tx: WhaleTransaction):
        """Update analytics for a whale address"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get existing data
            cursor.execute('SELECT * FROM whale_addresses WHERE address = ?', (address,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                total_volume = existing[3] + tx.value_usd
                tx_count = existing[4] + 1
                avg_tx_size = total_volume / tx_count
                
                # Update chains and tokens (stored as JSON)
                chains = set(json.loads(existing[5] or '[]'))
                chains.add(tx.chain)
                
                tokens = set(json.loads(existing[6] or '[]'))
                tokens.add(tx.token_symbol)
                
                whale_score = self.calculate_whale_score(total_volume, tx_count, len(chains), len(tokens))
                
                cursor.execute('''
                    UPDATE whale_addresses 
                    SET last_seen = ?, total_volume_usd = ?, transaction_count = ?,
                        avg_transaction_size = ?, chains_active = ?, tokens_traded = ?,
                        whale_score = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE address = ?
                ''', (
                    datetime.fromtimestamp(tx.timestamp),
                    total_volume, tx_count, avg_tx_size,
                    json.dumps(list(chains)), json.dumps(list(tokens)),
                    whale_score, address
                ))
            else:
                # Insert new record
                whale_score = self.calculate_whale_score(tx.value_usd, 1, 1, 1)
                
                cursor.execute('''
                    INSERT INTO whale_addresses
                    (address, first_seen, last_seen, total_volume_usd, transaction_count,
                     avg_transaction_size, chains_active, tokens_traded, whale_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    address,
                    datetime.fromtimestamp(tx.timestamp),
                    datetime.fromtimestamp(tx.timestamp),
                    tx.value_usd, 1, tx.value_usd,
                    json.dumps([tx.chain]),
                    json.dumps([tx.token_symbol]),
                    whale_score
                ))
    
    def update_address_relationship(self, from_addr: str, to_addr: str, volume: float):
        """Update relationship between addresses"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO address_relationships (from_address, to_address, total_volume_usd, last_interaction)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(from_address, to_address) DO UPDATE SET
                interaction_count = interaction_count + 1,
                total_volume_usd = total_volume_usd + ?,
                last_interaction = CURRENT_TIMESTAMP
            ''', (from_addr, to_addr, volume, volume))
    
    def calculate_whale_score(self, total_volume: float, tx_count: int, chain_count: int, token_count: int) -> float:
        """Calculate whale score based on multiple factors"""
        # Volume factor (max 500 points)
        volume_score = min(total_volume / 10000, 500)
        
        # Activity factor (max 200 points)
        activity_score = min(tx_count * 2, 200)
        
        # Diversification factors
        chain_score = chain_count * 20  # 20 points per chain
        token_score = token_count * 10  # 10 points per token
        
        return round(volume_score + activity_score + chain_score + token_score, 2)
    
    def get_top_whales(self, limit: int = 100) -> List[Dict]:
        """Get top whales by whale score"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT address, total_volume_usd, transaction_count, avg_transaction_size,
                       chains_active, tokens_traded, whale_score, first_seen, last_seen
                FROM whale_addresses
                ORDER BY whale_score DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_whale_transactions(self, address: str, limit: int = 100) -> List[Dict]:
        """Get all transactions for a specific whale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE from_address = ? OR to_address = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (address, address, limit))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_address_network(self, address: str, min_interactions: int = 2) -> Dict:
        """Get network of addresses that interact with the given address"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get relationships where this address is involved
            cursor.execute('''
                SELECT from_address, to_address, interaction_count, total_volume_usd
                FROM address_relationships
                WHERE (from_address = ? OR to_address = ?) AND interaction_count >= ?
                ORDER BY total_volume_usd DESC
            ''', (address, address, min_interactions))
            
            relationships = cursor.fetchall()
            
            # Build network graph data
            nodes = set([address])
            edges = []
            
            for from_addr, to_addr, count, volume in relationships:
                nodes.add(from_addr)
                nodes.add(to_addr)
                edges.append({
                    'from': from_addr,
                    'to': to_addr,
                    'interactions': count,
                    'volume': volume
                })
            
            return {
                'center_address': address,
                'nodes': list(nodes),
                'edges': edges,
                'network_size': len(nodes)
            }
    
    def analyze_trading_patterns(self, address: str, days: int = 30) -> Dict:
        """Analyze trading patterns for an address"""
        with sqlite3.connect(self.db_path) as conn:
            # Get transactions from last N days
            cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp())
            
            df = pd.read_sql_query('''
                SELECT timestamp, value_usd, token_symbol, 
                       CASE WHEN from_address = ? THEN 'out' ELSE 'in' END as direction
                FROM transactions 
                WHERE (from_address = ? OR to_address = ?) AND timestamp > ?
                ORDER BY timestamp
            ''', conn, params=(address, address, address, cutoff_time))
            
            if df.empty:
                return {'error': 'No transactions found'}
            
            # Convert timestamp to datetime
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df['hour'] = df['datetime'].dt.hour
            df['day_of_week'] = df['datetime'].dt.day_name()
            
            analysis = {
                'total_transactions': len(df),
                'total_volume': df['value_usd'].sum(),
                'avg_transaction_size': df['value_usd'].mean(),
                'volume_in': df[df['direction'] == 'in']['value_usd'].sum(),
                'volume_out': df[df['direction'] == 'out']['value_usd'].sum(),
                'most_active_hour': df['hour'].mode().iloc[0] if not df['hour'].mode().empty else None,
                'most_active_day': df['day_of_week'].mode().iloc[0] if not df['day_of_week'].mode().empty else None,
                'unique_tokens': df['token_symbol'].nunique(),
                'top_tokens': df['token_symbol'].value_counts().head(5).to_dict(),
                'daily_avg_transactions': len(df) / days,
                'largest_transaction': df['value_usd'].max(),
                'transaction_frequency_score': len(df) / days * 10  # Score out of 10 for frequency
            }
            
            return analysis
    
    def detect_unusual_activity(self, address: str, threshold_multiplier: float = 3.0) -> List[Dict]:
        """Detect unusual activity based on address's historical behavior"""
        with sqlite3.connect(self.db_path) as conn:
            # Get address stats
            cursor = conn.cursor()
            cursor.execute('''
                SELECT avg_transaction_size FROM whale_addresses WHERE address = ?
            ''', (address,))
            
            result = cursor.fetchone()
            if not result:
                return []
            
            avg_size = result[0]
            threshold = avg_size * threshold_multiplier
            
            # Find transactions above threshold
            cursor.execute('''
                SELECT hash, timestamp, value_usd, token_symbol
                FROM transactions 
                WHERE (from_address = ? OR to_address = ?) AND value_usd > ?
                ORDER BY timestamp DESC
                LIMIT 20
            ''', (address, address, threshold))
            
            unusual_txs = []
            for row in cursor.fetchall():
                unusual_txs.append({
                    'hash': row[0],
                    'timestamp': row[1],
                    'value_usd': row[2],
                    'token_symbol': row[3],
                    'multiplier': row[2] / avg_size if avg_size > 0 else 0
                })
            
            return unusual_txs
    
    def generate_daily_report(self, date: str = None) -> Dict:
        """Generate daily activity report"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get daily stats
            cursor.execute('''
                SELECT chain, COUNT(*) as tx_count, SUM(value_usd) as total_volume,
                       COUNT(DISTINCT from_address) + COUNT(DISTINCT to_address) as unique_addresses,
                       AVG(value_usd) as avg_tx_size
                FROM transactions 
                WHERE date(datetime(timestamp, 'unixepoch')) = ?
                GROUP BY chain
            ''', (date,))
            
            chain_stats = []
            total_volume = 0
            total_txs = 0
            
            for row in cursor.fetchall():
                stats = {
                    'chain': row[0],
                    'transactions': row[1],
                    'volume_usd': row[2],
                    'unique_addresses': row[3],
                    'avg_transaction_size': row[4]
                }
                chain_stats.append(stats)
                total_volume += row[2]
                total_txs += row[1]
            
            return {
                'date': date,
                'total_volume_usd': total_volume,
                'total_transactions': total_txs,
                'chain_breakdown': chain_stats
            }

class WhaleAnalytics:
    def __init__(self, db_path: str = "whale_tracker.db"):
        self.db = WhaleDatabase(db_path)
    
    def correlation_analysis(self, address1: str, address2: str) -> Dict:
        """Analyze correlation between two whale addresses"""
        with sqlite3.connect(self.db.db_path) as conn:
            # Get transaction timings for both addresses
            query = '''
                SELECT timestamp, value_usd, 
                       CASE WHEN from_address = ? OR to_address = ? THEN 'addr1' ELSE 'addr2' END as address
                FROM transactions 
                WHERE (from_address = ? OR to_address = ?) OR (from_address = ? OR to_address = ?)
                ORDER BY timestamp
            '''
            
            df = pd.read_sql_query(query, conn, params=(
                address1, address1, address1, address1, address2, address2
            ))
            
            if len(df) < 10:  # Need sufficient data
                return {'error': 'Insufficient data for correlation analysis'}
            
            # Create time-based correlation
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df['hour_bucket'] = df['datetime'].dt.floor('H')
            
            # Aggregate by hour
            hourly_activity = df.groupby(['hour_bucket', 'address'])['value_usd'].sum().unstack(fill_value=0)
            
            if len(hourly_activity.columns) == 2:
                correlation = hourly_activity.iloc[:, 0].corr(hourly_activity.iloc[:, 1])
                return {
                    'correlation_coefficient': correlation,
                    'interpretation': 'High' if abs(correlation) > 0.7 else 'Medium' if abs(correlation) > 0.3 else 'Low',
                    'data_points': len(hourly_activity)
                }
            
            return {'error': 'Unable to calculate correlation'}

# Example usage and testing
if __name__ == "__main__":
    # Initialize database
    db = WhaleDatabase()
    analytics = WhaleAnalytics()
    
    # Example transaction
    example_tx = WhaleTransaction(
        hash="0x123456789abcdef",
        chain="ethereum",
        from_address="0xabc123",
        to_address="0xdef456",
        token_symbol="USDT",
        token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        value_native=100000.0,
        value_usd=100000.0,
        timestamp=int(datetime.now().timestamp()),
        whale_category="LARGE_WHALE"
    )
    
    # Add transaction
    success = db.add_transaction(example_tx)
    print(f"Transaction added: {success}")
    
    # Get top whales
    top_whales = db.get_top_whales(10)
    print(f"Found {len(top_whales)} whales in database")
    
    # Generate daily report
    report = db.generate_daily_report()
    print(f"Daily report: {json.dumps(report, indent=2)}")