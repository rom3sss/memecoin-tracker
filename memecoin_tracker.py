# memecoin_tracker.py
#
# Objective: Monitor a list of X accounts for early memecoin mentions,
# focusing on contract addresses and pump.fun links, and then track
# the social media hype velocity of detected coins.


import tweepy
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import time
from datetime import datetime, timedelta


# --- CONFIGURATION & AUTHENTICATION ---
# Important: Replace these with your actual API keys and file paths.
# Store them securely, for example, using environment variables.


# X (Twitter) API v2 Bearer Token
# Essential for accessing the X API.
X_BEARER_TOKEN = "YOUR_X_BEARER_TOKEN"


# Google Sheets API Configuration
# This requires setting up a service account in Google Cloud Platform.
GOOGLE_SHEETS_SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
GOOGLE_SHEETS_CREDS_FILE = 'path/to/your/google-credentials.json' # The JSON file you download from GCP
INPUT_SHEET_NAME = 'Target Accounts' # The name of the sheet with X usernames
OUTPUT_SHEET_NAME = 'Memecoin Alpha' # The name of the sheet where results will be saved


# --- REGEX & KEYWORDS FOR DETECTION ---


# Regex for contract addresses (CA)
# This is a simplified regex. You can create more specific ones for each chain.
# ETH/BASE (EVM): Starts with '0x' and is 42 characters long.
# SOL: A more complex Base58 string, typically 32-44 characters. This is a general pattern.
CA_PATTERNS = {
   'ETH': r'0x[a-fA-F0-9]{40}',
   'BASE': r'0x[a-fA-F0-9]{40}',
   'SOL': r'[1-9A-HJ-NP-Za-km-z]{32,44}'
}


# Keywords that signal a potential new launch
MEMECOIN_KEYWORDS = [
   'just launched', 'send it', '1000x', 'degen play', 'low mc', 'pump.fun',
   'moonshot', 'alpha', 'gem'
]
# Emojis often associated with hype
HYPE_EMOJIS = ['🚀', '🌕', '🐸', '💎', '🔥']


# --- API CLIENT INITIALIZATION ---


def initialize_clients():
   """Initializes and returns authenticated clients for X and Google Sheets."""
   try:
       # Initialize Tweepy Client for X API v2
       x_client = tweepy.Client(X_BEARER_TOKEN)
       print("Successfully authenticated with X API.")
   except Exception as e:
       print(f"Error authenticating with X API: {e}")
       return None, None


   try:
       # Initialize Google Sheets Client
       creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDS_FILE, GOOGLE_SHEETS_SCOPE)
       gsheet_client = gspread.authorize(creds)
       print("Successfully authenticated with Google Sheets API.")
   except Exception as e:
       print(f"Error authenticating with Google Sheets API: {e}")
       return None, None


   return x_client, gsheet_client


# --- CORE FUNCTIONS ---


def get_target_accounts(gsheet_client):
   """Loads the list of X usernames from the specified Google Sheet."""
   try:
       sheet = gsheet_client.open(INPUT_SHEET_NAME).sheet1
       accounts = sheet.col_values(1) # Assumes usernames are in the first column
       print(f"Loaded {len(accounts)} target accounts: {accounts}")
       return accounts
   except Exception as e:
       print(f"Error loading target accounts from Google Sheet: {e}")
       return []


def get_user_id(x_client, username):
   """Fetches the X user ID for a given username."""
   try:
       response = x_client.get_user(username=username)
       if response.data:
           return response.data.id
   except Exception as e:
       print(f"Could not find user ID for {username}: {e}")
   return None


def parse_tweet_for_alpha(tweet_text):
   """
   Parses a tweet's text to find memecoin signals.
   Priority: 1. Contract Address, 2. pump.fun link, 3. Keywords.
   """
   # 1. Detect Contract Addresses
   for chain, pattern in CA_PATTERNS.items():
       match = re.search(pattern, tweet_text)
       if match:
           return {'type': 'CA', 'value': match.group(0), 'chain': chain}


   # 2. Detect pump.fun links
   pump_fun_match = re.search(r'https?://(www\.)?pump\.fun/([a-zA-Z0-9]+)', tweet_text)
   if pump_fun_match:
       # The part after pump.fun/ is often the contract address on Solana
       ca_from_link = pump_fun_match.group(2)
       return {'type': 'pump.fun', 'value': ca_from_link, 'chain': 'SOL', 'link': pump_fun_match.group(0)}


   # 3. Detect Keywords and Cashtags
   if any(keyword in tweet_text.lower() for keyword in MEMECOIN_KEYWORDS):
       # Find cashtags ($SYMBOL)
       cashtag_match = re.search(r'\$[A-Za-z]{2,6}', tweet_text)
       if cashtag_match:
           return {'type': 'cashtag', 'value': cashtag_match.group(0), 'chain': 'Unknown'}


   return None


def calculate_hype_velocity(x_client, query, time_minutes):
   """
   Calculates hype velocity by counting unique user mentions for a query
   in a given timeframe.
   """
   try:
       start_time = datetime.utcnow() - timedelta(minutes=time_minutes)
       start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')


       # Using search_recent_tweets endpoint
       response = x_client.search_recent_tweets(
           query=f'"{query}" -is:retweet', # Search for the CA or cashtag, exclude retweets
           start_time=start_time_str,
           max_results=100, # Max per request for this endpoint
           tweet_fields=['author_id']
       )


       if response.data:
           unique_users = {tweet.author_id for tweet in response.data}
           return len(unique_users)
       return 0
   except Exception as e:
       print(f"Error calculating hype for '{query}': {e}")
       return 0


def monitor_accounts(x_client, gsheet_client, user_ids_map):
   """Main loop to monitor accounts and process tweets."""
   output_sheet = gsheet_client.open(OUTPUT_SHEET_NAME).sheet1
   print("Starting real-time monitoring of target accounts...")
  
   # Keep track of processed tweets to avoid duplicates
   processed_tweet_ids = set()


   while True:
       try:
           for username, user_id in user_ids_map.items():
               if not user_id:
                   continue
              
               # Fetch recent tweets from the user's timeline
               response = x_client.get_users_tweets(
                   id=user_id,
                   max_results=5, # Check the 5 most recent tweets
                   exclude=['retweets', 'replies'],
                   tweet_fields=['created_at', 'text']
               )


               if not response.data:
                   continue


               for tweet in response.data:
                   if tweet.id in processed_tweet_ids:
                       continue # Skip already processed tweet


                   processed_tweet_ids.add(tweet.id)
                   alpha_signal = parse_tweet_for_alpha(tweet.text)


                   if alpha_signal:
                       print(f"\n--- ALPHA DETECTED from @{username} ---")
                       print(f"Tweet: {tweet.text[:100]}...")
                       print(f"Signal: {alpha_signal}")


                       # Extract mandatory data
                       contract_address = alpha_signal.get('value')
                       if alpha_signal['type'] == 'cashtag':
                           # For cashtags, we can't be sure of the CA, so we skip for now
                           # A more advanced version could try to find the CA from the cashtag
                           print("Signal is a cashtag. CA not available. Skipping hype calculation for now.")
                           continue


                       # Trigger hype velocity calculation
                       hype_15m = calculate_hype_velocity(x_client, contract_address, 15)
                       hype_1hr = calculate_hype_velocity(x_client, contract_address, 60)
                       hype_24hr = calculate_hype_velocity(x_client, contract_address, 24 * 60)


                       print(f"Hype Velocity: {hype_15m} (15m), {hype_1hr} (1hr), {hype_24hr} (24h)")


                       # Prepare data for Google Sheet
                       output_data = {
                           'Coin Ticker/Name': 'N/A', # Would need another API to get this from CA
                           'Contract Address': contract_address,
                           'Blockchain': alpha_signal.get('chain', 'Unknown'),
                           'Source Account': f"@{username}",
                           'Detection Time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                           'Hype Velocity (15m)': hype_15m,
                           'Hype Velocity (1hr)': hype_1hr,
                           'Total Mentions (24h)': hype_24hr,
                           'Link to Source Tweet': f"https://twitter.com/{username}/status/{tweet.id}",
                           'Launchpad Link': alpha_signal.get('link', 'N/A')
                       }


                       # Append to Google Sheet
                       output_sheet.insert_row(list(output_data.values()), 2) # Insert at row 2 to keep headers
                       print("Data successfully written to Google Sheet.")
                       print("---------------------------------------\n")




           # Polling interval: wait before checking timelines again
           # Be mindful of X API rate limits. 60 seconds is a safe starting point.
           print(f"Cycle complete. Waiting 60 seconds...")
           time.sleep(60)


       except Exception as e:
           print(f"An error occurred in the main loop: {e}")
           print("Retrying in 2 minutes...")
           time.sleep(120)




# --- MAIN EXECUTION ---


if __name__ == "__main__":
   x_client, gsheet_client = initialize_clients()


   if x_client and gsheet_client:
       target_accounts = get_target_accounts(gsheet_client)
       if target_accounts:
           # Convert usernames to user IDs for more efficient API calls
           user_ids_map = {username: get_user_id(x_client, username) for username in target_accounts}
           print(f"User IDs fetched: {user_ids_map}")
           monitor_accounts(x_client, gsheet_client, user_ids_map)
       else:
           print("No target accounts found. Exiting.")
   else:
       print("Failed to initialize API clients. Exiting.")