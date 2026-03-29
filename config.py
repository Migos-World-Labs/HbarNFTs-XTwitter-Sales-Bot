"""
Configuration settings for the NFT Sale & Mint Notification Bot

────────────────────────────────────────────────────────────
 CONFIGURATION GUIDE
────────────────────────────────────────────────────────────
All settings are loaded from environment variables.
Set them in your .env file (see .env.example for the full list).

REQUIRED — the bot will not start without these:
  SENTX_API_KEY, TWITTER_BEARER_TOKEN, TWITTER_CONSUMER_KEY,
  TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN,
  TWITTER_ACCESS_TOKEN_SECRET, DATABASE_URL,
  COLLECTION_ID, COLLECTION_NAME, SENTX_COLLECTION_SLUG, TOTAL_SUPPLY

OPTIONAL — the bot works fine without these:
  COLLECTION_WEBSITE, POLL_INTERVAL

TWEAKABLE SETTINGS (no env var needed — edit the values directly below):
  TWITTER_RATE_LIMIT_DELAY  — pause between tweets (default 60s)
  API_RETRY_ATTEMPTS        — how many times to retry failed API calls
  MAX_IMAGE_SIZE            — max image dimensions before resizing
  IMAGE_QUALITY             — JPEG quality for processed images (1-95)
"""

import os


class Config:
    """Configuration class for bot settings"""

    def __init__(self):

        # ── Required: API Keys ────────────────────────────────────────────────
        # Get these from developer.twitter.com and sentx.io
        self.SENTX_API_KEY = os.getenv('SENTX_API_KEY', '')
        self.TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
        self.TWITTER_CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY', '')
        self.TWITTER_CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET', '')
        self.TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
        self.TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')

        # ── Required: NFT Collection ──────────────────────────────────────────
        # COLLECTION_ID: Hedera token ID (format: 0.0.XXXXXXX)
        self.COLLECTION_ID = os.getenv('COLLECTION_ID', '0.0.6024491')

        # COLLECTION_NAME: Used in tweets (e.g. "Wild Tigers")
        self.COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'Wild Tigers')

        # SENTX_COLLECTION_SLUG: The URL slug on SentX (e.g. "wild-tigers")
        # Find it in your collection URL: sentx.io/nft-marketplace/<slug>
        self.SENTX_COLLECTION_SLUG = os.getenv('SENTX_COLLECTION_SLUG', 'wild-tigers')

        # TOTAL_SUPPLY: Total number of NFTs (used in rarity calculations)
        self.TOTAL_SUPPLY = int(os.getenv('TOTAL_SUPPLY', '3332'))

        # ── Optional: Collection Branding ─────────────────────────────────────
        # COLLECTION_WEBSITE: Shown at the end of tweets — leave blank to omit
        self.COLLECTION_WEBSITE = os.getenv('COLLECTION_WEBSITE', 'WildTigers.World')

        # ── Polling ───────────────────────────────────────────────────────────
        # How often (seconds) the bot checks SentX for new activity
        # TIP: 30s is good for live tracking; increase to 60s+ to reduce API calls
        self.POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '30'))

        # ── API Endpoints (do not change unless SentX/CoinGecko change URLs) ──
        self.SENTX_BASE_URL = 'https://api.sentx.io'
        self.COINGECKO_API_URL = 'https://api.coingecko.com/api/v3'

        # ── Image Processing ──────────────────────────────────────────────────
        # TIP: Twitter requires images under 5MB. 1024x1024 at quality 85 is safe.
        #      Lower IMAGE_QUALITY (e.g. 75) if uploads are slow or failing.
        self.MAX_IMAGE_SIZE = (1024, 1024)
        self.IMAGE_QUALITY = 85          # JPEG quality 1-95 (higher = better quality, larger file)
        self.TEMP_IMAGE_DIR = '/tmp'     # Temporary folder for image processing

        # ── Rate Limiting ─────────────────────────────────────────────────────
        # TIP: Twitter's free tier allows ~17 tweets/day. Keep TWITTER_RATE_LIMIT_DELAY
        #      at 60s or higher to avoid hitting limits during busy periods.
        self.TWITTER_RATE_LIMIT_DELAY = 60   # seconds to wait after each tweet
        self.API_RETRY_ATTEMPTS = 5          # retries before giving up on a failed API call
        self.API_RETRY_DELAY = 3             # seconds between retries (uses exponential backoff)

        # Validate required environment variables on startup
        self._validate_config()

    def _validate_config(self):
        """Validate that all required environment variables are present."""
        required_vars = [
            'SENTX_API_KEY',
            'TWITTER_BEARER_TOKEN',
            'TWITTER_CONSUMER_KEY',
            'TWITTER_CONSUMER_SECRET',
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET'
        ]

        missing_vars = [var for var in required_vars if not getattr(self, var)]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
