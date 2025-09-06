#!/usr/bin/env python3
"""
Crypto Whale Tracker - Main Orchestration Script
Advanced whale detection and tracking system with multi-chain support
"""

import argparse
import json
import time
from typing import Dict, List
from datetime import datetime

# Import our modules
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Helper functions for demo
def get_token_price(token_address):
    return 1.0

def get_transactions(address):
    return []

def classify_whale_size(usd_value):
    if usd_value >= 1000000:
        return "🐋 ULTRA WHALE"
    elif usd_value >= 500000:
        return "🦈 MEGA WHALE"
    elif usd_value >= 100000:
        return "🐳 LARGE WHALE"
    else:
        return "🐠 Regular"

# Import main classes with error handling
try:
    from whale_discovery import WhaleHunter
except ImportError:
    WhaleHunter = None

try:
    from multichain_tracker import MultiChainWhaleTracker
except ImportError:
    MultiChainWhaleTracker = None

try:
    from database_analytics import WhaleDatabase, WhaleTransaction, WhaleAnalytics
except ImportError:
    WhaleDatabase = None
    WhaleTransaction = None
    WhaleAnalytics = None

try:
    from advanced_analytics import WhalePatternAnalyzer
except ImportError:
    WhalePatternAnalyzer = None

class WhaleTrackerOrchestrator:
    def __init__(self, config: Dict):
        self.config = config
        self.db = WhaleDatabase() if WhaleDatabase else None
        self.analytics = WhaleAnalytics() if WhaleAnalytics else None
        self.pattern_analyzer = WhalePatternAnalyzer() if WhalePatternAnalyzer else None
        self.multichain_tracker = MultiChainWhaleTracker() if MultiChainWhaleTracker else None
        
    def run_whale_discovery(self) -> List[Dict]:
        """Run whale discovery process"""
        print("🔍 Starting whale discovery...")
        hunter = WhaleHunter()
        whales = hunter.run_discovery()
        
        print(f"✅ Discovered {len(whales)} potential whales")
        return whales
    
    def track_known_addresses(self, addresses: List[str]) -> Dict:
        """Track known whale addresses across all chains"""
        print(f"📊 Tracking {len(addresses)} known addresses...")
        
        results = self.multichain_tracker.batch_scan_addresses(addresses)
        transactions = self.multichain_tracker.save_multichain_results(results)
        
        # Store in database
        for tx_data in transactions:
            tx = WhaleTransaction(
                hash=tx_data['hash'],
                chain=tx_data['chain'],
                from_address=tx_data['from'],
                to_address=tx_data['to'],
                token_symbol=tx_data['token'],
                token_address=tx_data.get('token_address', ''),
                value_native=tx_data['value_native'],
                value_usd=tx_data['value_usd'],
                timestamp=tx_data['timestamp'],
                whale_category=classify_whale_size(tx_data['value_usd'])
            )
            self.db.add_transaction(tx)
        
        print(f"✅ Processed {len(transactions)} whale transactions")
        return results
    
    def run_pattern_analysis(self) -> Dict:
        """Run advanced pattern analysis"""
        print("🧠 Running pattern analysis...")
        return self.pattern_analyzer.generate_comprehensive_report()
    
    def generate_whale_report(self, limit: int = 50) -> Dict:
        """Generate comprehensive whale report"""
        print("📈 Generating whale report...")
        
        # Get top whales
        top_whales = self.db.get_top_whales(limit)
        
        # Get daily stats
        daily_stats = self.db.generate_daily_report()
        
        # Get network analysis for top whale
        network_data = {}
        if top_whales:
            network_data = self.db.get_address_network(top_whales[0]['address'])
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_whales_tracked': len(top_whales),
                'daily_stats': daily_stats
            },
            'top_whales': top_whales[:20],
            'network_analysis': network_data,
        }
        
        return report
    
    def run_monitoring_loop(self, addresses: List[str], interval_minutes: int = 30):
        """Run continuous monitoring loop"""
        print(f"🔄 Starting monitoring loop (checking every {interval_minutes} minutes)...")
        
        while True:
            try:
                print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Running whale scan...")
                
                # Track known addresses
                self.track_known_addresses(addresses)
                
                # Run pattern analysis periodically (every 6 hours)
                current_hour = datetime.now().hour
                if current_hour % 6 == 0:
                    pattern_report = self.run_pattern_analysis()
                    
                    # Save pattern analysis
                    with open(f"pattern_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json", 'w') as f:
                        json.dump(pattern_report, f, indent=2, default=str)
                
                print("✅ Scan complete, sleeping...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

def load_config(config_path: str = "config.json") -> Dict:
    """Load configuration from file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default config
        return {
            "whale_thresholds": {
                "large": 100000,
                "mega": 500000,
                "ultra": 1000000
            },
            "api_keys": {
                "etherscan": "YOUR_ETHERSCAN_API_KEY",
                "polygonscan": "YOUR_POLYGONSCAN_API_KEY",
                "bscscan": "YOUR_BSCSCAN_API_KEY"
            },
            "telegram": {
                "token": "YOUR_TELEGRAM_BOT_TOKEN",
                "chat_id": "YOUR_CHAT_ID"
            },
            "monitoring": {
                "interval_minutes": 30,
                "enable_notifications": True
            }
        }

def create_sample_config():
    """Create sample configuration file"""
    config = {
        "whale_thresholds": {
            "large": 100000,
            "mega": 500000,
            "ultra": 1000000
        },
        "api_keys": {
            "etherscan": "YOUR_ETHERSCAN_API_KEY",
            "polygonscan": "YOUR_POLYGONSCAN_API_KEY",
            "bscscan": "YOUR_BSCSCAN_API_KEY",
            "arbiscan": "YOUR_ARBISCAN_API_KEY",
            "optimism": "YOUR_OPTIMISM_API_KEY"
        },
        "telegram": {
            "token": "YOUR_TELEGRAM_BOT_TOKEN",
            "chat_id": "YOUR_CHAT_ID"
        },
        "monitoring": {
            "interval_minutes": 30,
            "enable_notifications": True
        },
        "known_whales": [
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Bitfinex
            "0x28C6c06298d514Db089934071355E5743bf21d60",  # Binance
            "0x8484Ef722627bf18ca5Ae6BcF031c23E6e922B30",  # Whale example
        ]
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("📁 Sample config.json created! Please update with your API keys.")

def main():
    parser = argparse.ArgumentParser(description="Crypto Whale Tracker")
    parser.add_argument('--mode', choices=['discover', 'track', 'analyze', 'monitor', 'report', 'setup'], 
                       required=True, help='Operation mode')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--addresses', nargs='+', help='Specific addresses to track')
    parser.add_argument('--output', default='whale_report.json', help='Output file for reports')
    
    args = parser.parse_args()
    
    if args.mode == 'setup':
        create_sample_config()
        return
    
    # Load configuration
    config = load_config(args.config)
    orchestrator = WhaleTrackerOrchestrator(config)
    
    if args.mode == 'discover':
        print("🎯 Running whale discovery...")
        whales = orchestrator.run_whale_discovery()
        
        with open('discovered_whales.json', 'w') as f:
            json.dump(whales, f, indent=2, default=str)
        
        print(f"💾 Discovered whales saved to discovered_whales.json")
    
    elif args.mode == 'track':
        addresses = args.addresses or config.get('known_whales', [])
        if not addresses:
            print("❌ No addresses to track. Use --addresses or add 'known_whales' to config.")
            return
        
        print(f"📊 Tracking {len(addresses)} addresses...")
        results = orchestrator.track_known_addresses(addresses)
        
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Tracking results saved to {args.output}")
    
    elif args.mode == 'analyze':
        print("🧠 Running comprehensive analysis...")
        analysis = orchestrator.run_pattern_analysis()
        
        with open(args.output, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"💾 Analysis saved to {args.output}")
    
    elif args.mode == 'monitor':
        addresses = args.addresses or config.get('known_whales', [])
        if not addresses:
            print("❌ No addresses to monitor. Use --addresses or add 'known_whales' to config.")
            return
        
        interval = config.get('monitoring', {}).get('interval_minutes', 30)
        orchestrator.run_monitoring_loop(addresses, interval)
    
    elif args.mode == 'report':
        print("📈 Generating whale report...")
        report = orchestrator.generate_whale_report()
        
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"💾 Report saved to {args.output}")
        
        # Print summary
        print(f"\n📊 Report Summary:")
        if 'summary' in report:
            print(f"   Total Whales: {report['summary']['total_whales_tracked']}")
        
        if 'top_whales' in report and report['top_whales']:
            top_whale = report['top_whales'][0]
            print(f"   Top Whale: {top_whale['address']} (Score: {top_whale['whale_score']})")

if __name__ == "__main__":
    print("🐋 Crypto Whale Tracker - Advanced Analytics Platform")
    print("=" * 60)
    main()