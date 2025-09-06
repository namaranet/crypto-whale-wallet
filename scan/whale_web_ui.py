#!/usr/bin/env python3
"""
Whale Tracker Web UI - Flask Dashboard
Simple web interface to browse whale database and analytics
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd
from address_labels import get_address_info, get_address_label, get_address_exchange, get_address_type

app = Flask(__name__)
app.config['SECRET_KEY'] = 'whale-tracker-secret-key'

# Add custom template filters
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime_filter(timestamp):
    """Convert timestamp to datetime object"""
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
    return timestamp

@app.template_filter('format_time')
def format_time_filter(timestamp):
    """Format timestamp as readable time"""
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        return dt.strftime('%H:%M')
    return str(timestamp)

@app.template_filter('format_date')
def format_date_filter(timestamp):
    """Format timestamp as readable date"""
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        return dt.strftime('%m/%d %H:%M')
    return str(timestamp)

class WhaleWebDB:
    def __init__(self, db_path="whale_tracker.db"):
        self.db_path = db_path
        self.init_sample_data()
    
    def init_sample_data(self):
        """Initialize with sample data if database is empty"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if we have data - DISABLED since we now have real data
            cursor.execute("SELECT COUNT(*) FROM whale_addresses")
            if cursor.fetchone()[0] == 0 and False:  # Disabled sample data
                # Add sample whale data
                sample_whales = [
                    {
                        'address': '0x365084b05fa7d5028346bd21d842ed0601bab5b8',
                        'total_volume_usd': 999803.19,
                        'transaction_count': 15,
                        'avg_transaction_size': 66653.55,
                        'whale_score': 143.97,
                        'chains_active': '["ethereum"]',
                        'tokens_traded': '["USDT", "WETH"]'
                    },
                    {
                        'address': '0x70bf6634ee8cb27d04478f184b9b8bb13e5f4710',
                        'total_volume_usd': 856200.45,
                        'transaction_count': 12,
                        'avg_transaction_size': 71350.04,
                        'whale_score': 128.75,
                        'chains_active': '["ethereum", "polygon"]',
                        'tokens_traded': '["USDT", "USDC"]'
                    },
                    {
                        'address': '0xfd386f4443fadd5479ff1078c7e9219f47836bdb',
                        'total_volume_usd': 623445.78,
                        'transaction_count': 8,
                        'avg_transaction_size': 77930.72,
                        'whale_score': 104.20,
                        'chains_active': '["ethereum"]',
                        'tokens_traded': '["WBTC", "ETH"]'
                    }
                ]
                
                for whale in sample_whales:
                    cursor.execute('''
                        INSERT OR REPLACE INTO whale_addresses 
                        (address, total_volume_usd, transaction_count, avg_transaction_size, 
                         whale_score, chains_active, tokens_traded, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        whale['address'],
                        whale['total_volume_usd'],
                        whale['transaction_count'], 
                        whale['avg_transaction_size'],
                        whale['whale_score'],
                        whale['chains_active'],
                        whale['tokens_traded'],
                        datetime.now(),
                        datetime.now()
                    ))
                
                # Add sample transactions
                sample_transactions = [
                    {
                        'hash': '0xa8022293a1bf9123e789f2341567890abcdef123',
                        'chain': 'ethereum',
                        'from_address': '0x365084b05fa7d5028346bd21d842ed0601bab5b8',
                        'to_address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
                        'token_symbol': 'USDT',
                        'value_native': 500000,
                        'value_usd': 500000,
                        'timestamp': int((datetime.now() - timedelta(hours=2)).timestamp()),
                        'whale_category': '🦈 MEGA WHALE'
                    },
                    {
                        'hash': '0xb9133304b2cf0234f890g3452678901bcdefg234',
                        'chain': 'ethereum',
                        'from_address': '0x70bf6634ee8cb27d04478f184b9b8bb13e5f4710',
                        'to_address': '0x28C6c06298d514Db089934071355E5743bf21d60',
                        'token_symbol': 'WETH',
                        'value_native': 150.5,
                        'value_usd': 643637.5,
                        'timestamp': int((datetime.now() - timedelta(hours=1)).timestamp()),
                        'whale_category': '🦈 MEGA WHALE'
                    }
                ]
                
                for tx in sample_transactions:
                    cursor.execute('''
                        INSERT OR IGNORE INTO transactions
                        (hash, chain, from_address, to_address, token_symbol, 
                         value_native, value_usd, timestamp, whale_category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        tx['hash'], tx['chain'], tx['from_address'], tx['to_address'],
                        tx['token_symbol'], tx['value_native'], tx['value_usd'], 
                        tx['timestamp'], tx['whale_category']
                    ))
                
                conn.commit()
    
    def get_top_whales(self, limit=50):
        """Get top whales by score"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT address, total_volume_usd, transaction_count, avg_transaction_size,
                       whale_score, chains_active, tokens_traded, first_seen, last_seen
                FROM whale_addresses
                ORDER BY whale_score DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            whales = []
            for row in cursor.fetchall():
                whale = dict(zip(columns, row))
                # Parse JSON fields
                whale['chains_active'] = json.loads(whale['chains_active'] or '[]')
                whale['tokens_traded'] = json.loads(whale['tokens_traded'] or '[]')
                whales.append(whale)
            
            return whales
    
    def get_recent_transactions(self, limit=100):
        """Get recent transactions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT hash, chain, from_address, to_address, token_symbol,
                       value_native, value_usd, timestamp, whale_category
                FROM transactions
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_whale_details(self, address):
        """Get details for specific whale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get whale info
            cursor.execute('''
                SELECT * FROM whale_addresses WHERE address = ?
            ''', (address,))
            
            whale_data = cursor.fetchone()
            if not whale_data:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            whale = dict(zip(columns, whale_data))
            whale['chains_active'] = json.loads(whale['chains_active'] or '[]')
            whale['tokens_traded'] = json.loads(whale['tokens_traded'] or '[]')
            
            # Get transactions
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE from_address = ? OR to_address = ?
                ORDER BY timestamp DESC
                LIMIT 50
            ''', (address, address))
            
            tx_columns = [desc[0] for desc in cursor.description]
            whale['transactions'] = [dict(zip(tx_columns, row)) for row in cursor.fetchall()]
            
            return whale
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total whales
            cursor.execute("SELECT COUNT(*) FROM whale_addresses")
            total_whales = cursor.fetchone()[0]
            
            # Total volume
            cursor.execute("SELECT SUM(total_volume_usd) FROM whale_addresses")
            total_volume = cursor.fetchone()[0] or 0
            
            # Total transactions
            cursor.execute("SELECT COUNT(*) FROM transactions")
            total_transactions = cursor.fetchone()[0]
            
            # Recent activity (last 24 hours)
            yesterday = int((datetime.now() - timedelta(days=1)).timestamp())
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE timestamp > ?", (yesterday,))
            recent_activity = cursor.fetchone()[0]
            
            # Chain breakdown
            cursor.execute('''
                SELECT chain, COUNT(*) as count, SUM(value_usd) as volume
                FROM transactions 
                GROUP BY chain
                ORDER BY volume DESC
            ''')
            chain_stats = [{'chain': row[0], 'count': row[1], 'volume': row[2]} 
                          for row in cursor.fetchall()]
            
            return {
                'total_whales': total_whales,
                'total_volume': total_volume,
                'total_transactions': total_transactions,
                'recent_activity': recent_activity,
                'chain_stats': chain_stats
            }
    
    def get_network_graph(self):
        """Get network graph data for all whales"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get transaction relationships
            cursor.execute('''
                SELECT from_address, to_address, COUNT(*) as tx_count, SUM(value_usd) as total_volume
                FROM transactions
                WHERE value_usd > 10000
                GROUP BY from_address, to_address
                HAVING tx_count >= 1
                ORDER BY total_volume DESC
                LIMIT 100
            ''')
            
            relationships = cursor.fetchall()
            
            # Get whale info for nodes
            cursor.execute('SELECT address, whale_score, total_volume_usd FROM whale_addresses')
            whales = {row[0]: {'score': row[1], 'volume': row[2]} for row in cursor.fetchall()}
            
            # Build network data
            nodes = {}
            edges = []
            
            for from_addr, to_addr, tx_count, volume in relationships:
                # Add nodes
                for addr in [from_addr, to_addr]:
                    if addr not in nodes:
                        is_whale = addr in whales
                        addr_info = get_address_info(addr)
                        
                        # Determine node type based on whale status and address info
                        if is_whale:
                            node_type = 'whale'
                        elif addr_info['type'] == 'exchange':
                            node_type = 'exchange'
                        elif addr_info['type'] == 'protocol':
                            node_type = 'protocol'
                        else:
                            node_type = 'regular'
                        
                        nodes[addr] = {
                            'id': addr,
                            'label': addr_info['label'],
                            'type': node_type,
                            'score': whales.get(addr, {}).get('score', 0),
                            'volume': whales.get(addr, {}).get('volume', 0),
                            'size': min(max(whales.get(addr, {}).get('score', 10) / 10, 5), 30) if is_whale else 5,
                            'exchange': addr_info['exchange'],
                            'chain': addr_info['chain'],
                            'address_type': addr_info['type']
                        }
                
                # Add edge
                edges.append({
                    'source': from_addr,
                    'target': to_addr,
                    'weight': tx_count,
                    'volume': volume,
                    'width': min(max(tx_count, 1), 10)
                })
            
            return {
                'nodes': list(nodes.values()),
                'edges': edges,
                'stats': {
                    'node_count': len(nodes),
                    'edge_count': len(edges),
                    'whale_count': len([n for n in nodes.values() if n['type'] == 'whale'])
                }
            }
    
    def get_whale_network_data(self, whale_address):
        """Get network data centered on specific whale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get direct relationships for this whale
            cursor.execute('''
                SELECT from_address, to_address, COUNT(*) as tx_count, SUM(value_usd) as total_volume
                FROM transactions
                WHERE (from_address = ? OR to_address = ?) AND value_usd > 5000
                GROUP BY from_address, to_address
                ORDER BY total_volume DESC
                LIMIT 50
            ''', (whale_address, whale_address))
            
            relationships = cursor.fetchall()
            
            # Get whale info
            cursor.execute('SELECT address, whale_score, total_volume_usd FROM whale_addresses')
            whales = {row[0]: {'score': row[1], 'volume': row[2]} for row in cursor.fetchall()}
            
            # Build network centered on target whale
            nodes = {}
            edges = []
            
            # Add center whale
            center_whale = whales.get(whale_address, {})
            center_info = get_address_info(whale_address)
            nodes[whale_address] = {
                'id': whale_address,
                'label': center_info['label'] if center_info['type'] != 'unknown' else f"{whale_address[:10]}...",
                'type': 'center_whale',
                'score': center_whale.get('score', 0),
                'volume': center_whale.get('volume', 0),
                'size': 40,
                'exchange': center_info['exchange'],
                'chain': center_info['chain'],
                'address_type': center_info['type']
            }
            
            for from_addr, to_addr, tx_count, volume in relationships:
                # Add connected nodes
                for addr in [from_addr, to_addr]:
                    if addr != whale_address and addr not in nodes:
                        is_whale = addr in whales
                        addr_data = whales.get(addr, {})
                        addr_info = get_address_info(addr)
                        
                        # Determine node type based on whale status and address info
                        if is_whale:
                            node_type = 'whale'
                        elif addr_info['type'] == 'exchange':
                            node_type = 'exchange'
                        elif addr_info['type'] == 'protocol':
                            node_type = 'protocol'
                        else:
                            node_type = 'regular'
                        
                        nodes[addr] = {
                            'id': addr,
                            'label': addr_info['label'],
                            'type': node_type,
                            'score': addr_data.get('score', 0),
                            'volume': addr_data.get('volume', 0),
                            'size': min(max(addr_data.get('score', 10) / 5, 8), 25) if is_whale else 8,
                            'exchange': addr_info['exchange'],
                            'chain': addr_info['chain'],
                            'address_type': addr_info['type']
                        }
                
                # Add edge
                edges.append({
                    'source': from_addr,
                    'target': to_addr,
                    'weight': tx_count,
                    'volume': volume,
                    'width': min(max(tx_count * 2, 1), 8)
                })
            
            return {
                'nodes': list(nodes.values()),
                'edges': edges,
                'center': whale_address,
                'stats': {
                    'connected_nodes': len(nodes) - 1,
                    'total_connections': len(edges),
                    'center_whale_score': center_whale.get('score', 0)
                }
            }

# Initialize database
db = WhaleWebDB()

@app.route('/')
def dashboard():
    """Main dashboard"""
    stats = db.get_dashboard_stats()
    recent_transactions = db.get_recent_transactions(10)
    top_whales = db.get_top_whales(10)
    
    return render_template('dashboard.html', 
                         stats=stats,
                         recent_transactions=recent_transactions,
                         top_whales=top_whales)

@app.route('/whales')
def whales_list():
    """Whales listing page"""
    page = int(request.args.get('page', 1))
    per_page = 20
    
    whales = db.get_top_whales(page * per_page)
    
    return render_template('whales.html', whales=whales, page=page)

@app.route('/whale/<address>')
def whale_detail(address):
    """Whale detail page"""
    whale = db.get_whale_details(address)
    
    if not whale:
        return "Whale not found", 404
    
    return render_template('whale_detail.html', whale=whale)

@app.route('/transactions')
def transactions_list():
    """Transactions listing page"""
    page = int(request.args.get('page', 1))
    per_page = 50
    
    transactions = db.get_recent_transactions(page * per_page)
    
    return render_template('transactions.html', transactions=transactions, page=page)

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard stats"""
    return jsonify(db.get_dashboard_stats())

@app.route('/api/whales')
def api_whales():
    """API endpoint for whales data"""
    limit = int(request.args.get('limit', 50))
    return jsonify(db.get_top_whales(limit))

@app.route('/api/transactions')
def api_transactions():
    """API endpoint for transactions"""
    limit = int(request.args.get('limit', 100))
    return jsonify(db.get_recent_transactions(limit))

@app.route('/network')
def network_graph():
    """Network graph visualization page"""
    return render_template('network.html')

@app.route('/network/<address>')
def whale_network_graph(address):
    """Network graph for specific whale"""
    whale = db.get_whale_details(address)
    if not whale:
        return "Whale not found", 404
    return render_template('whale_network.html', whale=whale)

@app.route('/api/network')
def api_network():
    """API endpoint for overall network data"""
    network_data = db.get_network_graph()
    return jsonify(network_data)

@app.route('/api/network/<address>')
def api_whale_network(address):
    """API endpoint for whale-specific network"""
    network_data = db.get_whale_network_data(address)
    return jsonify(network_data)

if __name__ == '__main__':
    print("🐋 Starting Whale Tracker Web UI...")
    print("📊 Dashboard available at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)