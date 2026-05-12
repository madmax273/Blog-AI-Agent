"""
Unsplash API utility module for image search and retrieval
"""

import os
import random
import httpx
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
UNSPLASH_API_URL = "https://api.unsplash.com"


class UnsplashClient:
    """Client for interacting with Unsplash API"""

    def __init__(self, access_key: Optional[str] = None):
        """
        Initialize Unsplash client

        Args:
            access_key: Unsplash API access key. If not provided, will use from environment
        """
        self.access_key = access_key or UNSPLASH_ACCESS_KEY
        if not self.access_key:
            raise ValueError("Unsplash access key not provided and not found in environment")

    def search_photo(self, query: str, orientation: Optional[str] = None, page: int = 1, per_page: int = 5) -> Optional[Dict]:
        """
        Search for a single photo based on query

        Args:
            query: Search query keyword
            orientation: Optional orientation filter (landscape, portrait, squarish)
            page: Page number for pagination (use different pages for variety)
            per_page: Number of results to fetch (pick randomly from these)

        Returns:
            Photo object dict or None if error
        """
        url = f"{UNSPLASH_API_URL}/search/photos"

        headers = {
            "Authorization": f"Client-ID {self.access_key}"
        }

        params = {
            "query": query,
            "per_page": per_page,
            "page": page
        }

        if orientation:
            params["orientation"] = orientation

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                # Return a random photo from results for variety
                results = data.get("results", [])
                if results:
                    return random.choice(results)
                return None
        except httpx.HTTPError as e:
            print(f"Error searching photo: {e}")
            return None

    def get_photo_urls(self, photo: Dict, size: str = "regular") -> Dict[str, str]:
        """
        Extract relevant URLs from photo object

        Args:
            photo: Photo object from Unsplash API
            size: Preferred image size (raw, full, regular, small, thumb)

        Returns:
            Dict with image URLs and metadata
        """
        urls = photo.get("urls", {})
        links = photo.get("links", {})
        user = photo.get("user", {})

        return {
            "image_url": urls.get(size, urls.get("regular")),
            "download_url": links.get("download"),
            "photographer": user.get("name", "Unknown"),
            "photographer_url": f"https://unsplash.com/@{user.get('username', '')}",
            "photo_url": f"https://unsplash.com/photos/{photo.get('id', '')}",
            "alt_text": photo.get("description") or photo.get("alt_description", "")
        }

    def search_and_get_image(self, query: str, orientation: Optional[str] = None, size: str = "regular", page: int = 1) -> Optional[Dict]:
        """
        Search for a photo and return formatted image data

        Args:
            query: Search query keyword
            orientation: Optional orientation filter
            size: Preferred image size
            page: Page offset for variety across multiple calls

        Returns:
            Dict with image URLs and metadata or None if error
        """
        photo = self.search_photo(query, orientation, page=page, per_page=5)
        if photo:
            return self.get_photo_urls(photo, size)
        return None


# Singleton instance for reuse
_unsplash_client = None


def get_unsplash_client() -> UnsplashClient:
    """Get or create singleton Unsplash client instance"""
    global _unsplash_client
    if _unsplash_client is None:
        _unsplash_client = UnsplashClient()
    return _unsplash_client
