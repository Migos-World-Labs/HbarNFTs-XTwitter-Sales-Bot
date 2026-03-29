"""
Image processing functionality for NFT images
"""

import requests
import os
import tempfile
import logging
from typing import Optional
from PIL import Image
from urllib.parse import urlparse
from config import Config

class ImageProcessor:
    """Handles downloading and processing of NFT images"""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NFT-Mint-Bot/1.0'
        })
    
    def download_and_process_image(self, image_url: str, token_id: str) -> Optional[str]:
        """
        Download and process an NFT image for Twitter
        
        Args:
            image_url: URL of the image to download
            token_id: Token ID for filename generation
            
        Returns:
            Path to processed image file or None if error
        """
        if not image_url:
            self.logger.warning("No image URL provided")
            return None
        
        try:
            # Download the image
            temp_path = self._download_image(image_url, token_id)
            if not temp_path:
                return None
            
            # Process the image
            processed_path = self._process_image(temp_path, token_id)
            
            # Clean up original if different from processed
            if temp_path != processed_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            
            return processed_path
            
        except Exception as e:
            self.logger.error(f"Error downloading/processing image for token {token_id}: {str(e)}")
            return None
    
    def _download_image(self, image_url: str, token_id: str) -> Optional[str]:
        """
        Download image from URL to temporary file with multiple IPFS gateway fallbacks
        
        Args:
            image_url: URL of the image
            token_id: Token ID for filename
            
        Returns:
            Path to downloaded file or None if error
        """
        # ── CUSTOMISATION TIP: IPFS gateways ─────────────────────────────────
        # The bot tries these gateways in order when fetching NFT images from IPFS.
        # If image downloads are slow or failing, try reordering these or adding
        # a dedicated gateway (e.g. your own Pinata gateway URL).
        # TIP: Put the fastest/most reliable gateway for your images first.
        ipfs_gateways = [
            'https://gateway.pinata.cloud/ipfs/',
            'https://cloudflare-ipfs.com/ipfs/',
            'https://ipfs.io/ipfs/',
            'https://dweb.link/ipfs/',
            'https://gateway.ipfs.io/ipfs/'
        ]
        # ─────────────────────────────────────────────────────────────────────
        
        # Prepare URLs to try
        urls_to_try = []
        if image_url.startswith('ipfs://'):
            ipfs_hash = image_url.replace('ipfs://', '')
            # Try multiple IPFS gateways
            for gateway in ipfs_gateways:
                urls_to_try.append(f"{gateway}{ipfs_hash}")
        else:
            # Direct URL
            urls_to_try.append(image_url)
        
        last_error = None
        
        for url in urls_to_try:
            try:
                self.logger.debug(f"Trying image URL: {url[:80]}...")
                response = self.session.get(url, timeout=10, stream=True)  # Shorter timeout per gateway
                response.raise_for_status()
                
                # Success! Process this response
                break
                
            except requests.exceptions.RequestException as e:
                last_error = e
                self.logger.debug(f"Gateway failed {url[:50]}: {str(e)[:100]}")
                continue
        else:
            # All gateways failed
            self.logger.error(f"All image gateways failed for token {token_id}. Last error: {str(last_error)}")
            return None
        
        try:
            # Get file extension from URL or response
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                extension = '.jpg'
            elif 'png' in content_type:
                extension = '.png'
            elif 'gif' in content_type:
                extension = '.gif'
            elif 'webp' in content_type:
                extension = '.webp'
            else:
                # Try to get extension from URL
                parsed_url = urlparse(image_url)
                path_extension = os.path.splitext(parsed_url.path)[1]
                extension = path_extension if path_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp'] else '.jpg'
            
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(
                suffix=f'_token_{token_id}{extension}',
                prefix='nft_image_',
                dir=self.config.TEMP_IMAGE_DIR
            )
            
            try:
                with os.fdopen(temp_fd, 'wb') as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                
                self.logger.debug(f"Downloaded image for token {token_id}: {temp_path}")
                return temp_path
                
            except Exception as e:
                # Clean up on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e
                
        except Exception as e:
            self.logger.error(f"Unexpected error downloading image: {str(e)}")
            return None
    
    def _process_image(self, image_path: str, token_id: str) -> Optional[str]:
        """
        Process image for Twitter compatibility
        
        Args:
            image_path: Path to source image
            token_id: Token ID for filename
            
        Returns:
            Path to processed image or None if error
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                if (img.width > self.config.MAX_IMAGE_SIZE[0] or 
                    img.height > self.config.MAX_IMAGE_SIZE[1]):
                    img.thumbnail(self.config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                    self.logger.debug(f"Resized image for token {token_id} to {img.size}")
                
                # Create output path
                output_fd, output_path = tempfile.mkstemp(
                    suffix=f'_token_{token_id}_processed.jpg',
                    prefix='nft_processed_',
                    dir=self.config.TEMP_IMAGE_DIR
                )
                os.close(output_fd)  # Close file descriptor
                
                # Save as JPEG
                img.save(output_path, 'JPEG', quality=self.config.IMAGE_QUALITY, optimize=True)
                
                self.logger.debug(f"Processed image for token {token_id}: {output_path}")
                return output_path
                
        except Exception as e:
            self.logger.error(f"Error processing image for token {token_id}: {str(e)}")
            return None
    
    def cleanup_image(self, image_path: str) -> bool:
        """
        Clean up temporary image file
        
        Args:
            image_path: Path to image file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(image_path):
                os.unlink(image_path)
                self.logger.debug(f"Cleaned up image file: {image_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error cleaning up image file {image_path}: {str(e)}")
            return False
    
    def validate_image_url(self, image_url: str) -> bool:
        """
        Validate if an image URL is accessible
        
        Args:
            image_url: URL to validate
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            # Handle IPFS URLs
            if image_url.startswith('ipfs://'):
                image_url = image_url.replace('ipfs://', 'https://ipfs.io/ipfs/')
            
            response = self.session.head(image_url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.debug(f"Image URL validation failed for {image_url}: {str(e)}")
            return False
