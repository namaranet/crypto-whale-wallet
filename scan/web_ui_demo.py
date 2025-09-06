#!/usr/bin/env python3
"""
Web UI Demo - How to access your whale tracker dashboard
"""

import webbrowser
import requests
import json
import time

def test_web_ui():
    """Test the web UI endpoints"""
    base_url = "http://localhost:5000"
    
    print("🐋 Whale Tracker Web UI Demo")
    print("=" * 50)
    
    # Test if the server is running
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            print("✅ Web server is running!")
            
            # Get stats
            stats = response.json()
            print(f"\n📊 Dashboard Stats:")
            print(f"   Total Whales: {stats['total_whales']}")
            print(f"   Total Volume: ${stats['total_volume']:,.2f}")
            print(f"   Total Transactions: {stats['total_transactions']}")
            print(f"   Recent Activity: {stats['recent_activity']}")
            
            # Test other endpoints
            print(f"\n🔗 Available URLs:")
            print(f"   Dashboard: {base_url}/")
            print(f"   Whales List: {base_url}/whales") 
            print(f"   Transactions: {base_url}/transactions")
            print(f"   API Stats: {base_url}/api/stats")
            print(f"   API Whales: {base_url}/api/whales")
            
            # Test whale endpoint
            whales_response = requests.get(f"{base_url}/api/whales?limit=5")
            if whales_response.status_code == 200:
                whales = whales_response.json()
                if whales:
                    print(f"\n🐳 Sample Whale:")
                    whale = whales[0]
                    print(f"   Address: {whale['address']}")
                    print(f"   Score: {whale['whale_score']}")
                    print(f"   Volume: ${whale['total_volume_usd']:,.2f}")
                    print(f"   Detail URL: {base_url}/whale/{whale['address']}")
            
            print(f"\n🌐 Access Instructions:")
            print(f"   1. Open your browser")
            print(f"   2. Navigate to: {base_url}")
            print(f"   3. Explore the dashboard!")
            
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Web server not accessible: {e}")
        print(f"\n🔧 To start the web UI:")
        print(f"   python whale_web_ui.py")
        return False

def demonstrate_features():
    """Show what features are available in the web UI"""
    print(f"\n🎨 Web UI Features:")
    print(f"=" * 30)
    
    features = [
        "📊 Interactive Dashboard with live stats",
        "🐋 Whale Directory with search and filters",
        "📈 Interactive charts and visualizations", 
        "💰 Transaction monitoring with real-time updates",
        "🔍 Detailed whale profiles and analytics",
        "📱 Responsive design for mobile/desktop",
        "⚡ Live activity feed simulation",
        "📊 Chain distribution charts",
        "🎯 Risk analysis for each whale",
        "🔗 Network connection visualization"
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"   {i:2d}. {feature}")
    
    print(f"\n🚀 Navigation:")
    print(f"   • Dashboard: Overview of all whale activity")
    print(f"   • Whales: Browse and search whale addresses")
    print(f"   • Transactions: Monitor real-time whale transactions")
    print(f"   • Click any whale address for detailed analysis")

if __name__ == "__main__":
    # Test the web UI
    is_running = test_web_ui()
    
    # Show features
    demonstrate_features()
    
    if is_running:
        print(f"\n🎉 Web UI is ready!")
        print(f"💡 The interface shows your discovered whales and simulated data")
        print(f"🔄 Data auto-refreshes every 30 seconds on dashboard")
        print(f"🎮 Try the filters and search functions!")
    else:
        print(f"\n⚠️  Start the web server first:")
        print(f"   python whale_web_ui.py")
        print(f"   Then run this demo again")