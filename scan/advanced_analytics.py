import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from collections import defaultdict, Counter
import networkx as nx
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class WhalePatternAnalyzer:
    def __init__(self, db_path: str = "whale_tracker.db"):
        self.db_path = db_path
        
    def get_data(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def detect_wash_trading(self, min_back_forth: int = 3, time_window_hours: int = 24) -> List[Dict]:
        """Detect potential wash trading patterns"""
        print("🔍 Analyzing wash trading patterns...")
        
        query = '''
            SELECT from_address, to_address, COUNT(*) as interaction_count,
                   GROUP_CONCAT(timestamp) as timestamps,
                   SUM(value_usd) as total_volume
            FROM transactions
            WHERE timestamp > ?
            GROUP BY from_address, to_address
            HAVING interaction_count >= ?
        '''
        
        cutoff = int((datetime.now() - timedelta(hours=time_window_hours)).timestamp())
        df = self.get_data(query, (cutoff, min_back_forth))
        
        wash_trading_pairs = []
        
        for _, row in df.iterrows():
            from_addr, to_addr = row['from_address'], row['to_address']
            
            # Check if there's reverse interaction
            reverse_query = '''
                SELECT COUNT(*) as reverse_count, SUM(value_usd) as reverse_volume
                FROM transactions
                WHERE from_address = ? AND to_address = ? AND timestamp > ?
            '''
            
            reverse_data = self.get_data(reverse_query, (to_addr, from_addr, cutoff))
            
            if not reverse_data.empty and reverse_data.iloc[0]['reverse_count'] > 0:
                # Potential wash trading detected
                wash_trading_pairs.append({
                    'address_a': from_addr,
                    'address_b': to_addr,
                    'forward_transactions': row['interaction_count'],
                    'reverse_transactions': reverse_data.iloc[0]['reverse_count'],
                    'forward_volume': row['total_volume'],
                    'reverse_volume': reverse_data.iloc[0]['reverse_volume'],
                    'wash_score': self.calculate_wash_score(
                        row['interaction_count'],
                        reverse_data.iloc[0]['reverse_count'],
                        row['total_volume'],
                        reverse_data.iloc[0]['reverse_volume']
                    )
                })
        
        return sorted(wash_trading_pairs, key=lambda x: x['wash_score'], reverse=True)
    
    def calculate_wash_score(self, forward_tx: int, reverse_tx: int, forward_vol: float, reverse_vol: float) -> float:
        """Calculate wash trading suspicion score"""
        # Balance of transactions
        tx_balance = 1 - abs(forward_tx - reverse_tx) / max(forward_tx + reverse_tx, 1)
        
        # Volume balance
        vol_balance = 1 - abs(forward_vol - reverse_vol) / max(forward_vol + reverse_vol, 1)
        
        # Frequency factor
        frequency_factor = min((forward_tx + reverse_tx) / 10, 1)
        
        return round((tx_balance * 40 + vol_balance * 40 + frequency_factor * 20), 2)
    
    def detect_coordinated_trading(self, time_threshold_minutes: int = 10) -> List[Dict]:
        """Detect coordinated trading between multiple addresses"""
        print("🤝 Analyzing coordinated trading patterns...")
        
        query = '''
            SELECT timestamp, from_address, to_address, value_usd, token_symbol
            FROM transactions
            WHERE timestamp > ?
            ORDER BY timestamp
        '''
        
        cutoff = int((datetime.now() - timedelta(days=7)).timestamp())
        df = self.get_data(query, (cutoff,))
        
        if df.empty:
            return []
        
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        coordinated_groups = []
        
        # Group transactions by time windows
        df['time_group'] = df['datetime'].dt.floor(f'{time_threshold_minutes}min')
        
        for time_group, group_df in df.groupby('time_group'):
            if len(group_df) < 3:  # Need at least 3 transactions for coordination
                continue
            
            # Analyze if multiple addresses are trading the same tokens
            token_traders = defaultdict(set)
            
            for _, row in group_df.iterrows():
                token_traders[row['token_symbol']].add(row['from_address'])
                token_traders[row['token_symbol']].add(row['to_address'])
            
            # Find tokens with multiple unique addresses
            for token, addresses in token_traders.items():
                if len(addresses) >= 4:  # At least 4 different addresses
                    total_volume = group_df[group_df['token_symbol'] == token]['value_usd'].sum()
                    
                    if total_volume > 50000:  # Significant volume
                        coordinated_groups.append({
                            'timestamp': time_group,
                            'token': token,
                            'addresses_involved': list(addresses),
                            'transaction_count': len(group_df[group_df['token_symbol'] == token]),
                            'total_volume': total_volume,
                            'coordination_score': len(addresses) * np.log(total_volume / 10000)
                        })
        
        return sorted(coordinated_groups, key=lambda x: x['coordination_score'], reverse=True)
    
    def analyze_market_impact(self, large_tx_threshold: float = 500000) -> Dict:
        """Analyze market impact of large transactions"""
        print("📈 Analyzing market impact patterns...")
        
        query = '''
            SELECT timestamp, value_usd, token_symbol, from_address, to_address
            FROM transactions
            WHERE value_usd > ?
            ORDER BY timestamp
        '''
        
        df = self.get_data(query, (large_tx_threshold,))
        
        if df.empty:
            return {'error': 'No large transactions found'}
        
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Group by token and analyze timing patterns
        token_analysis = {}
        
        for token in df['token_symbol'].unique():
            token_df = df[df['token_symbol'] == token].sort_values('timestamp')
            
            if len(token_df) < 2:
                continue
            
            # Calculate time intervals between large transactions
            time_diffs = token_df['datetime'].diff().dt.total_seconds() / 3600  # hours
            
            token_analysis[token] = {
                'large_tx_count': len(token_df),
                'total_volume': token_df['value_usd'].sum(),
                'avg_tx_size': token_df['value_usd'].mean(),
                'avg_time_between_large_tx_hours': time_diffs.mean(),
                'unique_whales': len(set(token_df['from_address'].tolist() + token_df['to_address'].tolist())),
                'clustering_coefficient': self.calculate_transaction_clustering(token_df)
            }
        
        return token_analysis
    
    def calculate_transaction_clustering(self, df: pd.DataFrame) -> float:
        """Calculate how clustered transactions are in time"""
        if len(df) < 3:
            return 0
        
        timestamps = df['timestamp'].values
        time_diffs = np.diff(sorted(timestamps))
        
        # Calculate coefficient of variation for time differences
        if len(time_diffs) > 0 and np.mean(time_diffs) > 0:
            return np.std(time_diffs) / np.mean(time_diffs)
        
        return 0
    
    def detect_pump_dump_patterns(self, volume_spike_threshold: float = 5.0) -> List[Dict]:
        """Detect potential pump and dump patterns"""
        print("🚨 Analyzing pump & dump patterns...")
        
        query = '''
            SELECT DATE(datetime(timestamp, 'unixepoch')) as date,
                   token_symbol,
                   SUM(value_usd) as daily_volume,
                   COUNT(*) as tx_count,
                   MAX(value_usd) as largest_tx
            FROM transactions
            WHERE timestamp > ?
            GROUP BY date, token_symbol
            HAVING daily_volume > 100000
            ORDER BY date, token_symbol
        '''
        
        cutoff = int((datetime.now() - timedelta(days=30)).timestamp())
        df = self.get_data(query, (cutoff,))
        
        if df.empty:
            return []
        
        pump_dump_candidates = []
        
        # Analyze each token for volume spikes
        for token in df['token_symbol'].unique():
            token_df = df[df['token_symbol'] == token].sort_values('date')
            
            if len(token_df) < 7:  # Need at least a week of data
                continue
            
            # Calculate rolling average volume
            token_df['volume_ma7'] = token_df['daily_volume'].rolling(window=7, min_periods=3).mean()
            
            # Find volume spikes
            token_df['volume_spike'] = token_df['daily_volume'] / token_df['volume_ma7']
            
            # Detect pump patterns (volume spike followed by decline)
            for i in range(1, len(token_df) - 1):
                if token_df.iloc[i]['volume_spike'] > volume_spike_threshold:
                    # Check if followed by decline
                    if i < len(token_df) - 2:
                        next_volume = token_df.iloc[i + 1]['daily_volume']
                        decline_ratio = next_volume / token_df.iloc[i]['daily_volume']
                        
                        if decline_ratio < 0.5:  # 50% decline
                            pump_dump_candidates.append({
                                'token': token,
                                'pump_date': token_df.iloc[i]['date'],
                                'pump_volume': token_df.iloc[i]['daily_volume'],
                                'baseline_volume': token_df.iloc[i]['volume_ma7'],
                                'volume_spike_ratio': token_df.iloc[i]['volume_spike'],
                                'decline_ratio': decline_ratio,
                                'pump_score': token_df.iloc[i]['volume_spike'] * (1 - decline_ratio)
                            })
        
        return sorted(pump_dump_candidates, key=lambda x: x['pump_score'], reverse=True)
    
    def build_whale_network(self, min_interaction_volume: float = 100000) -> Dict:
        """Build network graph of whale interactions"""
        print("🕸️ Building whale interaction network...")
        
        query = '''
            SELECT from_address, to_address, SUM(value_usd) as total_volume,
                   COUNT(*) as interaction_count
            FROM transactions
            WHERE value_usd > ?
            GROUP BY from_address, to_address
            HAVING total_volume > ?
        '''
        
        df = self.get_data(query, (50000, min_interaction_volume))
        
        if df.empty:
            return {'error': 'No qualifying interactions found'}
        
        # Build network graph
        G = nx.from_pandas_edgelist(
            df, 
            source='from_address', 
            target='to_address',
            edge_attr=['total_volume', 'interaction_count'],
            create_using=nx.DiGraph()
        )
        
        # Calculate network metrics
        network_metrics = {
            'node_count': G.number_of_nodes(),
            'edge_count': G.number_of_edges(),
            'density': nx.density(G),
            'average_clustering': nx.average_clustering(G.to_undirected()),
        }
        
        # Find central nodes
        centrality = nx.degree_centrality(G)
        betweenness = nx.betweenness_centrality(G)
        
        # Top nodes by centrality
        top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Detect communities
        G_undirected = G.to_undirected()
        communities = list(nx.community.greedy_modularity_communities(G_undirected))
        
        return {
            'network_metrics': network_metrics,
            'top_central_nodes': [{'address': addr, 'centrality': score} for addr, score in top_central],
            'top_bridge_nodes': [{'address': addr, 'betweenness': score} for addr, score in top_betweenness],
            'community_count': len(communities),
            'largest_community_size': max(len(c) for c in communities) if communities else 0,
            'communities': [list(c) for c in communities[:5]]  # Top 5 communities
        }
    
    def detect_arbitrage_opportunities(self, time_window_minutes: int = 30) -> List[Dict]:
        """Detect potential arbitrage opportunities based on whale movements"""
        print("⚖️ Analyzing arbitrage patterns...")
        
        query = '''
            SELECT timestamp, from_address, to_address, value_usd, token_symbol, chain
            FROM transactions
            WHERE timestamp > ?
            ORDER BY timestamp
        '''
        
        cutoff = int((datetime.now() - timedelta(days=3)).timestamp())
        df = self.get_data(query, (cutoff,))
        
        if df.empty:
            return []
        
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        arbitrage_opportunities = []
        
        # Group by time windows
        df['time_window'] = df['datetime'].dt.floor(f'{time_window_minutes}min')
        
        for window, window_df in df.groupby('time_window'):
            # Look for same token traded on different chains
            token_chain_activity = defaultdict(lambda: defaultdict(list))
            
            for _, row in window_df.iterrows():
                token_chain_activity[row['token_symbol']][row['chain']].append({
                    'volume': row['value_usd'],
                    'from': row['from_address'],
                    'to': row['to_address']
                })
            
            # Find tokens active on multiple chains
            for token, chain_data in token_chain_activity.items():
                if len(chain_data) > 1:  # Multi-chain activity
                    total_volume = sum(
                        sum(tx['volume'] for tx in chain_txs)
                        for chain_txs in chain_data.values()
                    )
                    
                    if total_volume > 200000:  # Significant volume
                        arbitrage_opportunities.append({
                            'timestamp': window,
                            'token': token,
                            'chains': list(chain_data.keys()),
                            'total_volume': total_volume,
                            'chain_volumes': {
                                chain: sum(tx['volume'] for tx in txs)
                                for chain, txs in chain_data.items()
                            },
                            'arbitrage_score': len(chain_data) * np.log(total_volume / 50000)
                        })
        
        return sorted(arbitrage_opportunities, key=lambda x: x['arbitrage_score'], reverse=True)
    
    def cluster_whale_behavior(self, n_clusters: int = 5) -> Dict:
        """Cluster whales based on trading behavior"""
        print("🎯 Clustering whale behavior patterns...")
        
        # Get whale statistics
        query = '''
            SELECT address, total_volume_usd, transaction_count, avg_transaction_size,
                   whale_score, chains_active, tokens_traded
            FROM whale_addresses
            WHERE transaction_count > 5
        '''
        
        df = self.get_data(query)
        
        if len(df) < n_clusters:
            return {'error': 'Not enough whales for clustering'}
        
        # Prepare features for clustering
        features = []
        addresses = []
        
        for _, row in df.iterrows():
            chains = len(json.loads(row['chains_active'] or '[]'))
            tokens = len(json.loads(row['tokens_traded'] or '[]'))
            
            feature_vector = [
                np.log(row['total_volume_usd'] + 1),
                np.log(row['transaction_count'] + 1),
                np.log(row['avg_transaction_size'] + 1),
                chains,
                tokens,
                row['whale_score']
            ]
            
            features.append(feature_vector)
            addresses.append(row['address'])
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Perform clustering
        clusterer = DBSCAN(eps=0.5, min_samples=2)
        cluster_labels = clusterer.fit_predict(features_scaled)
        
        # Analyze clusters
        clusters = defaultdict(list)
        for addr, label in zip(addresses, cluster_labels):
            clusters[label].append(addr)
        
        cluster_analysis = {}
        for label, cluster_addresses in clusters.items():
            if label == -1:  # Noise cluster
                continue
            
            # Get stats for this cluster
            cluster_df = df[df['address'].isin(cluster_addresses)]
            
            cluster_analysis[f'cluster_{label}'] = {
                'size': len(cluster_addresses),
                'addresses': cluster_addresses[:10],  # Top 10 addresses
                'avg_volume': cluster_df['total_volume_usd'].mean(),
                'avg_transaction_count': cluster_df['transaction_count'].mean(),
                'avg_whale_score': cluster_df['whale_score'].mean(),
                'characteristics': self.describe_cluster_characteristics(cluster_df)
            }
        
        return {
            'total_whales_analyzed': len(addresses),
            'clusters_found': len(cluster_analysis),
            'noise_points': len(clusters.get(-1, [])),
            'cluster_details': cluster_analysis
        }
    
    def describe_cluster_characteristics(self, cluster_df: pd.DataFrame) -> str:
        """Describe the characteristics of a whale cluster"""
        avg_volume = cluster_df['total_volume_usd'].mean()
        avg_tx_count = cluster_df['transaction_count'].mean()
        avg_tx_size = cluster_df['avg_transaction_size'].mean()
        
        if avg_volume > 1000000 and avg_tx_size > 100000:
            return "Ultra High-Value Traders"
        elif avg_tx_count > 50 and avg_tx_size < 50000:
            return "High-Frequency Small Traders"
        elif avg_tx_size > 200000:
            return "Large Block Traders"
        elif avg_tx_count > 30:
            return "Active Regular Traders"
        else:
            return "Moderate Activity Traders"
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive analytics report"""
        print("📊 Generating comprehensive whale analytics report...")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'wash_trading': self.detect_wash_trading()[:5],
            'coordinated_trading': self.detect_coordinated_trading()[:5],
            'market_impact': self.analyze_market_impact(),
            'pump_dump_patterns': self.detect_pump_dump_patterns()[:5],
            'network_analysis': self.build_whale_network(),
            'arbitrage_patterns': self.detect_arbitrage_opportunities()[:5],
            'whale_clusters': self.cluster_whale_behavior()
        }
        
        return report

# Example usage
if __name__ == "__main__":
    analyzer = WhalePatternAnalyzer()
    
    print("🐋 Starting comprehensive whale pattern analysis...")
    
    # Generate full report
    report = analyzer.generate_comprehensive_report()
    
    # Save report
    with open('whale_analytics_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n📈 Analysis Summary:")
    print(f"- Wash Trading Pairs Found: {len(report.get('wash_trading', []))}")
    print(f"- Coordinated Trading Events: {len(report.get('coordinated_trading', []))}")
    print(f"- Pump & Dump Candidates: {len(report.get('pump_dump_patterns', []))}")
    print(f"- Arbitrage Opportunities: {len(report.get('arbitrage_patterns', []))}")
    
    if 'network_analysis' in report and 'network_metrics' in report['network_analysis']:
        network = report['network_analysis']['network_metrics']
        print(f"- Network Size: {network['node_count']} nodes, {network['edge_count']} edges")
    
    if 'whale_clusters' in report and 'clusters_found' in report['whale_clusters']:
        print(f"- Whale Clusters: {report['whale_clusters']['clusters_found']} behavioral groups")
    
    print(f"\n💾 Full report saved to: whale_analytics_report.json")