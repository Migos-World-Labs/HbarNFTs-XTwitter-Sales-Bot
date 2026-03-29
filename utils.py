"""
Utility functions for the NFT Sale & Mint Notification Bot
"""

import json
import logging
import os
from typing import Set
from datetime import datetime

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('nft_bot.log', mode='a', encoding='utf-8')
        ]
    )
    
    # Set external library log levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

def load_processed_sales() -> Set[str]:
    """
    Load the set of processed sales from file
    
    Returns:
        Set of processed sale IDs
    """
    try:
        if os.path.exists('processed_sales.json'):
            with open('processed_sales.json', 'r') as f:
                data = json.load(f)
                return set(data.get('sales', []))
        else:
            return set()
    except Exception as e:
        logging.error(f"Error loading processed sales: {str(e)}")
        return set()

def save_processed_sales(processed_sales: Set[str]):
    """
    Save the set of processed sales to file
    
    Args:
        processed_sales: Set of processed sale IDs
    """
    try:
        # Keep only recent sales (limit to 10000 to prevent file from growing too large)
        if len(processed_sales) > 10000:
            # Convert to list, sort, and keep most recent 5000
            sales_list = list(processed_sales)
            processed_sales = set(sales_list[-5000:])
        
        data = {
            'sales': list(processed_sales),
            'last_updated': datetime.now().isoformat(),
            'count': len(processed_sales)
        }
        
        with open('processed_sales.json', 'w') as f:
            json.dump(data, f, indent=2)
            
        logging.debug(f"Saved {len(processed_sales)} processed sales")
        
    except Exception as e:
        logging.error(f"Error saving processed sales: {str(e)}")

def format_hbar_amount(amount: float) -> str:
    """
    Format HBAR amount for display
    
    Args:
        amount: HBAR amount as float
        
    Returns:
        Formatted string
    """
    if amount >= 1000000:
        return f"{amount / 1000000:.1f}M"
    elif amount >= 1000:
        return f"{amount / 1000:.1f}K"
    else:
        return f"{amount:.2f}"

def format_usd_amount(amount: float) -> str:
    """
    Format USD amount for display
    
    Args:
        amount: USD amount as float
        
    Returns:
        Formatted string
    """
    if amount >= 1000000:
        return f"${amount / 1000000:.1f}M"
    elif amount >= 1000:
        return f"${amount / 1000:.1f}K"
    else:
        return f"${amount:.2f}"

def validate_token_id(token_id: str) -> bool:
    """
    Validate token ID format
    
    Args:
        token_id: Token ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Token IDs should be numeric strings
        int(token_id)
        return True
    except (ValueError, TypeError):
        return False

def get_rarity_color(rarity: str) -> str:
    """
    Get color code for a rarity tier name.

    Args:
        rarity: Rarity tier name (case-insensitive)

    Returns:
        Hex color code string

    TIP: Keep this in sync with the colors defined in RARITY_TIERS in rarity.py
         if you add or rename tiers for your collection.
    """
    colors = {
        'mythic': '#FF0000',           # Red
        'legendary': '#FFD700',        # Gold
        'epic': '#9B30FF',             # Purple
        'rare': '#0000FF',             # Blue
        'uncommon': '#00FF00',         # Green
        'common': '#808080',           # Grey
        'animated edition': '#00FFFF', # Cyan
    }
    return colors.get(rarity.lower(), '#FFFFFF')

def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to maximum length with ellipsis
    
    Args:
        text: Text to truncate
        max_length: Maximum length including ellipsis
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def is_valid_hedera_id(hedera_id: str) -> bool:
    """
    Validate Hedera account/token ID format
    
    Args:
        hedera_id: Hedera ID to validate (e.g., "0.0.123456")
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        parts = hedera_id.split('.')
        if len(parts) != 3:
            return False
        
        # All parts should be numeric
        for part in parts:
            int(part)
        
        return True
    except (ValueError, AttributeError):
        return False
