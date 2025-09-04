import requests
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
import csv
from concurrent.futures import ThreadPoolExecutor

@dataclass
class ChainConfig:
    name: str
    api_base: str
    api_key_param: str
    native_token: str
    price_id: str
    explorer_base: str

# Chain configurations
CHAINS = {
    "ethereum": ChainConfig(
        name="Ethereum",
        api_base="https://api.etherscan.io/api",
        api_key_param="apikey",
        native_token="ETH",
        price_id="ethereum",
        explorer_base="https://etherscan.io"
    ),
    "polygon": ChainConfig(
        name="Polygon",
        api_base="https://api.polygonscan.com/api",
        api_key_param="apikey",
        native_token="MATIC",
        price_id="matic-network",
        explorer_base="https://polygonscan.com"
    ),
    "bsc": ChainConfig(
        name="BSC",
        api_base="https://api.bscscan.com/api",
        api_key_param="apikey", 
        native_token="BNB",
        price_id="binancecoin",
        explorer_base="https://bscscan.com"
    ),
    "arbitrum": ChainConfig(
        name="Arbitrum",
        api_base="https://api.arbiscan.io/api",
        api_key_param="apikey",
        native_token="ETH",
        price_id="ethereum",
        explorer_base="https://arbiscan.io"
    ),
    "optimism": ChainConfig(
        name="Optimism", 
        api_base="https://api-optimistic.etherscan.io/api",
        api_key_param="apikey",
        native_token="ETH",
        price_id="ethereum",
        explorer_base="https://optimistic.etherscan.io"
    )
}

# Solana configuration (different API structure)
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
SOLANA_CONFIG = {
    "name": "Solana",
    "native_token": "SOL", 
    "price_id": "solana",
    "explorer_base": "https://solscan.io"
}

API_KEYS = {
    "ethereum": "YOUR_ETHERSCAN_API_KEY",
    "polygon": "YOUR_POLYGONSCAN_API_KEY", 
    "bsc": "YOUR_BSCSCAN_API_KEY",
    "arbitrum": "YOUR_ARBISCAN_API_KEY",
    "optimism": "YOUR_OPTIMISM_API_KEY"
}

WHALE_THRESHOLD_USD = 100000
OUTPUT_DIR = "multichain_data"

class MultiChainWhaleTracker:
    def __init__(self):
        self.price_cache = {}
        self.last_price_update = 0
        self.PRICE_CACHE_DURATION = 300  # 5 minutes
        
    def get_native_token_prices(self):
        """Get prices for all native tokens"""
        if time.time() - self.last_price_update < self.PRICE_CACHE_DURATION:
            return self.price_cache
            
        try:
            price_ids = [config.price_id for config in CHAINS.values()]
            price_ids.append(SOLANA_CONFIG["price_id"])
            
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": ",".join(set(price_ids)),
                "vs_currencies": "usd"
            }
            
            response = requests.get(url, params=params, timeout=10)
            self.price_cache = response.json()
            self.last_price_update = time.time()
            
        except Exception as e:
            print(f"Error fetching prices: {e}")
            
        return self.price_cache
    
    def get_evm_transactions(self, chain: str, address: str) -> List[Dict]:
        """Get transactions for EVM-compatible chains"""
        if chain not in CHAINS or chain not in API_KEYS:
            return []
            
        config = CHAINS[chain]
        api_key = API_KEYS[chain]
        
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "page": 1,
            "offset": 20,
            "sort": "desc",
            config.api_key_param: api_key
        }
        
        try:
            response = requests.get(config.api_base, params=params, timeout=15)
            data = response.json()
            
            if data.get("status") == "1":
                return data.get("result", [])
                
        except Exception as e:
            print(f"Error fetching {chain} transactions for {address}: {e}")
            
        return []
    
    def get_evm_token_transfers(self, chain: str, address: str) -> List[Dict]:
        """Get ERC-20/BEP-20 token transfers"""
        if chain not in CHAINS or chain not in API_KEYS:
            return []
            
        config = CHAINS[chain]
        api_key = API_KEYS[chain]
        
        params = {
            "module": "account", 
            "action": "tokentx",
            "address": address,
            "page": 1,
            "offset": 50,
            "sort": "desc",
            config.api_key_param: api_key
        }
        
        try:
            response = requests.get(config.api_base, params=params, timeout=15)
            data = response.json()
            
            if data.get("status") == "1":
                return data.get("result", [])
                
        except Exception as e:
            print(f"Error fetching {chain} token transfers for {address}: {e}")
            
        return []
    
    def get_solana_transactions(self, address: str) -> List[Dict]:
        """Get Solana transactions using RPC"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getConfirmedSignaturesForAddress2",
                "params": [
                    address,
                    {"limit": 20}
                ]
            }
            
            response = requests.post(SOLANA_RPC, json=payload, timeout=15)
            data = response.json()
            
            if "result" in data:
                # Get detailed transaction info
                signatures = [tx["signature"] for tx in data["result"][:10]]
                transactions = []
                
                for sig in signatures:
                    tx_payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getTransaction",
                        "params": [
                            sig,
                            {"encoding": "json", "maxSupportedTransactionVersion": 0}
                        ]
                    }
                    
                    tx_response = requests.post(SOLANA_RPC, json=tx_payload, timeout=10)
                    tx_data = tx_response.json()
                    
                    if "result" in tx_data and tx_data["result"]:
                        transactions.append(tx_data["result"])
                    
                    time.sleep(0.1)  # Rate limiting
                    
                return transactions
                
        except Exception as e:
            print(f"Error fetching Solana transactions for {address}: {e}")
            
        return []
    
    def analyze_evm_transaction(self, tx: Dict, chain: str) -> Optional[Dict]:
        """Analyze EVM transaction for whale activity"""
        try:
            config = CHAINS[chain]
            prices = self.get_native_token_prices()
            
            value_wei = int(tx.get("value", 0))
            value_native = value_wei / (10**18)
            
            native_price = prices.get(config.price_id, {}).get("usd", 0)
            usd_value = value_native * native_price
            
            if usd_value >= WHALE_THRESHOLD_USD:
                return {
                    "chain": chain,
                    "hash": tx["hash"],
                    "from": tx["from"],
                    "to": tx["to"],
                    "value_native": value_native,
                    "value_usd": usd_value,
                    "token": config.native_token,
                    "timestamp": int(tx["timeStamp"]),
                    "explorer_url": f"{config.explorer_base}/tx/{tx['hash']}",
                    "gas_used": int(tx.get("gasUsed", 0)),
                    "gas_price": int(tx.get("gasPrice", 0))
                }
                
        except Exception as e:
            pass
            
        return None
    
    def analyze_solana_transaction(self, tx: Dict) -> Optional[Dict]:
        """Analyze Solana transaction for whale activity"""
        try:
            prices = self.get_native_token_prices()
            sol_price = prices.get("solana", {}).get("usd", 0)
            
            # Extract transaction details
            meta = tx.get("meta", {})
            transaction = tx.get("transaction", {})
            
            # Calculate SOL transferred
            pre_balances = meta.get("preBalances", [])
            post_balances = meta.get("postBalances", [])
            
            if len(pre_balances) > 1 and len(post_balances) > 1:
                # Simple calculation for main transfer
                balance_change = abs(post_balances[0] - pre_balances[0]) / (10**9)  # SOL has 9 decimals
                usd_value = balance_change * sol_price
                
                if usd_value >= WHALE_THRESHOLD_USD:
                    accounts = transaction.get("message", {}).get("accountKeys", [])
                    
                    return {
                        "chain": "solana",
                        "hash": tx.get("signature", ""),
                        "from": accounts[0] if accounts else "",
                        "to": accounts[1] if len(accounts) > 1 else "",
                        "value_native": balance_change,
                        "value_usd": usd_value,
                        "token": "SOL",
                        "timestamp": tx.get("blockTime", 0),
                        "explorer_url": f"{SOLANA_CONFIG['explorer_base']}/tx/{tx.get('signature', '')}",
                        "slot": tx.get("slot", 0)
                    }
                    
        except Exception as e:
            pass
            
        return None
    
    def scan_address_multichain(self, address: str) -> Dict[str, List[Dict]]:
        """Scan an address across all supported chains"""
        results = {}
        
        def scan_chain(chain_name):
            whale_transactions = []
            
            if chain_name == "solana":
                # Different address format for Solana
                if len(address) == 44:  # Solana address length
                    txs = self.get_solana_transactions(address)
                    for tx in txs:
                        whale_tx = self.analyze_solana_transaction(tx)
                        if whale_tx:
                            whale_transactions.append(whale_tx)
            else:
                # EVM chains
                if address.startswith("0x") and len(address) == 42:
                    # Native token transactions
                    native_txs = self.get_evm_transactions(chain_name, address)
                    for tx in native_txs:
                        whale_tx = self.analyze_evm_transaction(tx, chain_name)
                        if whale_tx:
                            whale_transactions.append(whale_tx)
                    
                    # Token transfers (simplified - would need token price lookup)
                    token_txs = self.get_evm_token_transfers(chain_name, address)
                    # Token analysis would be added here
                    
            return chain_name, whale_transactions
        
        # Use threading for parallel chain scanning
        with ThreadPoolExecutor(max_workers=6) as executor:
            chain_names = list(CHAINS.keys()) + ["solana"]
            futures = [executor.submit(scan_chain, chain) for chain in chain_names]
            
            for future in futures:
                try:
                    chain_name, transactions = future.result(timeout=30)
                    results[chain_name] = transactions
                    if transactions:
                        print(f"✅ {chain_name}: Found {len(transactions)} whale transactions")
                except Exception as e:
                    print(f"❌ Error scanning chain: {e}")
        
        return results
    
    def batch_scan_addresses(self, addresses: List[str]) -> Dict:
        """Scan multiple addresses across all chains"""
        all_results = {}
        
        for i, address in enumerate(addresses, 1):
            print(f"\n🔍 Scanning address {i}/{len(addresses)}: {address}")
            
            results = self.scan_address_multichain(address)
            all_results[address] = results
            
            # Rate limiting between addresses
            time.sleep(2)
        
        return all_results
    
    def save_multichain_results(self, results: Dict, filename: str = "multichain_whales.csv"):
        """Save results to CSV with chain information"""
        all_transactions = []
        
        for address, chain_results in results.items():
            for chain, transactions in chain_results.items():
                for tx in transactions:
                    tx["scanned_address"] = address
                    all_transactions.append(tx)
        
        # Sort by USD value
        all_transactions.sort(key=lambda x: x["value_usd"], reverse=True)
        
        # Save to CSV
        if all_transactions:
            fieldnames = [
                "scanned_address", "chain", "hash", "from", "to", 
                "value_native", "value_usd", "token", "timestamp", "explorer_url"
            ]
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_transactions)
            
            print(f"💾 Saved {len(all_transactions)} whale transactions to {filename}")
        
        return all_transactions

# Example usage
if __name__ == "__main__":
    tracker = MultiChainWhaleTracker()
    
    # Example addresses (mix of EVM and Solana)
    test_addresses = [
        "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Bitfinex ETH
        "0x28C6c06298d514Db089934071355E5743bf21d60",  # Binance ETH
        "EGboTiF5aJL31BBHSjq2UoJw6nUFgsDnvahsh2efJHAF"   # Solana example
    ]
    
    print("🚀 Starting Multi-Chain Whale Scanner...")
    
    results = tracker.batch_scan_addresses(test_addresses)
    transactions = tracker.save_multichain_results(results)
    
    # Summary
    chain_summary = {}
    total_volume = 0
    
    for tx in transactions:
        chain = tx["chain"]
        if chain not in chain_summary:
            chain_summary[chain] = {"count": 0, "volume": 0}
        
        chain_summary[chain]["count"] += 1
        chain_summary[chain]["volume"] += tx["value_usd"]
        total_volume += tx["value_usd"]
    
    print(f"\n📊 Multi-Chain Whale Summary:")
    print(f"   Total Volume: ${total_volume:,.2f}")
    print(f"   Total Transactions: {len(transactions)}")
    
    for chain, stats in chain_summary.items():
        print(f"   {chain.upper()}: {stats['count']} txs, ${stats['volume']:,.2f}")