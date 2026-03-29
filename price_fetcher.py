"""
Price fetching functionality for HBAR/USD conversion
"""

import requests
import logging
import time
from typing import Optional
from config import Config

class PriceFetcher:
    """Fetches cryptocurrency prices from CoinGecko API"""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NFT-Mint-Bot/1.0',
            'Accept': 'application/json'
        })
        self._last_price = None
        self._last_fetch_time = 0
        self._cache_duration = 300  # 5 minutes cache
    
    def get_hbar_price(self) -> Optional[float]:
        """
        Get current HBAR price in USD from CoinGecko
        
        Returns:
            HBAR price in USD or None if error
        """
        current_time = time.time()
        
        # Use cached price if recent
        if (self._last_price and 
            current_time - self._last_fetch_time < self._cache_duration):
            self.logger.debug(f"Using cached HBAR price: ${self._last_price}")
            return self._last_price
        
        try:
            endpoint = f"{self.config.COINGECKO_API_URL}/simple/price"
            params = {
                'ids': 'hedera-hashgraph',
                'vs_currencies': 'usd'
            }
            
            response = self._make_request('GET', endpoint, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                price = data.get('hedera-hashgraph', {}).get('usd')
                
                if price:
                    self._last_price = float(price)
                    self._last_fetch_time = current_time
                    self.logger.info(f"HBAR price updated: ${self._last_price}")
                    return self._last_price
                else:
                    self.logger.error("HBAR price not found in response")
                    return self._last_price  # Return cached if available
            else:
                self.logger.error(f"Failed to fetch HBAR price: {response.status_code if response else 'No response'}")
                return self._last_price  # Return cached if available
                
        except Exception as e:
            self.logger.error(f"Error fetching HBAR price: {str(e)}")
            return self._last_price  # Return cached if available
    
    def get_multiple_prices(self, coin_ids: list) -> Optional[dict]:
        """
        Get prices for multiple cryptocurrencies
        
        Args:
            coin_ids: List of CoinGecko coin IDs
            
        Returns:
            Dictionary of coin prices or None if error
        """
        try:
            endpoint = f"{self.config.COINGECKO_API_URL}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd'
            }
            
            response = self._make_request('GET', endpoint, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                self.logger.debug(f"Retrieved prices for {len(data)} coins")
                return data
            else:
                self.logger.error(f"Failed to fetch multiple prices: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching multiple prices: {str(e)}")
            return None
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object or None if failed
        """
        for attempt in range(self.config.API_RETRY_ATTEMPTS):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)
                
                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"CoinGecko rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.config.API_RETRY_ATTEMPTS - 1:
                    time.sleep(self.config.API_RETRY_DELAY)
                    continue
                else:
                    self.logger.error(f"All request attempts failed for {url}")
                    return None
        
        return None
