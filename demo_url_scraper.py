#!/usr/bin/env python3
"""
Demo script showing how to use COS scraper with JSON URLs
"""

import asyncio
from cos_scraper import COSScraper

async def demo_url_scraping():
    """Demo of URL-based scraping"""

    # Your Supabase credentials
    SUPABASE_URL = "https://yqawmzggcgpeyaaynrjk.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxYXdtemdnY2dwZXlhYXlucmprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTAxMDkyNiwiZXhwIjoyMDcwNTg2OTI2fQ.XtLpxausFriraFJeX27ZzsdQsFv3uQKXBBggoz6P4D4"

    # Initialize scraper
    scraper = COSScraper(SUPABASE_URL, SUPABASE_KEY)

    print("🔥 COS URL Scraper Demo")
    print("=" * 50)

    # Example: Paste your JSON URL here
    # Get this by:
    # 1. Go to https://www.cos.com/en-eu/men/view-all
    # 2. Press F12 → Network tab
    # 3. Scroll to load products
    # 4. Find the JSON API call and copy its URL

    json_url = "https://your-captured-json-url-here"  # <-- PASTE YOUR URL HERE

    if json_url == "https://your-captured-json-url-here":
        print("❌ Please replace the json_url with your actual captured URL!")
        print("\nHow to get the URL:")
        print("1. Go to https://www.cos.com/en-eu/men/view-all")
        print("2. Press F12 → Network tab")
        print("3. Scroll down to load products")
        print("4. Find the JSON request (look for 'items' in response)")
        print("5. Right-click → Copy → Copy link address")
        print("6. Paste it above and run again!")
        return

    print(f"📡 Fetching from: {json_url}")

    try:
        # Scrape with limit for testing
        results = await scraper.scrape_from_json_url(json_url, limit=5)

        print("✅ Success!")
        print(f"Results: {results}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(demo_url_scraping())
