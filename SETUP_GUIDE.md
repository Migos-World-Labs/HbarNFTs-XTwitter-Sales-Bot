# NFT Mint & Sale Bot — Step-by-Step Setup Guide

This guide walks you through everything you need to get the bot running and posting tweets for your own NFT collection on SentX.

---

## What You'll Need Before You Start

- A computer with Python 3.11+ installed (or a cloud service — no local install needed)
- A [SentX.io](https://sentx.io) account with an API key
- A [Twitter Developer](https://developer.twitter.com) account with Elevated access
- A free PostgreSQL database (setup instructions below)

Estimated setup time: **20–30 minutes**

---

## Step 1 — Get Your SentX API Key

1. Log in to [sentx.io](https://sentx.io)
2. Click your profile icon in the top right
3. Go to **User Settings → API**
4. Click **Generate API Key** and copy the key
5. Save it — you'll need it later as `SENTX_API_KEY`

---

## Step 2 — Set Up Your Twitter Developer Account

The bot posts tweets using Twitter's official API. You need **Elevated access** to upload images (free to apply for).

### 2a. Create a Developer Account

1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Sign in with the Twitter account you want the bot to tweet from
3. Click **Sign up for Free Account** and fill in the form
4. Accept the terms and submit

### 2b. Create a Project and App

1. In the developer portal, go to **Projects & Apps → Overview**
2. Click **New Project**, give it a name, and follow the prompts
3. When asked to create an app, give it a name (e.g. "My NFT Bot")

### 2c. Apply for Elevated Access (Required for Image Tweets)

Without Elevated access, image uploads will fail and the bot will post text-only tweets.

1. In the portal, go to **Products → Elevated**
2. Click **Apply** and fill in the form (what you're building, how you'll use the API)
3. Approval is usually instant or within a few hours

### 2d. Set App Permissions

1. In your app settings, click **App permissions**
2. Change to **Read and Write** (the bot needs to post tweets)
3. Save the changes

> **Important:** After changing permissions you must regenerate your access tokens (Step 2e) — old tokens will not have the new permissions.

### 2e. Get Your API Keys and Tokens

1. In your app, go to **Keys and Tokens**
2. Under **Consumer Keys**, click **Regenerate** and copy:
   - `API Key` → this is your `TWITTER_CONSUMER_KEY`
   - `API Key Secret` → this is your `TWITTER_CONSUMER_SECRET`
3. Under **Authentication Tokens**, click **Generate** for **Access Token and Secret** and copy:
   - `Access Token` → this is your `TWITTER_ACCESS_TOKEN`
   - `Access Token Secret` → this is your `TWITTER_ACCESS_TOKEN_SECRET`
4. Under **Bearer Token**, copy the value → this is your `TWITTER_BEARER_TOKEN`

You should now have all five Twitter values ready.

---

## Step 3 — Set Up Your PostgreSQL Database

The bot uses a PostgreSQL database to store rarity data. You need a free database from one of these providers:

| Provider | Free Tier | Link |
|---|---|---|
| Neon | 512MB, no credit card required | [neon.tech](https://neon.tech) |
| Supabase | 500MB, no credit card required | [supabase.com](https://supabase.com) |
| Railway | Paid plans from $5/month, includes database | [railway.app](https://railway.app) |

### Getting Your DATABASE_URL

Every provider gives you a **connection string** that looks like:

```
postgresql://user:password@host:port/database
```

Copy this string — it's your `DATABASE_URL`.

### Creating the Required Table

After connecting to your database (each provider has a built-in SQL editor), run this SQL once:

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

This creates the table the bot uses to track rarity data. You only need to do this once.

---

## Step 4 — Configure Your Collection

### 4a. Find Your Collection Details

You need three pieces of information about your collection:

**Hedera Token ID (`COLLECTION_ID`)**
This is the on-chain identifier for your NFT collection. It looks like `0.0.6024491`. You can find it on your collection's SentX page or in your minting records.

**SentX URL Slug (`SENTX_COLLECTION_SLUG`)**
Open your collection on SentX. The URL looks like:
`https://sentx.io/nft-marketplace/your-collection-name`
The part at the end (`your-collection-name`) is your slug.

**Total Supply (`TOTAL_SUPPLY`)**
The total number of NFTs in your collection.

### 4b. Set Up Rarity Tiers

Open `rarity.py` and replace the `RARITY_TIERS` dictionary with your own collection's rarity breakdown. Each tier needs:

- `min_rank` and `max_rank` — the rank range (rank 1 = rarest)
- `count` — how many NFTs are in this tier
- `color` — a hex color code (for display)
- `emoji` — the emoji shown in tweets

Example for a 1,000-supply collection:

```python
RARITY_TIERS = {
    'Legendary': {
        'min_rank': 1,
        'max_rank': 50,
        'count': 50,
        'color': '#FFD700',
        'emoji': '🟡'
    },
    'Rare': {
        'min_rank': 51,
        'max_rank': 200,
        'count': 150,
        'color': '#0000FF',
        'emoji': '🔵'
    },
    'Common': {
        'min_rank': 201,
        'max_rank': 1000,
        'count': 800,
        'color': '#808080',
        'emoji': '⚪'
    },
}
```

Make sure your ranges cover every rank from 1 to your `TOTAL_SUPPLY` with no gaps.

> **Tip:** The rarity ranks come from SentX's `rarityRank` field in the API. Check your collection on SentX to see how many NFTs fall into each rarity category.

---

## Step 5 — Set Your Environment Variables

Copy the example file:

```bash
cp .env.example .env
```

Open `.env` and fill in all your values:

```env
DATABASE_URL=postgresql://user:password@host:5432/database

SENTX_API_KEY=your_sentx_api_key

TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_CONSUMER_KEY=your_consumer_key
TWITTER_CONSUMER_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

COLLECTION_ID=0.0.XXXXXXX
COLLECTION_NAME=Your Collection Name
SENTX_COLLECTION_SLUG=your-collection-slug
TOTAL_SUPPLY=1000

# Optional — shown at the end of tweets. Remove this line to omit it.
COLLECTION_WEBSITE=yourcollection.com

# Optional — how often to check SentX in seconds (default: 30)
POLL_INTERVAL=30
```

---

## Step 6 — Test Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the bot:

```bash
python main.py
```

If everything is configured correctly you'll see log output like:

```
2026-01-01 12:00:00,000 - twitter_bot - INFO - Twitter authentication successful for user: YourBotAccount
2026-01-01 12:00:00,001 - __main__ - INFO - Bot initialized. Monitoring collection: 0.0.XXXXXXX
2026-01-01 12:00:00,002 - __main__ - INFO - Checking for new mints and sales...
```

If you see an error about missing environment variables, double-check your `.env` file. If you see a Twitter authentication error, check your API keys and that you have Read + Write permissions set.

---

## Step 7 — Deploy (Keep the Bot Running 24/7)

Once the bot works locally, deploy it to a cloud service so it keeps running without your computer being on.

---

### Option A — Railway (Recommended)

Railway is the easiest option. It has a free tier and a `railway.toml` is already included in this project.

1. Sign up at [railway.app](https://railway.app)
2. Click **New Project → Deploy from GitHub Repo**
3. Connect your GitHub account and select your fork of this repo
4. Once the project is created, go to **Variables** and add all your environment variables from Step 5
5. Railway will automatically deploy and restart the bot if it crashes

**Free tier note:** Railway's free Hobby plan gives you $5 of credit per month. The bot uses very little compute, so this typically covers it.

---

### Option B — Render

1. Sign up at [render.com](https://render.com)
2. Click **New → Background Worker**
3. Connect your GitHub repo
4. Set the **Start Command** to: `python main.py`
5. Go to **Environment** and add all your variables from Step 5
6. Click **Create Background Worker**

The `Procfile` in this project (`worker: python main.py`) is also supported by Render automatically.

---

### Option C — Heroku

1. Sign up at [heroku.com](https://heroku.com) and install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. In your project folder, run:
   ```bash
   heroku create your-bot-name
   heroku config:set SENTX_API_KEY=your_key TWITTER_BEARER_TOKEN=your_token ...
   git push heroku main
   heroku ps:scale worker=1
   ```

The `Procfile` in this project is already set up for Heroku's worker dyno.

---

### Option D — Fly.io

1. Install the [flyctl CLI](https://fly.io/docs/hands-on/install-flyctl/) and sign up
2. In your project folder, run:
   ```bash
   fly launch
   fly secrets set SENTX_API_KEY=your_key TWITTER_BEARER_TOKEN=your_token ...
   fly deploy
   ```

---

### Option E — Replit

If you're already running this on Replit:

1. Add all your environment variables under the **Secrets** tab (the padlock icon in the sidebar)
2. The bot will run via the configured workflow — click **Run** to start it
3. To keep it running after you close the browser, you need a Replit Core or Teams plan (free Replit pauses when the tab is closed)

---

## Troubleshooting

### Bot starts but no tweets are posted

- Check that your `COLLECTION_ID` and `SENTX_COLLECTION_SLUG` are correct
- Check the logs for "No new mints found" — this is normal if there has been no activity in the last 15 minutes
- Make sure there has been actual mint or sale activity on SentX for your collection

### Twitter authentication error

- Double-check all five Twitter keys are correct and have no extra spaces
- Make sure you regenerated your access tokens **after** setting Read + Write permissions
- Confirm you have Elevated access approved

### Image uploads failing (403 error)

- Confirm your Twitter app has Elevated access (not just Basic)
- Regenerate your access tokens after applying for Elevated access

### Database connection error

- Check your `DATABASE_URL` is the full connection string including username, password, host, port, and database name
- Make sure the `nft_rarity` table was created (Step 3)

### Rarity showing as "Unknown"

- Your `TOTAL_SUPPLY` env var may not match your `RARITY_TIERS` ranges in `rarity.py`
- Make sure the rank ranges in `RARITY_TIERS` cover 1 through `TOTAL_SUPPLY` with no gaps

---

## Help & Support

If you get stuck, reach out to **@Mauii_MW** on X (Twitter).

---

## Built By

This bot was built by the [Wild Tigers](https://WildTigers.World) team — an NFT collection on the Hedera Hashgraph network.

- Twitter: [@WildTigersNFT](https://twitter.com/WildTigersNFT)
- Marketplace: [sentx.io/nft-marketplace/wild-tigers](https://sentx.io/nft-marketplace/wild-tigers)
