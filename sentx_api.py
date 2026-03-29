"""
SentX.io API client for fetching NFT sales and metadata
"""

import requests
import logging
import time
from typing import List, Dict, Optional
from config import Config

class SentXAPI:
    """Client for SentX.io API interactions"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = Config().SENTX_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'NFT-Mint-Bot/1.0'
        })
        self.logger = logging.getLogger(__name__)
    
    def get_recent_mints(self, collection_id: str, limit: int = 50) -> Optional[List[Dict]]:
        """
        Get recent mint events for a specific collection from SentX launchpad
        
        Args:
            collection_id: The Hedera collection ID
            limit: Maximum number of mint events to return
            
        Returns:
            List of mint event dictionaries or None if error
        """
        try:
            # Use the launchpad activity endpoint for actual mint events
            endpoint = f"{self.base_url}/v1/public/launchpad/activity"
            params = {
                'apikey': self.api_key,
                'token': collection_id,  # Filter by this collection
                'limit': limit,
                'page': 1
            }
            
            self.logger.info(f"Requesting mint events from: {endpoint}")
            response = self._make_request('GET', endpoint, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'response' in data:
                    mint_events = data['response']
                    # Add activity type for processing
                    for event in mint_events:
                        event['activity_type'] = 'mint'
                    self.logger.info(f"✅ Retrieved {len(mint_events)} mint events from launchpad API")
                    return mint_events
                else:
                    self.logger.warning(f"Unexpected launchpad API response format: {data}")
                    return []
            elif response:
                self.logger.error(f"❌ SentX API error {response.status_code}: {response.text[:200]}...")
                return None
            else:
                self.logger.error("❌ SentX API connection failed - no response received")
                self.logger.error(f"   Endpoint: {endpoint}")
                self.logger.error(f"   Params: {params}")
                self.logger.error("   Check network connectivity and SentX API status")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching launchpad activity: {str(e)}")
            return None

    def get_recent_sales(self, collection_id: str, limit: int = 50) -> Optional[List[Dict]]:
        """
        Get recent sales for a specific collection from SentX market activity
        
        Args:
            collection_id: The Hedera collection ID
            limit: Maximum number of sales to return
            
        Returns:
            List of sale dictionaries or None if error
        """
        try:
            # Use the market activity endpoint for secondary sales
            endpoint = f"{self.base_url}/v1/public/market/activity"
            params = {
                'apikey': self.api_key,
                'token': collection_id,
                'amount': limit,
                'page': 1,
                'hbarMarketOnly': 1  # Focus on HBAR transactions
            }
            
            response = self._make_request('GET', endpoint, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'marketActivity' in data:
                    activities = data['marketActivity']
                    # Filter for only "Sold" activities (actual sales)
                    sale_activities = []
                    for activity in activities:
                        stype = activity.get('saletype', '')
                        if stype == 'Sold':
                            activity['activity_type'] = 'sale'
                            sale_activities.append(activity)
                    
                    self.logger.info(f"Retrieved {len(sale_activities)} sale activities from {len(activities)} total activities")
                    return sale_activities
                else:
                    self.logger.warning(f"Unexpected market API response format: {data}")
                    return []
            else:
                self.logger.error(f"Failed to get market activity: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching market activity: {str(e)}")
            return None
    
    def get_nft_metadata(self, collection_id: str, token_id: str) -> Optional[Dict]:
        """
        Get metadata for a specific NFT using Hedera Mirror Node or from sales data
        
        Args:
            collection_id: The Hedera collection ID  
            token_id: The token ID within the collection
            
        Returns:
            Metadata dictionary or None if error
        """
        try:
            # For now, return basic metadata structure
            # This will need to be enhanced with actual Hedera Mirror Node calls
            # or SentX specific token metadata endpoints when available
            
            metadata = {
                'name': f'NFT #{token_id}',
                'rarity': 'common',  # Default rarity, should be fetched from actual metadata
                'image': f'https://ipfs.io/ipfs/QmDefaultHash/{token_id}',  # Placeholder
                'token_id': token_id,
                'collection_id': collection_id
            }
            
            # Try to get from market listings to find rarity/metadata
            try:
                listing_endpoint = f"{self.base_url}/v1/public/market/listings"
                listing_params = {
                    'apikey': self.api_key,
                    'token': collection_id,
                    'limit': 100
                }
                listing_response = self._make_request('GET', listing_endpoint, params=listing_params)
                
                if listing_response and listing_response.status_code == 200:
                    listing_data = listing_response.json()
                    if listing_data and listing_data.get('success') and 'marketListings' in listing_data:
                        # Extract metadata from listing if available
                        listings = listing_data['marketListings']
                        for listing in listings:
                            if str(listing.get('serialId')) == str(token_id):
                                metadata.update({
                                    'name': listing.get('nftName', metadata['name']),
                                    'image': listing.get('nftImage', metadata['image']),
                                    'rarity': listing.get('rarity', metadata['rarity'])  # May not be available
                                })
                                break
                                
            except Exception as listing_error:
                self.logger.debug(f"Could not get listing metadata: {listing_error}")
            
            self.logger.debug(f"Retrieved metadata for token {token_id}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error fetching metadata for token {token_id}: {str(e)}")
            return None
    
    def get_floor_price(self, collection_id: str) -> Optional[float]:
        """
        Get the floor price for a collection
        
        Args:
            collection_id: The Hedera collection ID
            
        Returns:
            Floor price in HBAR or None if error
        """
        try:
            endpoint = f"{self.base_url}/v1/public/market/floor"
            params = {
                'apikey': self.api_key,
                'token': collection_id
            }
            
            response = self._make_request('GET', endpoint, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    floor_data = data[0]
                    if floor_data.get('success') and 'floor' in floor_data:
                        floor_price = float(floor_data['floor'])
                        self.logger.debug(f"Retrieved floor price: {floor_price} HBAR")
                        return floor_price
                elif isinstance(data, dict) and data.get('success') and 'floor' in data:
                    # Handle single object response format
                    floor_price = float(data['floor'])
                    self.logger.debug(f"Retrieved floor price: {floor_price} HBAR")
                    return floor_price
                        
                self.logger.warning(f"No floor price data found: {data}")
                return None
            else:
                self.logger.error(f"Failed to get floor price: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching floor price: {str(e)}")
            return None

    def get_collection_info(self, collection_id: str) -> Optional[Dict]:
        """
        Get general information about a collection
        
        Args:
            collection_id: The Hedera collection ID
            
        Returns:
            Collection info dictionary or None if error
        """
        try:
            endpoint = f"{self.base_url}/collections/{collection_id}"
            
            response = self._make_request('GET', endpoint)
            
            if response and response.status_code == 200:
                data = response.json()
                collection_info = data.get('data', data) if isinstance(data, dict) else data
                self.logger.debug(f"Retrieved collection info for {collection_id}")
                return collection_info
            else:
                self.logger.error(f"Failed to get collection info: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching collection info: {str(e)}")
            return None
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with enhanced retry logic and better error handling
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object or None if failed
        """
        config = Config()
        
        for attempt in range(config.API_RETRY_ATTEMPTS):
            try:
                self.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1}/{config.API_RETRY_ATTEMPTS})")
                
                # Increase timeout for better reliability
                response = self.session.request(method, url, timeout=45, **kwargs)
                
                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                if response.status_code >= 500:  # Server error, retry
                    self.logger.warning(f"Server error {response.status_code}, retrying...")
                    if attempt < config.API_RETRY_ATTEMPTS - 1:
                        time.sleep(config.API_RETRY_DELAY * (attempt + 1))  # Exponential backoff
                        continue
                
                self.logger.debug(f"Request successful: {response.status_code}")
                return response
                
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"Request timeout on attempt {attempt + 1}: {str(e)}")
                if attempt < config.API_RETRY_ATTEMPTS - 1:
                    time.sleep(config.API_RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    continue
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < config.API_RETRY_ATTEMPTS - 1:
                    time.sleep(config.API_RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    continue
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt < config.API_RETRY_ATTEMPTS - 1:
                    time.sleep(config.API_RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    continue
        
        self.logger.error(f"All {config.API_RETRY_ATTEMPTS} request attempts failed for {url}")
        return None
