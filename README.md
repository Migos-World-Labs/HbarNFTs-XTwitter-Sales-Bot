# NFT Sale & Mint Notification Bot

A Python bot that monitors the [SentX.io](https://sentx.io) marketplace on the **Hedera Hashgraph** network for NFT mints and secondary sales, then automatically posts updates to **Twitter**.

Built originally for the Wild Tigers collection — fully configurable for any SentX collection via environment variables.

---

## Features

- Polls SentX for new mints (launchpad) and secondary sales every 30 seconds
- Posts formatted tweets with NFT image, rarity tier, and price (HBAR + USD)
- 7-tier rarity system (fully customizable in `rarity.py`)
- Stores rarity data to PostgreSQL for historical tracking
- Avoids duplicate posts using a local JSON state file
- Multiple IPFS gateway fallbacks for reliable image downloads

---

## How It Works

The bot monitors two separate types of NFT activity on SentX and posts a different tweet format for each:

### 1. Launchpad Mints (Forever Mint)
Triggered when someone mints an NFT directly from your collection's launchpad page on SentX. The bot detects this via the SentX launchpad activity API.

**Example tweet:**
```
Wild Tigers Mint

Wild Tiger #1234 has been minted!
🔵 Rare | Rank #521

Minted for: 150 HBAR

Mint on @SentX_io https://sentx.io/nft-marketplace/wild-tigers
Website: WildTigers.World
```

### 2. Secondary Sales
Triggered when an NFT is sold on the SentX secondary marketplace (one holder selling to another). The bot detects this via the SentX market activity API, filtering for `Sold` events only.

**Example tweet:**
```
Wild Tigers Sale Alert

Wild Tiger #88
🟡 Legendary | Rank #72

Sale Price: 800 HBAR

View the collection https://sentx.io/nft-marketplace/wild-tigers
Website: WildTigers.World
```

Both activity types include the NFT image, rarity tier, and rank pulled from SentX's `rarityRank` field. The bot checks for new activity every 30 seconds and processes up to 5 events per cycle to stay within Twitter's rate limits.

---

## Requirements

- Python 3.11+
- A PostgreSQL database (Railway, Supabase, Neon, etc.)
- A [SentX.io](https://sentx.io) API key
- A [Twitter Developer](https://developer.twitter.com) app with **Elevated** access (required for media uploads) and Read + Write permissions

---

## Quick Start

> **New here?** See the full [Step-by-Step Setup Guide](SETUP_GUIDE.md) for detailed instructions including getting API keys, configuring rarity tiers, and deploying to Railway, Render, Heroku, Fly.io, or Replit.

### 1. Clone the repository

```bash
git clone https://github.com/your-username/nft-mint-bot.git
cd nft-mint-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your credentials. The required variables are:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SENTX_API_KEY` | Your SentX.io API key |
| `TWITTER_BEARER_TOKEN` | Twitter API v2 bearer token |
| `TWITTER_CONSUMER_KEY` | Twitter app consumer key |
| `TWITTER_CONSUMER_SECRET` | Twitter app consumer secret |
| `TWITTER_ACCESS_TOKEN` | Twitter user access token |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter user access token secret |
| `COLLECTION_ID` | Hedera token ID (e.g. `0.0.6024491`) |
| `COLLECTION_NAME` | Display name (e.g. `Wild Tigers`) |
| `SENTX_COLLECTION_SLUG` | SentX URL slug (e.g. `wild-tigers`) |
| `TOTAL_SUPPLY` | Total NFT count in the collection |

See `.env.example` for the full list of optional variables.

### 4. Set up the database

The bot needs one table in your PostgreSQL database. Run this SQL to create it:

```sql
CREATE TABLE IF NOT EXISTS nft_rarity (
    serial_id INTEGER PRIMARY KEY,
    nft_name TEXT,
    rank INTEGER,
    tier TEXT,
    tier_emoji TEXT,
    tier_color TEXT,
    image_url TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Run the bot

```bash
python main.py
```

---

## Customizing for Your Collection

### Rarity Tiers

The rarity system in `rarity.py` is pre-configured for the Wild Tigers collection (3,332 total supply). To use it for your own collection, open `rarity.py` and update the `RARITY_TIERS` dictionary with your own rank ranges, counts, colors, and emojis:

```python
RARITY_TIERS = {
    'Legendary': {
        'min_rank': 1,
        'max_rank': 100,
        'count': 100,
        'color': '#FFD700',
        'emoji': '🟡'
    },
    'Rare': {
        'min_rank': 101,
        'max_rank': 500,
        'count': 400,
        'color': '#0000FF',
        'emoji': '🔵'
    },
    # ... add more tiers as needed
}
```

Make sure the rank ranges cover your entire `TOTAL_SUPPLY` without gaps.

### Tweet Format

The tweet text is built in `format_tweet_text()` in `main.py`. Edit that function to change the wording, add hashtags, or rearrange the layout.

---

## Deployment

The bot is configured to run as a long-running worker process.

### Railway

A `railway.toml` is included. Connect your GitHub repo to Railway, add your environment variables in the Railway dashboard, and deploy.

### Heroku / Render / Fly.io

A `Procfile` is included with `worker: python main.py`. Add your environment variables in the platform's dashboard and deploy.

### Replit

1. Fork or import this repo into Replit.
2. Add your environment variables under the **Secrets** tab.
3. The bot will run via the configured workflow.

---

## Environment Variables Reference

See [`.env.example`](.env.example) for the full list with descriptions.

---

## Project Structure

```
.
├── main.py              # Entry point and main polling loop
├── config.py            # Centralized configuration from environment variables
├── sentx_api.py         # SentX.io API client (mints, sales, metadata)
├── twitter_bot.py       # Twitter API client (tweets and media upload)
├── image_processor.py   # Downloads and resizes NFT images for Twitter
├── price_fetcher.py     # CoinGecko HBAR/USD price fetching with caching
├── rarity.py            # Rarity tier system and PostgreSQL storage
├── utils.py             # Logging, state persistence, formatting helpers
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── README.md            # Project overview and quick start
├── SETUP_GUIDE.md       # Full step-by-step setup and deployment guide
├── Procfile             # Heroku/Render worker process definition
└── railway.toml         # Railway deployment configuration
```

---

## API Keys & Setup Guides

### SentX API Key
Log in to [sentx.io](https://sentx.io), go to **User Settings → API**, and generate a key.

### Twitter API

Go to [developer.twitter.com](https://developer.twitter.com) and create a project and app.

**Access level required:**

| Feature | Access Level |
|---|---|
| Posting tweets (text only) | Basic (free) |
| Posting tweets with images | **Elevated** (free, apply in the portal) |

**Steps:**
1. Apply for **Elevated** access in the developer portal (required for image uploads).
2. In your app settings, set permissions to **Read and Write**.
3. Generate **User Access Tokens** (Access Token + Secret) — these are tied to your Twitter account. Do not confuse these with app-only bearer tokens.
4. Copy all five values into your environment: `TWITTER_BEARER_TOKEN`, `TWITTER_CONSUMER_KEY`, `TWITTER_CONSUMER_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`.

### PostgreSQL
Free tiers available on [Railway](https://railway.app), [Supabase](https://supabase.com), and [Neon](https://neon.tech). Run the table creation SQL from Step 4 above after connecting.

---

## Help & Support

If you need help setting up the bot, reach out to **@Mauii_MW** on X (Twitter).

---

## Built By

This bot was built by the [Wild Tigers](https://WildTigers.World) team — an NFT collection on the Hedera Hashgraph network.

- Twitter: [@WildTigersNFT](https://twitter.com/WildTigersNFT)
- Marketplace: [sentx.io/nft-marketplace/wild-tigers](https://sentx.io/nft-marketplace/wild-tigers)

We open-sourced this so other NFT projects on Hedera/SentX can run their own mint and sale bots without starting from scratch.

---

## License

MIT License — you are free to use, modify, and distribute this project. See [LICENSE](LICENSE) for the full text.

If you build something with this, a shoutout to Wild Tigers is always appreciated!
