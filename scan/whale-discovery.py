import requests
import time
import json
from collections import defaultdict, Counter
import csv

# ====== CONFIG ======
ETHERSCAN_API_KEY = "YOUR_ETHERSCAN_API_KEY"
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

# Major DEX contract addresses on Ethereum
DEX_CONTRACTS = {
    "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "uniswap_v2_router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "sushiswap_router": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    "pancakeswap_router": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
    "1inch_v4": "0x1111111254fb6c44bAC0beD2854e76F90643097d",
}

# High-value token contracts to monitor
MAJOR_TOKENS = {
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86a33E6441D316e51581DeF8A6b1c4c4d4D6E",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
}

DISCOVERY_THRESHOLDS = {
    "min_tx_value_usd": 50000,      # Minimum transaction value to consider
    "min_daily_volume": 500000,     # Minimum daily volume to flag as whale
    "min_tx_frequency": 5,          # Minimum transactions per day
}

OUTPUT_FILE = "discovered_whales.csv"
ANALYSIS_FILE = "whale_analysis.json"

class WhaleHunter:
    def __init__(self):
        self.discovered_addresses = {}
        self.address_stats = defaultdict(lambda: {
            'total_volume': 0,
            'tx_count': 0,
            'tokens_traded': set(),
            'avg_tx_size': 0,
            'first_seen': None,
            'last_seen': None
        })
        self.price_cache = {}
        
    def get_token_price(self, contract_address):
        """Get token price with caching"""
        if contract_address in self.price_cache:
            return self.price_cache[contract_address]
            
        try:
            url = f"{COINGECKO_API_BASE}/simple/token_price/ethereum"
            params = {
                "contract_addresses": contract_address,
                "vs_currencies": "usd"
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if contract_address.lower() in data:
                price = data[contract_address.lower()]["usd"]
                self.price_cache[contract_address] = price
                return price
                
        except Exception as e:
            print(f"Price fetch error for {contract_address}: {e}")
            
        return None
    
    def scan_dex_transactions(self, dex_address, blocks_to_scan=1000):
        """Scan DEX contract for high-value transactions"""
        print(f"🔍 Scanning DEX: {dex_address}")
        
        # Get latest block
        latest_block_response = requests.get(
            f"https://api.etherscan.io/api",
            params={
                "module": "proxy",
                "action": "eth_blockNumber",
                "apikey": ETHERSCAN_API_KEY
            }
        )
        
        latest_block = int(latest_block_response.json()["result"], 16)
        start_block = latest_block - blocks_to_scan
        
        # Get transactions to this contract
        url = f"https://api.etherscan.io/api"
        params = {
            "module": "account",
            "action": "txlist",
            "address": dex_address,
            "startblock": start_block,
            "endblock": latest_block,
            "page": 1,
            "offset": 100,
            "sort": "desc",
            "apikey": ETHERSCAN_API_KEY
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            transactions = data.get("result", [])
            
            for tx in transactions:
                self.analyze_transaction(tx)
                time.sleep(0.1)  # Rate limiting
                
        except Exception as e:
            print(f"Error scanning DEX {dex_address}: {e}")
    
    def scan_token_transfers(self, token_address, min_value_usd=50000):
        """Scan high-value transfers for a specific token"""
        print(f"🪙 Scanning token transfers: {token_address}")
        
        url = f"https://api.etherscan.io/api"
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": token_address,
            "page": 1,
            "offset": 100,
            "sort": "desc",
            "apikey": ETHERSCAN_API_KEY
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            transfers = data.get("result", [])
            
            token_price = self.get_token_price(token_address)
            
            for transfer in transfers:
                try:
                    value = int(transfer["value"]) / (10 ** int(transfer["tokenDecimal"]))
                    usd_value = value * token_price if token_price else 0
                    
                    if usd_value >= min_value_usd:
                        self.track_address(transfer["from"], usd_value, transfer)
                        self.track_address(transfer["to"], usd_value, transfer)
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error scanning token {token_address}: {e}")
    
    def track_address(self, address, tx_value, tx_data):
        """Track statistics for a specific address"""
        if address == "0x0000000000000000000000000000000000000000":
            return
            
        stats = self.address_stats[address]
        stats['total_volume'] += tx_value
        stats['tx_count'] += 1
        stats['tokens_traded'].add(tx_data.get('tokenSymbol', 'ETH'))
        
        timestamp = int(tx_data.get('timeStamp', time.time()))
        
        if stats['first_seen'] is None or timestamp < stats['first_seen']:
            stats['first_seen'] = timestamp
        if stats['last_seen'] is None or timestamp > stats['last_seen']:
            stats['last_seen'] = timestamp
            
        stats['avg_tx_size'] = stats['total_volume'] / stats['tx_count']
    
    def analyze_transaction(self, tx_data):
        """Analyze individual transaction for whale behavior"""
        try:
            value_eth = int(tx_data["value"]) / (10**18)
            # Rough ETH price estimation - in production, get real price
            usd_value = value_eth * 2000  # Approximate ETH price
            
            if usd_value >= DISCOVERY_THRESHOLDS["min_tx_value_usd"]:
                self.track_address(tx_data["from"], usd_value, tx_data)
                self.track_address(tx_data["to"], usd_value, tx_data)
                
        except Exception as e:
            pass
    
    def identify_whales(self):
        """Identify addresses that meet whale criteria"""
        whales = []
        
        for address, stats in self.address_stats.items():
            # Calculate time period
            if stats['first_seen'] and stats['last_seen']:
                days_active = max(1, (stats['last_seen'] - stats['first_seen']) / 86400)
                daily_volume = stats['total_volume'] / days_active
                daily_tx_frequency = stats['tx_count'] / days_active
                
                # Whale criteria
                is_whale = (
                    daily_volume >= DISCOVERY_THRESHOLDS["min_daily_volume"] or
                    stats['avg_tx_size'] >= DISCOVERY_THRESHOLDS["min_tx_value_usd"] and
                    daily_tx_frequency >= DISCOVERY_THRESHOLDS["min_tx_frequency"]
                )
                
                if is_whale:
                    whale_data = {
                        'address': address,
                        'total_volume_usd': stats['total_volume'],
                        'daily_volume_usd': daily_volume,
                        'tx_count': stats['tx_count'],
                        'avg_tx_size_usd': stats['avg_tx_size'],
                        'tokens_traded': list(stats['tokens_traded']),
                        'days_active': days_active,
                        'daily_tx_frequency': daily_tx_frequency,
                        'whale_score': self.calculate_whale_score(stats, daily_volume)
                    }
                    whales.append(whale_data)
        
        # Sort by whale score
        whales.sort(key=lambda x: x['whale_score'], reverse=True)
        return whales
    
    def calculate_whale_score(self, stats, daily_volume):
        """Calculate whale score based on multiple factors"""
        score = 0
        
        # Volume factor
        score += min(daily_volume / 1000000, 10) * 30  # Max 300 points
        
        # Transaction frequency factor
        daily_freq = stats['tx_count'] / max(1, (stats['last_seen'] - stats['first_seen']) / 86400)
        score += min(daily_freq, 50) * 2  # Max 100 points
        
        # Average transaction size factor
        score += min(stats['avg_tx_size'] / 100000, 10) * 20  # Max 200 points
        
        # Token diversity factor
        score += len(stats['tokens_traded']) * 10  # 10 points per token
        
        return round(score, 2)
    
    def save_results(self, whales):
        """Save discovered whales to files"""
        # Save to CSV
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'address', 'whale_score', 'total_volume_usd', 'daily_volume_usd',
                'tx_count', 'avg_tx_size_usd', 'tokens_traded', 'days_active'
            ])
            
            for whale in whales:
                writer.writerow([
                    whale['address'],
                    whale['whale_score'],
                    round(whale['total_volume_usd'], 2),
                    round(whale['daily_volume_usd'], 2),
                    whale['tx_count'],
                    round(whale['avg_tx_size_usd'], 2),
                    ', '.join(whale['tokens_traded']),
                    round(whale['days_active'], 1)
                ])
        
        # Save detailed analysis to JSON
        with open(ANALYSIS_FILE, 'w') as f:
            json.dump(whales, f, indent=2, default=str)
        
        print(f"💾 Results saved to {OUTPUT_FILE} and {ANALYSIS_FILE}")
    
    def run_discovery(self):
        """Run the whale discovery process"""
        print("🐋 Starting Whale Discovery Process...")
        
        # Scan DEX contracts
        for name, address in DEX_CONTRACTS.items():
            print(f"\n📊 Scanning {name}: {address}")
            self.scan_dex_transactions(address)
            time.sleep(1)  # Rate limiting
        
        # Scan major token transfers
        for name, address in MAJOR_TOKENS.items():
            print(f"\n🪙 Scanning {name} transfers: {address}")
            self.scan_token_transfers(address)
            time.sleep(1)  # Rate limiting
        
        print("\n🧮 Analyzing discovered addresses...")
        whales = self.identify_whales()
        
        print(f"\n🎯 Discovered {len(whales)} potential whales!")
        
        # Display top 10 whales
        print("\n🏆 Top 10 Whales by Score:")
        for i, whale in enumerate(whales[:10], 1):
            print(f"{i:2d}. {whale['address']} (Score: {whale['whale_score']})")
            print(f"     Daily Volume: ${whale['daily_volume_usd']:,.0f}")
            print(f"     Avg TX Size: ${whale['avg_tx_size_usd']:,.0f}")
            print(f"     Tokens: {', '.join(whale['tokens_traded'][:3])}")
            print()
        
        self.save_results(whales)
        return whales

if __name__ == "__main__":
    hunter = WhaleHunter()
    whales = hunter.run_discovery()
    
    print(f"\n✅ Discovery complete! Found {len(whales)} whales.")
    print(f"📄 Check {OUTPUT_FILE} for the full list.")