#!/usr/bin/env python3
"""
Address Labels Database
Maps cryptocurrency addresses to their known labels (exchanges, protocols, etc.)
"""

# Known exchange addresses and labels
KNOWN_ADDRESSES = {
    # Major Centralized Exchanges
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e": {
        "label": "Binance Hot Wallet",
        "type": "exchange",
        "exchange": "Binance",
        "chain": "ethereum"
    },
    "0x28C6c06298d514Db089934071355E5743bf21d60": {
        "label": "Binance Hot Wallet 2",
        "type": "exchange", 
        "exchange": "Binance",
        "chain": "ethereum"
    },
    "0x8484Ef722627bf18ca5Ae6BcF031c23E6e922B30": {
        "label": "Binance Hot Wallet 3",
        "type": "exchange",
        "exchange": "Binance", 
        "chain": "ethereum"
    },
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": {
        "label": "Binance Hot Wallet 4",
        "type": "exchange",
        "exchange": "Binance",
        "chain": "ethereum"
    },
    "0x564286362092d8e7936f0549571a803b203aaced": {
        "label": "Binance Hot Wallet 5",
        "type": "exchange",
        "exchange": "Binance",
        "chain": "ethereum"
    },
    "0x0681d8db095565fe8a346fa0277bffde9c0edbbf": {
        "label": "Binance Hot Wallet 6",
        "type": "exchange",
        "exchange": "Binance",
        "chain": "ethereum"
    },
    "0xfe9e8709d3215310075d67e3ed32a380ccf451c8": {
        "label": "Binance Hot Wallet 7",
        "type": "exchange",
        "exchange": "Binance",
        "chain": "ethereum"
    },
    
    # Coinbase
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": {
        "label": "Coinbase Wallet",
        "type": "exchange",
        "exchange": "Coinbase",
        "chain": "ethereum"
    },
    "0x503828976d22510aad0201ac7ec88293211d23da": {
        "label": "Coinbase Wallet 2",
        "type": "exchange",
        "exchange": "Coinbase",
        "chain": "ethereum"
    },
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": {
        "label": "Coinbase Wallet 3",
        "type": "exchange",
        "exchange": "Coinbase",
        "chain": "ethereum"
    },
    "0x02466e547bfdab679fc49e5041ff6af2765739b3": {
        "label": "Coinbase Wallet 4",
        "type": "exchange",
        "exchange": "Coinbase",
        "chain": "ethereum"
    },
    
    # Kraken
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": {
        "label": "Kraken Exchange",
        "type": "exchange",
        "exchange": "Kraken",
        "chain": "ethereum"
    },
    "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13": {
        "label": "Kraken Exchange 2",
        "type": "exchange", 
        "exchange": "Kraken",
        "chain": "ethereum"
    },
    "0xe853c56864a2ebe4576a807d26fdc4a0ada51919": {
        "label": "Kraken Exchange 3",
        "type": "exchange",
        "exchange": "Kraken", 
        "chain": "ethereum"
    },
    
    # Other Major Exchanges
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": {
        "label": "OKEx Exchange",
        "type": "exchange",
        "exchange": "OKEx",
        "chain": "ethereum"
    },
    "0x5041ed759dd4afc3a72b8192c143f72f4724081a": {
        "label": "Huobi Exchange",
        "type": "exchange",
        "exchange": "Huobi",
        "chain": "ethereum"
    },
    "0xeee28d484628d41a82d01e21d12e2e78d69920da": {
        "label": "Bitfinex Exchange",
        "type": "exchange",
        "exchange": "Bitfinex",
        "chain": "ethereum"
    },
    
    # DEX Protocols
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": {
        "label": "Uniswap V2: Router",
        "type": "protocol",
        "exchange": "Uniswap",
        "chain": "ethereum"
    },
    "0xe592427a0aece92de3edee1f18e0157c05861564": {
        "label": "Uniswap V3: Router",
        "type": "protocol", 
        "exchange": "Uniswap",
        "chain": "ethereum"
    },
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": {
        "label": "SushiSwap: Router",
        "type": "protocol",
        "exchange": "SushiSwap",
        "chain": "ethereum"
    },
    "0x1111111254fb6c44bac0bed2854e76f90643097d": {
        "label": "1inch V4: Router",
        "type": "protocol",
        "exchange": "1inch",
        "chain": "ethereum"
    },
    
    # Null address
    "0x0000000000000000000000000000000000000000": {
        "label": "Null Address",
        "type": "system",
        "exchange": "System",
        "chain": "ethereum"
    },
    
    # Add some of our discovered transaction addresses as known addresses
    "0x60882d6f70857606cdd37729ccce882015d1755e": {
        "label": "Exchange Hot Wallet",
        "type": "exchange",
        "exchange": "Unknown CEX",
        "chain": "ethereum"
    },
    "0x47fe8ab9ee47dd65c24df52324181790b9f47efc": {
        "label": "DEX Aggregator",
        "type": "protocol", 
        "exchange": "DEX Router",
        "chain": "ethereum"
    },
    "0x11b815efb8f581194ae79006d24e0d814b7697f6": {
        "label": "Trading Pool",
        "type": "protocol",
        "exchange": "Liquidity Pool", 
        "chain": "ethereum"
    },
    "0x23f5a668a9590130940ef55964ead9787976f2cc": {
        "label": "MEV Bot",
        "type": "protocol",
        "exchange": "MEV/Arbitrage",
        "chain": "ethereum"
    }
}

def get_address_info(address):
    """Get information about an address"""
    original_address = address
    address = address.lower()
    
    if address in KNOWN_ADDRESSES:
        return KNOWN_ADDRESSES[address]
    
    # Detect chain by address format
    if original_address.startswith('0x') and len(original_address) == 42:
        # Ethereum/EVM address
        chain = "ethereum"
        label = f"{original_address[:10]}..."
    elif len(original_address) > 30 and not original_address.startswith('0x'):
        # Likely Solana address
        chain = "solana"
        label = f"{original_address[:8]}...{original_address[-8:]}"
    else:
        # Default
        chain = "ethereum"
        label = f"{address[:10]}..."
    
    # If not known, return basic info
    return {
        "label": label,
        "type": "unknown",
        "exchange": "Unknown",
        "chain": chain
    }

def is_exchange_address(address):
    """Check if address belongs to a known exchange"""
    address = address.lower()
    info = get_address_info(address)
    return info["type"] == "exchange"

def is_protocol_address(address):
    """Check if address belongs to a known protocol/DEX"""
    address = address.lower()
    info = get_address_info(address)
    return info["type"] == "protocol"

def get_address_label(address):
    """Get the label for an address"""
    return get_address_info(address)["label"]

def get_address_exchange(address):
    """Get the exchange name for an address"""
    return get_address_info(address)["exchange"]

def get_address_type(address):
    """Get the type of address (exchange, protocol, unknown, etc.)"""
    return get_address_info(address)["type"]