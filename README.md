# 🐋 Crypto Whale Tracker

A comprehensive system for tracking and analyzing large cryptocurrency transactions across multiple blockchains. Automatically discover whale addresses, monitor high-volume trading, and detect sophisticated trading patterns.

## Features

- **Volume-Based Whale Detection**: Configurable USD thresholds ($100k, $500k, $1M+)
- **Real-Time Price Integration**: CoinGecko API for accurate USD valuations
- **Automated Address Discovery**: Find whales by scanning DEX transactions
- **Multi-Chain Support**: Ethereum, Polygon, BSC, Arbitrum, Optimism, Solana
- **Advanced Pattern Detection**: Wash trading, pump & dump, coordinated trading
- **Network Analysis**: Whale interaction graphs and community detection
- **Database Analytics**: SQLite with relationship tracking
- **Telegram Integration**: Real-time notifications

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get API Keys
- **Etherscan**: Get free key at https://etherscan.io/myapikey
- **Polygonscan**: Get free key at https://polygonscan.com/apis  
- **BscScan**: Get free key at https://bscscan.com/apis
- **CoinGecko**: No key needed (free tier)
- **Telegram** (optional): Create bot with @BotFather

### 3. Setup Configuration
```bash
cd scan
python whale_tracker_main.py --mode setup
```

This creates a `config.json` file. Edit it with your actual API keys:

```json
{
  "api_keys": {
    "etherscan": "YOUR_ACTUAL_API_KEY_HERE",
    "polygonscan": "YOUR_POLYGONSCAN_KEY",
    "bscscan": "YOUR_BSCSCAN_KEY"
  },
  "telegram": {
    "token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "known_whales": [
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "0x28C6c06298d514Db089934071355E5743bf21d60"
  ]
}
```

### 4. Start Using
```bash
# Find new whale addresses automatically
python whale_tracker_main.py --mode discover

# Track specific addresses
python whale_tracker_main.py --mode track --addresses 0x742d35Cc6634C0532925a3b844Bc454e4438f44e

# Start continuous monitoring
python whale_tracker_main.py --mode monitor
```

## 📋 Usage Guide

### Main Commands

#### Discover New Whales
```bash
python whale_tracker_main.py --mode discover
```
- Scans DEX contracts for high-volume trades
- Analyzes major token transfers
- Outputs ranked list of potential whales
- Results saved to `discovered_whales.json`

#### Track Specific Addresses
```bash
python whale_tracker_main.py --mode track --addresses ADDRESS1 ADDRESS2
```
- Monitors addresses across all supported chains
- Records transactions in database
- Calculates USD values and whale categories

#### Run Pattern Analysis
```bash
python whale_tracker_main.py --mode analyze --output analysis_report.json
```
- Detects wash trading patterns
- Identifies coordinated trading
- Finds pump & dump schemes
- Analyzes market impact

#### Generate Whale Report
```bash
python whale_tracker_main.py --mode report --output whale_report.json
```
- Top whales by activity score
- Network relationship analysis
- Daily statistics summary

#### Start Live Monitoring
```bash
python whale_tracker_main.py --mode monitor
```
- Runs continuously (checks every 30 minutes)
- Real-time Telegram notifications
- Automatic pattern analysis every 6 hours
- Ctrl+C to stop

### Advanced Usage

#### Individual Scripts

**Enhanced Live Tracking:**
```bash
# Edit script first to add API keys and addresses
python enhanced-whale-tracker.py
```

**Pure Whale Discovery:**
```bash
python whale-discovery.py
```

**Multi-Chain Analysis:**
```bash
python multichain-tracker.py
```

**Database Operations:**
```bash
python database_analytics.py
```

**Advanced Pattern Detection:**
```bash
python advanced_analytics.py
```

## 📊 Understanding the Output

### Whale Categories
- 🐠 **Regular**: Under $100k transactions
- 🐳 **Large Whale**: $100k - $500k transactions
- 🦈 **Mega Whale**: $500k - $1M transactions  
- 🐋 **Ultra Whale**: $1M+ transactions

### Key Output Files
- `whale_tracker.db` - SQLite database with all whale data
- `discovered_whales.csv` - Newly discovered whale addresses
- `multichain_whales.csv` - Cross-chain whale activity
- `whale_analytics_report.json` - Comprehensive analysis report
- `pattern_analysis_*.json` - Timestamped pattern detection reports

### Whale Score Calculation
Addresses are scored based on:
- **Volume Factor**: Total USD volume traded
- **Activity Factor**: Number of transactions
- **Chain Diversity**: Number of different blockchains used
- **Token Diversity**: Number of different tokens traded

## 🎯 Monitoring Strategy

### For Whale Tracking
1. **Start with Known Exchanges**: Use major exchange addresses as seeds
2. **Run Discovery**: Find new whales automatically
3. **Build Your List**: Add discovered addresses to config
4. **Continuous Monitoring**: Run 24/7 monitoring for real-time alerts

### For Market Analysis
1. **Daily Pattern Analysis**: Run analysis mode daily for trends
2. **Monitor Alerts**: Set up Telegram for pump & dump alerts
3. **Track Networks**: Analyze whale interaction patterns
4. **Cross-Chain Activity**: Monitor arbitrage opportunities

## 🔧 Configuration Options

### Whale Thresholds
```json
"whale_thresholds": {
  "large": 100000,     // $100k
  "mega": 500000,      // $500k  
  "ultra": 1000000     // $1M
}
```

### Monitoring Settings
```json
"monitoring": {
  "interval_minutes": 30,        // Check frequency
  "enable_notifications": true   // Telegram alerts
}
```

### Supported Chains
- **Ethereum**: Primary chain with full DEX analysis
- **Polygon**: Matic network transactions
- **BSC**: Binance Smart Chain  
- **Arbitrum**: Layer 2 scaling solution
- **Optimism**: Layer 2 scaling solution
- **Solana**: High-performance blockchain (different address format)

## 🛡️ Security & Best Practices

### API Management
- **Use Read-Only Keys**: Never use keys with write permissions
- **Rate Limiting**: Built-in delays respect API limits
- **Key Security**: Store API keys securely, never commit to version control
- **Separate Keys**: Use different keys for different chains when possible

### Database Management
- **Regular Backups**: Backup `whale_tracker.db` frequently
- **Storage Location**: Consider encrypted storage for sensitive data
- **Performance**: Database is optimized with indexes for large datasets

### Operational Security
- **Start Small**: Test with 2-3 addresses before scaling up
- **Monitor Usage**: Track API call counts to avoid limits
- **Error Handling**: All scripts include robust error handling
- **Logging**: Review logs regularly for unusual patterns

## 📈 Pattern Detection Capabilities

### Wash Trading Detection
- Identifies back-and-forth transactions between addresses
- Analyzes volume and timing correlations
- Calculates suspicion scores based on transaction balance

### Coordinated Trading Analysis
- Detects multiple addresses trading same tokens simultaneously
- Identifies unusual timing correlations across addresses  
- Flags potential market manipulation schemes

### Pump & Dump Detection
- Monitors volume spikes followed by rapid declines
- Analyzes price impact patterns
- Tracks token activity across multiple time periods

### Network Analysis
- Maps relationships between whale addresses
- Identifies central players and community structures
- Detects money flow patterns and clustering

## 🚨 Troubleshooting

### Common Issues

**"API Key Invalid" Errors**
- Verify API keys are correctly entered in config.json
- Check if API key has required permissions
- Ensure no extra spaces in API key strings

**"Rate Limit Exceeded"**
- Built-in delays should prevent this
- If persisting, increase delay times in scripts
- Consider using multiple API keys

**"No Data Found"**
- Verify addresses are correctly formatted
- Check if addresses have recent transaction activity
- Ensure blockchain explorers are accessible

**Database Errors**
- Check file permissions on whale_tracker.db
- Ensure sufficient disk space
- Backup and recreate database if corrupted

### Getting Help
- Review error messages carefully
- Check API explorer websites directly to verify data
- Ensure all dependencies are installed correctly
- Verify network connectivity to all API endpoints

## 📚 File Structure

```
scan/
├── whale_tracker_main.py          # Main orchestration script
├── enhanced-whale-tracker.py      # Enhanced version of original tracker
├── whale-discovery.py             # Automated whale discovery
├── multichain-tracker.py          # Multi-blockchain support
├── database_analytics.py          # Database operations and analytics
├── advanced_analytics.py          # Pattern detection and ML analysis
├── config.json                    # Configuration file (created by setup)
├── whale_tracker.db              # SQLite database (created automatically)
└── WHALE_TRACKER_README.md       # Detailed technical documentation

Output Files:
├── discovered_whales.csv         # New whale addresses found
├── multichain_whales.csv         # Cross-chain whale activity
├── whale_analytics_report.json   # Comprehensive analysis
└── pattern_analysis_*.json       # Timestamped pattern reports
```

## 🔮 Advanced Features

### Machine Learning Integration
- **Behavioral Clustering**: Groups whales by trading patterns using DBSCAN
- **Anomaly Detection**: Identifies unusual trading behavior
- **Predictive Analysis**: Models potential whale movement patterns

### Network Graph Analysis
- **Community Detection**: Finds groups of related addresses
- **Centrality Analysis**: Identifies key players in whale networks
- **Flow Analysis**: Tracks money movement patterns

### Cross-Chain Correlation
- **Multi-Chain Address Linking**: Connects same entity across chains
- **Arbitrage Detection**: Identifies cross-chain trading opportunities
- **Bridge Monitoring**: Tracks large cross-chain transfers

---

## 🤝 Contributing

This whale tracking system is designed to be educational and help with market transparency. Please use responsibly and in accordance with local regulations.

For feature requests or bug reports, please provide:
- Configuration used (without API keys)
- Error messages or unexpected behavior
- Steps to reproduce the issue
- Expected vs actual results