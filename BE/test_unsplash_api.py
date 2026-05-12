"""
Test file for Unsplash API integration
This demonstrates how to search for photos using the Unsplash API
"""

import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Unsplash API configuration
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
UNSPLASH_API_URL = "https://api.unsplash.com"

def search_photos(query, per_page=10, orientation=None, color=None):
    """
    Search for photos on Unsplash

    Args:
        query (str): Search query keyword
        per_page (int): Number of results per page (default: 10)
        orientation (str): Filter by orientation (landscape, portrait, squarish)
        color (str): Filter by color (black_and_white, black, white, yellow, orange, red, purple, magenta, green, teal, blue)

    Returns:
        dict: JSON response from Unsplash API
    """
    if not UNSPLASH_ACCESS_KEY:
        raise ValueError("UNSPLASH_ACCESS_KEY not found in environment variables")

    url = f"{UNSPLASH_API_URL}/search/photos"

    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }

    params = {
        "query": query,
        "per_page": per_page,
        "page": 1
    }

    # Add optional parameters
    if orientation:
        params["orientation"] = orientation
    if color:
        params["color"] = color

    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error searching photos: {e}")
        return None

def get_photo(photo_id):
    """
    Get a single photo by ID

    Args:
        photo_id (str): The ID of the photo

    Returns:
        dict: JSON response from Unsplash API
    """
    if not UNSPLASH_ACCESS_KEY:
        raise ValueError("UNSPLASH_ACCESS_KEY not found in environment variables")

    url = f"{UNSPLASH_API_URL}/photos/{photo_id}"

    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }

    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error getting photo: {e}")
        return None

def get_random_photo(query=None):
    """
    Get a random photo

    Args:
        query (str): Optional query to filter random photos

    Returns:
        dict: JSON response from Unsplash API
    """
    if not UNSPLASH_ACCESS_KEY:
        raise ValueError("UNSPLASH_ACCESS_KEY not found in environment variables")

    url = f"{UNSPLASH_API_URL}/photos/random"

    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }

    params = {}
    if query:
        params["query"] = query

    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error getting random photo: {e}")
        return None

def print_photo_info(photo):
    """Print photo information in a readable format"""
    if not photo:
        return
    
    print(f"\n{'='*60}")
    print(f"Photo ID: {photo.get('id')}")
    print(f"Description: {photo.get('description', 'No description')}")
    print(f"Photographer: {photo.get('user', {}).get('name', 'Unknown')}")
    print(f"Photographer Username: @{photo.get('user', {}).get('username', 'unknown')}")
    print(f"Dimensions: {photo.get('width')} x {photo.get('height')}")
    print(f"Created at: {photo.get('created_at')}")
    print(f"\nImage URLs:")
    urls = photo.get('urls', {})
    print(f"  Raw: {urls.get('raw')}")
    print(f"  Full: {urls.get('full')}")
    print(f"  Regular: {urls.get('regular')}")
    print(f"  Small: {urls.get('small')}")
    print(f"  Thumb: {urls.get('thumb')}")
    print(f"\nDownload Link: {photo.get('links', {}).get('download')}")
    print(f"{'='*60}\n")

def test_search_photos():
    """Test searching for photos"""
    print("Testing photo search...")
    
    # Test 1: Basic search
    print("\n1. Basic search for 'technology':")
    results = search_photos("technology", per_page=3)
    if results and "results" in results:
        print(f"Found {results.get('total')} photos")
        for photo in results["results"]:
            print_photo_info(photo)
    
    # Test 2: Search with orientation
    print("\n2. Search for 'nature' with landscape orientation:")
    results = search_photos("nature", per_page=2, orientation="landscape")
    if results and "results" in results:
        for photo in results["results"]:
            print_photo_info(photo)
    
    # Test 3: Search with color filter
    print("\n3. Search for 'sunset' with blue color:")
    results = search_photos("sunset", per_page=2, color="blue")
    if results and "results" in results:
        for photo in results["results"]:
            print_photo_info(photo)

def test_get_photo():
    """Test getting a specific photo"""
    print("\nTesting get photo by ID...")
    
    # First get a photo from search
    search_results = search_photos("office", per_page=1)
    if search_results and "results" in search_results and len(search_results["results"]) > 0:
        photo_id = search_results["results"][0]["id"]
        print(f"\nGetting photo with ID: {photo_id}")
        photo = get_photo(photo_id)
        print_photo_info(photo)

def test_random_photo():
    """Test getting a random photo"""
    print("\nTesting random photo...")
    
    print("\n1. Random photo:")
    photo = get_random_photo()
    print_photo_info(photo)
    
    print("\n2. Random photo with query 'mountains':")
    photo = get_random_photo("mountains")
    print_photo_info(photo)

if __name__ == "__main__":
    print("Unsplash API Test Suite")
    print("=" * 60)
    
    # Check if access key is set
    if not UNSPLASH_ACCESS_KEY:
        print("ERROR: UNSPLASH_ACCESS_KEY not found in environment variables")
        print("Please add your Unsplash Access Key to your .env file:")
        print("UNSPLASH_ACCESS_KEY=your_access_key_here")
        exit(1)
    
    print(f"Using Access Key: {UNSPLASH_ACCESS_KEY[:20]}...")
    
    # Run tests
    try:
        test_search_photos()
        test_get_photo()
        test_random_photo()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {e}")
        exit(1)
