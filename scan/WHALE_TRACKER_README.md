# 🐋 Advanced Crypto Whale Tracker

A comprehensive system for tracking and analyzing large cryptocurrency transactions across multiple blockchains.

## Features

### ✅ Completed Enhancements

- **Volume-Based Whale Detection**: Configurable USD thresholds ($100k, $500k, $1M+)
- **Real-Time Price Integration**: CoinGecko API for accurate USD valuations  
- **Automated Address Discovery**: Find whales by scanning DEX transactions and high-volume transfers
- **Multi-Chain Support**: Ethereum, Polygon, BSC, Arbitrum, Optimism, and Solana
- **Advanced Database Analytics**: SQLite with relationship tracking and behavioral analysis
- **Pattern Recognition**: Wash trading, coordinated trading, pump & dump detection
- **Network Analysis**: Whale interaction graphs and community detection
- **Behavioral Clustering**: Group whales by trading patterns using machine learning

## Quick Start

1. **Setup Configuration**
```bash
cd scan
python whale_tracker_main.py --mode setup
```

2. **Edit `config.json` with your API keys**
```json
{
  "api_keys": {
    "etherscan": "YOUR_ETHERSCAN_API_KEY",
    "polygonscan": "YOUR_POLYGONSCAN_API_KEY",
    "bscscan": "YOUR_BSCSCAN_API_KEY"
  },
  "telegram": {
    "token": "YOUR_TELEGRAM_BOT_TOKEN", 
    "chat_id": "YOUR_CHAT_ID"
  }
}
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

## Usage Examples

### Discover New Whales
```bash
python whale_tracker_main.py --mode discover
```
Scans DEX contracts and major token transfers to find high-volume addresses.

### Track Specific Addresses
```bash
python whale_tracker_main.py --mode track --addresses 0x742d35Cc6634C0532925a3b844Bc454e4438f44e 0x28C6c06298d514Db089934071355E5743bf21d60
```

### Run Pattern Analysis
```bash
python whale_tracker_main.py --mode analyze --output analysis_report.json
```

### Start Continuous Monitoring
```bash
python whale_tracker_main.py --mode monitor
```

### Generate Whale Report
```bash
python whale_tracker_main.py --mode report --output daily_report.json
```

## Individual Scripts

### Enhanced Whale Tracker (`enhanced-whale-tracker.py`)
- Real-time monitoring with Telegram alerts
- USD value calculations
- Whale size classification
- Automatic whale discovery

### Whale Discovery (`whale-discovery.py`)  
- Scans DEX contracts for high-volume trades
- Analyzes token transfers
- Scores addresses by whale potential
- Outputs ranked whale lists

### Multi-Chain Tracker (`multichain-tracker.py`)
- Simultaneous tracking across 6 blockchains
- Parallel chain scanning
- Cross-chain arbitrage detection
- Unified whale identification

### Database Analytics (`database_analytics.py`)
- SQLite storage with relationships
- Address behavior tracking
- Network analysis
- Unusual activity detection

### Advanced Analytics (`advanced_analytics.py`)
- Wash trading detection
- Coordinated trading analysis
- Pump & dump pattern recognition
- Behavioral clustering
- Market impact analysis

## Database Schema

The system uses SQLite with these main tables:
- `transactions`: All whale transactions
- `whale_addresses`: Address analytics and scores  
- `address_relationships`: Who transacts with whom
- `daily_stats`: Aggregated daily statistics

## Whale Detection Criteria

### Volume Thresholds
- **Large Whale**: $100k+ transactions
- **Mega Whale**: $500k+ transactions  
- **Ultra Whale**: $1M+ transactions

### Discovery Methods
1. **DEX Scanning**: Monitor Uniswap, SushiSwap, 1inch routers
2. **Token Analysis**: Track major stablecoin/WETH transfers
3. **Network Effects**: Follow connections from known whales
4. **Volume Spikes**: Identify addresses with sudden activity increases

## Pattern Detection

### Wash Trading
- Back-and-forth transactions between addresses
- Similar volume patterns
- Time correlation analysis

### Coordinated Trading
- Multiple addresses trading same tokens simultaneously
- Unusual timing correlations
- Volume coordination

### Pump & Dump
- Volume spike detection
- Price impact analysis
- Rapid volume decline patterns

## API Requirements

### Required APIs
- **Etherscan**: Ethereum transaction data
- **Polygonscan**: Polygon transaction data  
- **BscScan**: BSC transaction data
- **CoinGecko**: Price data (no key required)

### Optional APIs
- **Telegram Bot**: Real-time notifications
- **Arbiscan**: Arbitrum data
- **Optimism Etherscan**: Optimism data

## Configuration

### Whale Thresholds
```json
"whale_thresholds": {
  "large": 100000,
  "mega": 500000, 
  "ultra": 1000000
}
```

### Monitoring Settings
```json
"monitoring": {
  "interval_minutes": 30,
  "enable_notifications": true
}
```

### Known Whales List
```json
"known_whales": [
  "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "0x28C6c06298d514Db089934071355E5743bf21d60"
]
```

## Output Files

- `discovered_whales.csv`: Newly discovered whale addresses
- `whale_transactions.csv`: All tracked transactions
- `whale_analytics_report.json`: Comprehensive analysis
- `multichain_whales.csv`: Cross-chain whale activity
- `pattern_analysis_*.json`: Timestamped pattern reports

## Performance Tips

1. **Rate Limiting**: Built-in delays to respect API limits
2. **Caching**: Price data cached for 5 minutes
3. **Batch Processing**: Parallel chain scanning
4. **Database Indexing**: Optimized queries for large datasets

## Security Notes

- Store API keys securely
- Use read-only API keys where possible
- Monitor API usage to avoid rate limits
- Regularly backup the whale database

## Advanced Features

### Network Analysis
- Build interaction graphs between whales
- Community detection algorithms
- Centrality analysis for key players

### Machine Learning
- Behavioral clustering with DBSCAN
- Anomaly detection for unusual patterns
- Predictive modeling for whale movements

### Cross-Chain Analysis
- Multi-chain address correlation
- Cross-chain arbitrage detection
- Bridge transaction monitoring

---

## Support

For issues or feature requests, please check the main project repository or create detailed bug reports with:
- Configuration used
- Error messages
- Expected vs actual behavior
- Transaction hashes for reference