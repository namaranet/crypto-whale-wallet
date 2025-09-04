🛠 Setup Telegram Bot

Open Telegram and search for @BotFather.

Run /newbot → follow prompts → you’ll get a BOT TOKEN.

Start a chat with your bot and send any message.

Go to https://api.telegram.org/botYOUR_TOKEN/getUpdates

Replace YOUR_TOKEN with your bot token.

Look for your chat_id in the JSON response.

📡 How It Works

Watches your chosen wallet on Etherscan.

When a new transaction happens → sends a Telegram push notification with details + a link to Etherscan.

⚡️ You can expand this to:

Monitor multiple wallets (loop through a list).

Track ETH transfers too (swap action=tokentx → action=txlist).

Filter only buy/sell on Uniswap by looking at contract addresses.