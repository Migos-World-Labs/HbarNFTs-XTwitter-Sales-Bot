"""
Twitter bot functionality for posting NFT sale and mint updates.

Authentication overview:
  - Public tweets: OAuth 1.0a (consumer key/secret + access token/secret)
  - Image uploads: Twitter API v1.1 via OAuth 1.0a (requires Elevated access)
"""

import tweepy
import logging
import time
from typing import Optional
from config import Config


class TwitterBot:
    """Twitter API client for posting NFT sale and mint updates"""

    def __init__(self, bearer_token: str, consumer_key: str, consumer_secret: str,
                 access_token: str, access_token_secret: str):
        self.config = Config()
        self.logger = logging.getLogger(__name__)

        try:
            # Initialize Twitter API v2 client (for posting tweets)
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True
            )

            # Initialize API v1.1 for media uploads (requires Elevated access)
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

            # Test authentication
            try:
                user = self.client.get_me()
                if user and hasattr(user, 'data') and user.data:
                    self.logger.info(f"Twitter authentication successful for user: {user.data.username}")
                else:
                    self.logger.warning("Authentication successful but user data unavailable")
            except Exception as e:
                self.logger.error(f"Twitter authentication failed: {str(e)}")
                raise

        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter client: {str(e)}")
            raise

    def post_sale_tweet(self, text: str, image_path: Optional[str] = None) -> bool:
        """
        Post a tweet about an NFT mint or sale.

        Args:
            text: Tweet text content
            image_path: Path to image file to attach (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            media_id = None

            if image_path:
                media_id = self._upload_image(image_path)
                if not media_id:
                    self.logger.warning("Failed to upload image, posting text-only tweet")

            if media_id:
                response = self.client.create_tweet(text=text, media_ids=[media_id])
            else:
                response = self.client.create_tweet(text=text)

            if response:
                tweet_id = 'unknown'
                if hasattr(response, 'data') and response.data:
                    if hasattr(response.data, 'id'):
                        tweet_id = response.data.id
                    elif isinstance(response.data, dict):
                        tweet_id = response.data.get('id', 'unknown')

                self.logger.info(f"Tweet posted successfully: {tweet_id}")

                # Rate limit protection between consecutive tweets
                time.sleep(self.config.TWITTER_RATE_LIMIT_DELAY)
                return True
            else:
                self.logger.error("Tweet posting failed - no response data")
                return False

        except tweepy.TooManyRequests:
            self.logger.error("Twitter rate limit exceeded")
            return False
        except tweepy.Forbidden as e:
            self.logger.error(f"Twitter API forbidden error (check app permissions): {str(e)}")
            return False
        except tweepy.BadRequest as e:
            self.logger.error(f"Twitter API bad request: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error posting tweet: {str(e)}")
            return False

    def _upload_image(self, image_path: str) -> Optional[str]:
        """
        Upload an image to Twitter using API v1.1.

        Requires Elevated access on your Twitter developer app.

        Args:
            image_path: Path to the local image file

        Returns:
            Media ID string if successful, None otherwise
        """
        try:
            media = self.api_v1.media_upload(filename=image_path)

            if media and media.media_id_string:
                self.logger.debug(f"Image uploaded successfully: {media.media_id_string}")
                return media.media_id_string
            else:
                self.logger.error("Media upload failed - no media ID returned")
                return None
        except tweepy.TooManyRequests:
            self.logger.error("Twitter media upload rate limit exceeded")
            return None
        except tweepy.Forbidden as e:
            self.logger.error(
                f"Media upload forbidden (check Elevated access is enabled on your app): {str(e)}"
            )
            return None
        except FileNotFoundError:
            self.logger.error(f"Image file not found: {image_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error uploading image: {str(e)}")
            return None

    def test_connection(self) -> bool:
        """
        Test that Twitter API credentials are working.

        Returns:
            True if the connection succeeds, False otherwise
        """
        try:
            user = self.client.get_me()
            if user and hasattr(user, 'data') and user.data:
                self.logger.info(f"Twitter connection test successful: @{user.data.username}")
                return True
            else:
                self.logger.error("Twitter connection test failed - no user data returned")
                return False
        except Exception as e:
            self.logger.error(f"Twitter connection test failed: {str(e)}")
            return False
