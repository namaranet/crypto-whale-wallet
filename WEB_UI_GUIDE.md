# 🌐 Whale Tracker Web UI Guide

Your whale tracker now has a beautiful web interface! Access it at **http://localhost:5000**

## 🚀 Quick Start

1. **Start the Web UI:**
   ```bash
   cd scan
   python whale_web_ui.py
   ```

2. **Open Your Browser:**
   - Navigate to: http://localhost:5000
   - The dashboard will load with your whale data

## 📊 Dashboard Features

### Main Dashboard (/)
- **Live Stats Cards**: Total whales, volume, transactions, recent activity
- **Interactive Charts**: Chain distribution pie chart and volume bar chart
- **Top Whales Table**: Ranked by whale score with clickable addresses
- **Live Activity Feed**: Simulated real-time whale alerts
- **Auto-refresh**: Updates every 30 seconds automatically

### Whale Directory (/whales)
- **Whale Cards**: Visual cards for each whale with color-coded scoring
- **Search**: Filter whales by address
- **Category Filters**: Filter by Ultra/Mega/Large whales
- **Detailed Info**: Whale scores, volume, transaction count, active chains
- **Click to View**: Each whale links to detailed profile

### Individual Whale Pages (/whale/ADDRESS)
- **Whale Profile**: Complete address analytics and scoring
- **Transaction History**: All transactions for this whale
- **Activity Charts**: Token distribution and trading patterns
- **Risk Analysis**: Wash trading and pattern detection scores
- **Network Connections**: Related addresses and interaction counts
- **Export Options**: Download transaction data

### Transaction Monitor (/transactions)
- **Live Transaction Feed**: Real-time whale transaction monitoring
- **Advanced Filters**: Chain, whale size, token type, minimum value
- **Auto-refresh**: New transactions appear automatically
- **Transaction Details**: Full transaction info with explorer links
- **Export Functions**: Download filtered transaction data

## 🎨 Visual Design

### Color Coding
- 🐋 **Ultra Whales**: Red borders ($1M+ transactions)
- 🦈 **Mega Whales**: Orange borders ($500K-$1M)
- 🐳 **Large Whales**: Green borders ($100K-$500K)
- 🐠 **Regular**: Gray borders (under $100K)

### Interactive Elements
- **Hover Effects**: Cards lift and highlight on hover
- **Copy Buttons**: One-click copy for all addresses
- **Dropdown Menus**: Explorer links and watch list options
- **Search Bars**: Real-time filtering and search
- **Charts**: Interactive Chart.js visualizations

## 📱 Responsive Design

The interface works perfectly on:
- 🖥️ **Desktop**: Full dashboard with all features
- 📱 **Mobile**: Responsive design with collapsible navigation
- 📱 **Tablet**: Optimized card layouts and touch-friendly

## 🔧 API Endpoints

Access data programmatically:

```bash
# Get dashboard stats
curl http://localhost:5000/api/stats

# Get whale list
curl http://localhost:5000/api/whales?limit=50

# Get recent transactions  
curl http://localhost:5000/api/transactions?limit=100
```

## 🎯 Your Real Data

The web UI displays:
- ✅ **Your 4 discovered whales** from the blockchain scan
- ✅ **Real whale scores** calculated from transaction patterns
- ✅ **Actual transaction data** from your API calls
- ✅ **Live database** that updates as you run more scans

## 🔄 Live Features

### Auto-Refresh
- Dashboard refreshes every 30 seconds
- New transactions appear automatically
- Live activity feed simulates real whale alerts
- Charts update with new data

### Simulated Activity
- Demo mode shows whale activity patterns
- New transaction alerts appear periodically  
- Activity feed demonstrates real-time monitoring

## 📊 Data Sources

The web UI pulls from:
1. **whale_tracker.db** - Your SQLite database
2. **Real API data** - From your Etherscan/Polygonscan keys
3. **Sample data** - Demo transactions for UI demonstration

## 🚀 Production Deployment

For production use:

1. **Install Production Server:**
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 whale_web_ui:app
   ```

3. **Environment Variables:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secret-key
   ```

## 🔧 Customization

### Adding More Chains
Edit `whale_web_ui.py` and add chain configurations:
```python
# Add new chains to the database schema
# Update the chain filter dropdowns
# Add new API integrations
```

### Custom Styling
Modify the CSS in `templates/base.html`:
- Change color themes
- Adjust card layouts  
- Modify chart styling

### Additional Features
The modular design allows easy addition of:
- Real-time WebSocket updates
- More advanced analytics
- Additional chain support
- Custom alert rules

## 🎉 What You've Built

You now have a **complete whale tracking platform** with:

1. **🔍 Discovery Engine**: Finds whales from blockchain data
2. **📊 Analytics Dashboard**: Beautiful web interface
3. **⚡ Real-time Monitoring**: Live transaction tracking
4. **🎯 Pattern Detection**: Advanced trading analysis
5. **🌐 Multi-chain Support**: 6 different blockchains
6. **📱 Modern UI**: Responsive, interactive interface

## 🛠️ Troubleshooting

### Web UI Won't Load
```bash
# Check if server is running
curl http://localhost:5000/api/stats

# Restart the web UI
python whale_web_ui.py
```

### No Data Showing
```bash
# Run whale discovery first
python whale_tracker_main.py --mode discover

# Or add sample data
python web_ui_demo.py
```

### Port Already in Use
```bash
# Change port in whale_web_ui.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

---

Your whale tracker web interface is now **live and operational**! 🐋🚀

Navigate to **http://localhost:5000** and explore your whale empire!