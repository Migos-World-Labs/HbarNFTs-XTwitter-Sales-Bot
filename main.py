#!/usr/bin/env python3
"""
NFT Sale & Mint Notification Bot
Monitors SentX.io for NFT mints and secondary sales, then posts updates to Twitter.
Configure your collection via environment variables in .env (see .env.example).
"""

import time
import logging
from datetime import datetime
from config import Config
from sentx_api import SentXAPI
from twitter_bot import TwitterBot
from price_fetcher import PriceFetcher
from image_processor import ImageProcessor
from utils import setup_logging, load_processed_sales, save_processed_sales
from rarity import save_nft_rarity, format_rarity_text

def main():
    """Main bot execution loop"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting NFT Mint & Sale Notification Bot")
    
    try:
        # Initialize components
        config = Config()
        sentx_api = SentXAPI(config.SENTX_API_KEY)
        twitter_bot = TwitterBot(
            config.TWITTER_BEARER_TOKEN,
            config.TWITTER_CONSUMER_KEY,
            config.TWITTER_CONSUMER_SECRET,
            config.TWITTER_ACCESS_TOKEN,
            config.TWITTER_ACCESS_TOKEN_SECRET
        )
        price_fetcher = PriceFetcher()
        image_processor = ImageProcessor()
        
        # Load processed sales to avoid duplicates
        processed_sales = load_processed_sales()
        
        logger.info(f"Bot initialized. Monitoring collection: {config.COLLECTION_ID}")
        
        while True:
            try:
                logger.info(f"Checking for new {config.COLLECTION_NAME} mints and sales...")
                
                # Get mints from SentX launchpad API
                mints = sentx_api.get_recent_mints(config.COLLECTION_ID, limit=50)
                
                # Get secondary sales from SentX market API
                sales = sentx_api.get_recent_sales(config.COLLECTION_ID, limit=50)
                
                # Process both mints and sales
                all_activities = []
                if mints:
                    all_activities.extend(mints)
                if sales:
                    all_activities.extend(sales)
                    
                if not all_activities:
                    logger.info("No mint data received")
                    time.sleep(config.POLL_INTERVAL)
                    continue
                
                new_mints = []
                current_time = datetime.now()
                
                for mint in all_activities:
                    # SentX API format: nftSerialId, saleDate, etc.
                    mint_id = f"{mint.get('nftSerialId', mint.get('serialId'))}_{mint.get('saleDate', mint.get('timestamp'))}"
                    
                    # Only process mints that haven't been posted before
                    if mint_id not in processed_sales:
                        mint_date_str = mint.get('saleDate', mint.get('timestamp'))
                        if mint_date_str:
                            try:
                                # Parse the mint date
                                mint_date = datetime.fromisoformat(mint_date_str.replace('Z', '+00:00'))
                                time_diff = current_time - mint_date.replace(tzinfo=None)
                                
                                # Time window: 15 minutes for production
                                if time_diff.total_seconds() <= 900:
                                    new_mints.append(mint)
                                    processed_sales.add(mint_id)
                                else:
                                    # Add to processed to avoid checking again
                                    processed_sales.add(mint_id)
                                    
                            except Exception as date_error:
                                logger.warning(f"Could not parse mint date {mint_date_str}: {date_error}")
                                processed_sales.add(mint_id)
                
                if not new_mints:
                    logger.info("No new mints found")
                    time.sleep(config.POLL_INTERVAL)
                    continue
                
                logger.info(f"Found {len(new_mints)} new mints to process")
                
                # Get current HBAR price
                hbar_price = price_fetcher.get_hbar_price()
                if not hbar_price:
                    logger.error("Failed to get HBAR price, skipping this cycle")
                    time.sleep(config.POLL_INTERVAL)
                    continue
                
                # Get floor price for the collection
                floor_price = sentx_api.get_floor_price(config.COLLECTION_ID)
                if floor_price:
                    logger.info(f"{config.COLLECTION_NAME} floor price: {floor_price} HBAR")
                
                # Process each new mint
                for mint in new_mints[:5]:  # Limit to 5 mints per cycle to avoid rate limits
                    try:
                        # Extract token ID from SentX API format
                        token_id = str(mint.get('nftSerialId', mint.get('serialId', 'unknown')))
                        
                        # Get NFT metadata
                        metadata = sentx_api.get_nft_metadata(config.COLLECTION_ID, token_id)
                        
                        if not metadata:
                            logger.warning(f"Failed to get metadata for token {token_id}")
                            continue
                        
                        # Extract additional data from the mint record
                        if mint.get('nftName'):
                            metadata['name'] = mint['nftName']
                        if mint.get('nftImage'):
                            metadata['image'] = mint['nftImage']
                        
                        # Extract rank data from SentX API response
                        rank = mint.get('rarityRank') or mint.get('rank') or mint.get('nftRank')
                        if rank:
                            rank = int(rank)
                            metadata['rank'] = rank
                            # Save rarity data to database
                            save_nft_rarity(
                                serial_id=int(token_id),
                                nft_name=metadata.get('name', f'{config.COLLECTION_NAME} #{token_id}'),
                                rank=rank,
                                image_url=mint.get('nftImage') or mint.get('imageCDN')
                            )
                            logger.info(f"Token #{token_id} has rank {rank} - {format_rarity_text(rank)}")
                        
                        
                        # Download and process image from mint data
                        image_path = None
                        # Try multiple image sources from mint data
                        image_sources = [
                            mint.get('imageCDN'),  # Best quality CDN image
                            mint.get('nftImage'),  # IPFS image from mint
                            metadata.get('image') if metadata else None  # Fallback to metadata
                        ]
                        
                        for img_url in image_sources:
                            if img_url and 'QmDefaultHash' not in img_url:
                                try:
                                    image_path = image_processor.download_and_process_image(img_url, token_id)
                                    if image_path:
                                        break
                                except Exception:
                                    continue
                        
                        # Calculate USD value from SentX format
                        hbar_amount = float(mint.get('salePrice', 0))
                        usd_value = hbar_amount * hbar_price
                        
                        # Create tweet content for mint
                        activity_type = mint.get('activity_type', 'mint')  # Default to mint
                        tweet_text = format_tweet_text(mint, metadata, hbar_amount, usd_value, floor_price, hbar_price, activity_type, config)
                        
                        # Post to Twitter (public tweet)
                        twitter_success = twitter_bot.post_sale_tweet(tweet_text, image_path)

                        if twitter_success:
                            logger.info(f"Posted tweet for token #{token_id}")
                        else:
                            logger.error(f"Failed to post tweet for token #{token_id}")
                        
                        # Clean up image file
                        if image_path:
                            image_processor.cleanup_image(image_path)
                        
                        # Rate limit protection
                        time.sleep(10)
                        
                    except Exception as e:
                        token_id = mint.get('nftSerialId', mint.get('serialId', 'unknown'))
                        logger.error(f"Error processing mint {token_id}: {str(e)}")
                        continue
                
                # Save processed mints
                save_processed_sales(processed_sales)
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
            
            # Wait before next check
            time.sleep(config.POLL_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

def format_tweet_text(sale, metadata, hbar_amount, usd_value, floor_price, hbar_price, activity_type='sale', config=None):
    """
    Format the tweet text for a mint or sale.

    ──────────────────────────────────────────────────
     CUSTOMISATION TIPS
    ──────────────────────────────────────────────────
    Edit the tweet text blocks below to change the wording,
    add hashtags, or rearrange the layout.

    Available variables you can use:
      config.COLLECTION_NAME  — your collection name
      name                    — the individual NFT name (e.g. "Wild Tiger #42")
      hbar_amount             — sale/mint price in HBAR (float)
      usd_value               — sale/mint price in USD (float)
      rarity_line             — formatted rarity string (e.g. "🔴 Mythic | Rank #5")
      collection_url          — link to your SentX collection page
      config.COLLECTION_WEBSITE — your website (empty string if not set)
      token_id                — the NFT serial number

    TIP: Tweets have a 280 character limit. Keep an eye on length
         if you add hashtags or extra lines.
    ──────────────────────────────────────────────────
    """
    if config is None:
        config = Config()

    token_id = sale.get('nftSerialId', sale.get('serialId', 'unknown'))
    name = metadata.get('name', f'{config.COLLECTION_NAME} #{token_id}')
    collection_url = f"https://sentx.io/nft-marketplace/{config.SENTX_COLLECTION_SLUG}"

    rank = metadata.get('rank')
    rarity_line = ""
    if rank:
        rarity_line = f"{format_rarity_text(rank)}\n"

    if activity_type == 'mint':
        # ── MINT TWEET FORMAT ─────────────────────────────────────────────────
        # Edit this block to change what mint tweets look like
        tweet = f"{config.COLLECTION_NAME} Mint\n\n"
        tweet += f"{name} has been minted!\n"
        tweet += rarity_line
        tweet += f"Minted for: {hbar_amount:.0f} HBAR\n\n"
        tweet += f"Mint on @SentX_io {collection_url}\n"
        if config.COLLECTION_WEBSITE:
            tweet += f"Website: {config.COLLECTION_WEBSITE}"
    else:
        # ── SALE TWEET FORMAT ─────────────────────────────────────────────────
        # Edit this block to change what secondary sale tweets look like
        tweet = f"{config.COLLECTION_NAME} Sale Alert\n\n"
        tweet += f"{name}\n"
        tweet += rarity_line
        tweet += f"Sale Price: {hbar_amount:.0f} HBAR\n\n"
        tweet += f"View the collection {collection_url}\n"
        if config.COLLECTION_WEBSITE:
            tweet += f"Website: {config.COLLECTION_WEBSITE}"

    return tweet

if __name__ == "__main__":
    main()
