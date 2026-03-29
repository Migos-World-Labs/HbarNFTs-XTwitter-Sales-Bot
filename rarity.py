"""
NFT Rarity System
Maps rank ranges to rarity tiers based on SentX rarityRank data.

The RARITY_TIERS dictionary below is pre-configured for the Wild Tigers collection
(Hedera token 0.0.6024491, total supply 3,332).

────────────────────────────────────────────────────────────
 CONFIGURATION GUIDE — HOW TO CUSTOMISE FOR YOUR COLLECTION
────────────────────────────────────────────────────────────
1. Replace or edit the tiers in RARITY_TIERS below to match your collection.
2. Each tier needs:
     min_rank  — lowest rank number that belongs to this tier (1 = rarest)
     max_rank  — highest rank number that belongs to this tier
     count     — how many NFTs fall in this range (max_rank - min_rank + 1)
     color     — hex colour used for display (optional, informational only)
     emoji     — emoji shown in tweets and Slack messages
3. Make sure the ranges cover every rank from 1 to your TOTAL_SUPPLY with no gaps.
4. You can add or remove tiers — there is no fixed number required.
5. Set the TOTAL_SUPPLY environment variable to match your collection size.

TIP: To find your rarity distribution, check your collection on SentX or your
     metadata — the rarityRank field goes from 1 (rarest) to TOTAL_SUPPLY (most common).
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# EDIT THIS: Replace these tiers with your own collection's rarity breakdown.
# The tiers below are for Wild Tigers (3,332 total supply).
# ─────────────────────────────────────────────────────────────────────────────
RARITY_TIERS = {
    'Mythic': {
        'min_rank': 1,
        'max_rank': 49,
        'count': 49,
        'color': '#FF0000',  # Red
        'emoji': '🔴'
    },
    'Legendary': {
        'min_rank': 50,
        'max_rank': 166,
        'count': 117,
        'color': '#FFD700',  # Gold
        'emoji': '🟡'
    },
    'Epic': {
        'min_rank': 167,
        'max_rank': 416,
        'count': 250,
        'color': '#9B30FF',  # Purple
        'emoji': '🟣'
    },
    'Rare': {
        'min_rank': 417,
        'max_rank': 832,
        'count': 416,
        'color': '#0000FF',  # Blue
        'emoji': '🔵'
    },
    'Uncommon': {
        'min_rank': 833,
        'max_rank': 1665,
        'count': 833,
        'color': '#00FF00',  # Green
        'emoji': '🟢'
    },
    'Common': {
        'min_rank': 1666,
        'max_rank': 3315,
        'count': 1650,
        'color': '#808080',  # Grey
        'emoji': '⚪'
    },
    'Animated Edition': {
        'min_rank': 3316,
        'max_rank': 3332,
        'count': 17,
        'color': '#00FFFF',  # Cyan
        'emoji': '✨'
    }
}
# ─────────────────────────────────────────────────────────────────────────────


def get_tier_from_rank(rank: int) -> Tuple[str, str, str]:
    """
    Get the tier name, emoji, and color from a rank number.

    Args:
        rank: The NFT rank (1 = rarest, higher = more common)

    Returns:
        Tuple of (tier_name, emoji, color_hex)
    """
    if rank is None or rank < 1:
        return ('Unknown', '❓', '#000000')

    for tier_name, tier_data in RARITY_TIERS.items():
        if tier_data['min_rank'] <= rank <= tier_data['max_rank']:
            return (tier_name, tier_data['emoji'], tier_data['color'])

    return ('Unknown', '❓', '#000000')


def get_db_connection():
    """Get database connection using DATABASE_URL environment variable."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not set")
        return None
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None


def save_nft_rarity(serial_id: int, nft_name: str, rank: int, image_url: str = None) -> bool:
    """
    Save or update NFT rarity data in the database.

    Args:
        serial_id: The NFT serial ID
        nft_name: Name of the NFT
        rank: The rarity rank
        image_url: URL to the NFT image

    Returns:
        True if successful, False otherwise
    """
    tier_name, emoji, color = get_tier_from_rank(rank)

    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nft_rarity (serial_id, nft_name, rank, tier, tier_emoji, tier_color, image_url, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (serial_id)
                DO UPDATE SET
                    nft_name = EXCLUDED.nft_name,
                    rank = EXCLUDED.rank,
                    tier = EXCLUDED.tier,
                    tier_emoji = EXCLUDED.tier_emoji,
                    tier_color = EXCLUDED.tier_color,
                    image_url = EXCLUDED.image_url,
                    updated_at = CURRENT_TIMESTAMP
            """, (serial_id, nft_name, rank, tier_name, emoji, color, image_url))
            conn.commit()
            logger.info(f"Saved rarity data for #{serial_id}: Rank {rank} ({tier_name} {emoji})")
            return True
    except Exception as e:
        logger.error(f"Error saving rarity data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_nft_rarity(serial_id: int) -> Optional[Dict]:
    """
    Get NFT rarity data from the database.

    Args:
        serial_id: The NFT serial ID

    Returns:
        Dictionary with rarity data or None
    """
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT serial_id, nft_name, rank, tier, tier_emoji, tier_color, image_url
                FROM nft_rarity
                WHERE serial_id = %s
            """, (serial_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    except Exception as e:
        logger.error(f"Error getting rarity data: {e}")
        return None
    finally:
        conn.close()


def format_rarity_text(rank: int) -> str:
    """
    Format rarity text for tweet display.

    Args:
        rank: The NFT rank

    Returns:
        Formatted string like "🔴 Mythic | Rank #42"

    TIP: Edit this function if you want to change how rarity appears in tweets.
         e.g. return f"{emoji} {tier_name} (Rank #{rank})" for a different format.
    """
    tier_name, emoji, _ = get_tier_from_rank(rank)
    return f"{emoji} {tier_name} | Rank #{rank}"
