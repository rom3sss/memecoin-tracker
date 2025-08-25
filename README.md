## Memecoin Alpha & Hype Tracker Bot
📖 Overview
This high-speed, automated Python script is designed to monitor a curated list of influential X (formerly Twitter) accounts to detect early mentions of new memecoins. The primary goal is to identify potential launches on platforms like pump.fun and quantify social media hype in real-time. By automating the discovery process, the bot aims to provide a significant informational edge in the fast-paced memecoin market.

The bot parses tweets for high-priority signals such as contract addresses (CAs) and launchpad links. Once a potential coin is identified, it immediately measures its "Hype Velocity" by tracking mentions across X, and logs all actionable data to a Google Sheet for quick analysis and decision-making.

## Features
Influencer Monitoring: Continuously monitors the timelines of a specified list of X usernames from a Google Sheet.

Multi-Signal Detection: Scans tweets with a prioritized approach:

Contract Addresses (CA): Directly parses for ETH, BASE, and SOL contract addresses.

Launchpad Links: Automatically identifies and extracts CAs from pump.fun links.

Keywords & Cashtags: Detects memecoin slang (send it, 1000x, $WIF) to catch early signals.

Real-Time Hype Tracking: Upon detection, the bot immediately queries the X API to calculate the number of unique users mentioning the coin within critical timeframes (15 minutes, 1 hour, 24 hours).

Automated Data Logging: All findings are structured and exported in real-time to a dedicated Google Sheet, providing a clean dashboard for analysis.

Robust & Resilient: Includes error handling and retry logic to ensure continuous operation.

## ⚙️ How It Works
Initialization: The script authenticates with the X API v2 and the Google Sheets API using your provided credentials.

Load Targets: It fetches the list of target X usernames from your designated 'Target Accounts' Google Sheet.

Timeline Polling: The bot enters a continuous loop, fetching the most recent tweets from each target account's timeline.

Signal Parsing: Each new tweet is scanned by the parse_tweet_for_alpha function. It aggressively searches for contract addresses, pump.fun links, or a combination of keywords and new cashtags.

Hype Calculation: If a valid signal (like a CA) is found, the calculate_hype_velocity function is triggered. It performs a search on X for the coin's CA to count recent unique mentions.

Data Output: The collected data—including the CA, source account, detection time, hype metrics, and a link to the source tweet—is formatted and inserted as a new row in your 'Memecoin Alpha' Google Sheet.

Loop & Repeat: The script waits for a configured interval (e.g., 60 seconds) before repeating the process to check for new tweets, ensuring it stays up-to-date while respecting API rate limits.

## 🚀 Setup and Usage
For a detailed, step-by-step guide on acquiring API keys and configuring your environment, please refer to the Setup Guide provided with the script. The basic steps are:

## Prerequisites: Install Python 3.8+ and the required libraries:

pip install tweepy pandas gspread oauth2client

## API Keys:

Obtain a Bearer Token from the X Developer Portal.

Set up a Google Cloud Project, enable the Google Drive & Sheets APIs, and download the JSON credentials for a service account.

## Google Sheets Setup:

Create two sheets: one for input (Target Accounts) and one for output (Memecoin Alpha).

Share both sheets with the client_email found in your Google JSON credentials file, granting it "Editor" permissions.

## Configure the Script:

Edit the memecoin_tracker.py file and fill in the following variables:

X_BEARER_TOKEN

GOOGLE_SHEETS_CREDS_FILE (the path to your JSON file)

INPUT_SHEET_NAME

OUTPUT_SHEET_NAME

## Run the Bot:

python memecoin_tracker.py

⚠️ Disclaimer
Memecoin trading is speculative and carries an extremely high level of risk. This tool is for informational and educational purposes only and does not constitute financial advice. The data provided may contain inaccuracies or be subject to API limitations. Always conduct your own thorough research (DYOR) before making any investment decisions.
