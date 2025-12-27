#!/usr/bin/env python3
"""
COS EU Fashion Store Scraper
Scrapes all products, generates image embeddings, and imports to Supabase
"""

import json
import asyncio
import aiohttp
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from urllib.parse import urljoin

# Third-party imports
import torch
from transformers import AutoProcessor, AutoModel
from PIL import Image
import requests
from io import BytesIO
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProductData:
    """Structured product data matching Supabase schema"""
    id: str
    product_url: str
    image_url: str
    title: str
    gender: str  # "MAN" or "WOMAN"
    price: float
    currency: str
    source: str = "scraper"
    affiliate_url: Optional[str] = None
    brand: str = "COS"
    description: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[str] = None
    size: Optional[str] = None
    second_hand: bool = False
    embedding: Optional[List[float]] = None
    country: str = "EU"
    compressed_image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class COSEmbeddingGenerator:
    """Generate 768-dim embeddings using google/siglip-base-patch16-384"""

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Load model and processor - exactly Siglip as requested
        self.processor = AutoProcessor.from_pretrained("google/siglip-base-patch16-384")
        self.model = AutoModel.from_pretrained("google/siglip-base-patch16-384")
        self.model.to(self.device)
        self.model.eval()

    def generate_embedding(self, image_url: str) -> Optional[List[float]]:
        """Generate embedding from image URL using Siglip model"""
        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            # Open image
            image = Image.open(BytesIO(response.content)).convert("RGB")

            # Process image with dummy text (SigLIP requires both image and text)
            inputs = self.processor(
                images=image,
                text=["a photo of a fashion item"],  # Dummy text input
                return_tensors="pt",
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate embedding
            with torch.no_grad():
                outputs = self.model(**inputs)
                # For SigLIP, use the image embeddings (vision outputs)
                embedding = outputs.image_embeds.squeeze().cpu().numpy()

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to generate embedding for {image_url}: {e}")
            return None

class COSDataProcessor:
    """Process COS JSON data into structured ProductData"""

    def __init__(self):
        self.embedding_generator = COSEmbeddingGenerator()

    def process_product(self, product_json: Dict[str, Any]) -> Optional[ProductData]:
        """Process a single product from COS JSON"""
        try:
            # Extract basic info
            product_id = product_json.get("id", "")
            if not product_id:
                return None

            # Build product URL
            uri = product_json.get("uri", "")
            product_url = f"https://www.cos.com/en-eu/{uri}" if uri else ""

            # Get primary image
            primary_image = product_json.get("primaryImage", {})
            image_url = primary_image.get("src", "")

            if not image_url:
                # Fallback to first image in images array
                images = product_json.get("images", [])
                if images:
                    image_url = images[0].get("src", "")

            if not image_url:
                logger.warning(f"No image found for product {product_id}")
                return None

            # Extract title
            title = product_json.get("name", "").strip()
            if not title:
                return None

            # Determine gender
            categories = product_json.get("categories", [])
            gender = "WOMAN"  # default
            if any("men" in cat.lower() for cat in categories):
                gender = "MAN"

            # Extract price
            price_str = product_json.get("price", "").replace("€", "").replace(",", ".").strip()
            try:
                price = float(price_str)
            except (ValueError, TypeError):
                price = 0.0

            # Extract category (simplified)
            category = None
            category_uri = product_json.get("categoryUri", "")
            if "/" in category_uri:
                category = category_uri.split("/")[-1].replace("-", " ").title()

            # Create metadata JSON
            metadata = {
                "centra_product_id": product_json.get("centraProductId"),
                "sku": product_json.get("sku"),
                "product_sku": product_json.get("product_sku"),
                "variants_count": product_json.get("variantsCount"),
                "is_new": product_json.get("isNew", False),
                "is_on_sale": product_json.get("isOnSale", False),
                "categories": categories,
                "sustainability_composition": product_json.get("sustainabilityComposition", []),
                "all_images": [img.get("src") for img in product_json.get("images", []) if img.get("src")]
            }

            # Generate embedding
            logger.info(f"Generating embedding for product {product_id}: {title}")
            embedding = self.embedding_generator.generate_embedding(image_url)

            # Create tags from categories (simplified)
            tags = []
            for cat in categories:
                if "cashmere" in cat.lower():
                    tags.append("cashmere")
                elif "wool" in cat.lower():
                    tags.append("wool")
                elif "cotton" in cat.lower():
                    tags.append("cotton")

            return ProductData(
                id=f"cos_{product_id}",
                product_url=product_url,
                image_url=image_url,
                title=title,
                gender=gender,
                price=price,
                currency="EUR",
                category=category,
                metadata=json.dumps(metadata),
                embedding=embedding,
                tags=tags if tags else None
            )

        except Exception as e:
            logger.error(f"Failed to process product {product_json.get('id', 'unknown')}: {e}")
            return None

    def process_json_response(self, json_data: Dict[str, Any]) -> List[ProductData]:
        """Process complete JSON response with products"""
        products = []

        # Extract items array
        items = json_data.get("items", [])
        logger.info(f"Processing {len(items)} products from JSON")

        for item in items:
            product = self.process_product(item)
            if product:
                products.append(product)

        return products

class SupabaseImporter:
    """Import products to Supabase database"""

    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    def import_products(self, products: List[ProductData]) -> Dict[str, int]:
        """Import products to Supabase with upsert logic"""
        results = {"inserted": 0, "updated": 0, "errors": 0}

        for product in products:
            try:
                # Convert to dict for Supabase
                product_dict = {
                    "id": product.id,
                    "source": product.source,
                    "product_url": product.product_url,
                    "affiliate_url": product.affiliate_url,
                    "image_url": product.image_url,
                    "brand": product.brand,
                    "title": product.title,
                    "description": product.description,
                    "category": product.category,
                    "gender": product.gender,
                    "price": product.price,
                    "currency": product.currency,
                    "metadata": product.metadata,
                    "size": product.size,
                    "second_hand": product.second_hand,
                    "embedding": product.embedding,
                    "country": product.country,
                    "compressed_image_url": product.compressed_image_url,
                    "tags": product.tags,
                    "created_at": datetime.utcnow().isoformat()
                }

                # Upsert using the unique constraint on (source, product_url)
                response = self.client.table("products").upsert(
                    product_dict,
                    on_conflict="source,product_url"
                ).execute()

                if response.data:
                    results["inserted"] += 1
                    logger.info(f"Inserted/Updated product: {product.title}")
                else:
                    results["errors"] += 1
                    logger.error(f"Failed to insert product: {product.title}")

            except Exception as e:
                results["errors"] += 1
                logger.error(f"Error importing product {product.id}: {e}")

        return results

class COSScraper:
    """Main scraper class"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.processor = COSDataProcessor()
        self.importer = SupabaseImporter(supabase_url, supabase_key)

    def load_json_from_file(self, file_path: str) -> Dict[str, Any]:
        """Load JSON data from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def scrape_from_json_file(self, json_file_path: str, limit: Optional[int] = None) -> Dict[str, int]:
        """Scrape products from JSON file and import to Supabase"""
        logger.info(f"Loading products from file: {json_file_path}")

        # Load JSON data
        json_data = self.load_json_from_file(json_file_path)

        # Process products
        products = self.processor.process_json_response(json_data)

        if limit:
            products = products[:limit]
            logger.info(f"Limited to first {limit} products for testing")

        logger.info(f"Processed {len(products)} products successfully")

        # Import to Supabase
        results = self.importer.import_products(products)

        return results

    async def scrape_from_json_url(self, json_url: str, limit: Optional[int] = None) -> Dict[str, int]:
        """Scrape products from JSON URL and import to Supabase"""
        logger.info(f"Fetching products from URL: {json_url}")

        # Fetch JSON data from URL
        json_data = await self.fetch_json_from_url(json_url)

        # Process products
        products = self.processor.process_json_response(json_data)

        if limit:
            products = products[:limit]
            logger.info(f"Limited to first {limit} products for testing")

        logger.info(f"Processed {len(products)} products successfully")

        # Import to Supabase
        results = self.importer.import_products(products)

        return results

    async def fetch_json_from_url(self, url: str) -> Dict[str, Any]:
        """Fetch JSON data from URL with proper headers to mimic browser requests"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    json_data = await response.json()
                    return json_data

            except Exception as e:
                logger.error(f"Failed to fetch JSON from {url}: {e}")
                raise

    async def scrape_from_api(self, api_url: str) -> Dict[str, int]:
        """Scrape products from API endpoint"""
        logger.info(f"Fetching products from {api_url}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(api_url) as response:
                    response.raise_for_status()
                    json_data = await response.json()

                    # Process products
                    products = self.processor.process_json_response(json_data)

                    logger.info(f"Processed {len(products)} products successfully")

                    # Import to Supabase
                    results = self.importer.import_products(products)

                    return results

            except Exception as e:
                logger.error(f"Failed to fetch from API: {e}")
                return {"inserted": 0, "updated": 0, "errors": 1}

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json not found. Creating default config...")
        default_config = {
            "urls": ["PASTE_YOUR_JSON_URLS_HERE"],
            "limit": None,
            "run_on_push": True
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        print("Created config.json. Please edit it with your URLs.")
        return default_config
    except json.JSONDecodeError:
        print("ERROR: Invalid config.json format")
        return None

def main():
    """Main execution function"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="COS EU Fashion Scraper")
    parser.add_argument("--limit", type=int, help="Limit number of products to process (for testing)")
    parser.add_argument("--json-file", help="JSON file to process (local file)")
    parser.add_argument("--json-url", help="JSON URL to fetch and process")
    parser.add_argument("--config", action="store_true", help="Use config.json for URLs")

    args = parser.parse_args()

    # Configuration
    SUPABASE_URL = "https://yqawmzggcgpeyaaynrjk.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxYXdtemdnY2dwZXlhYXlucmprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTAxMDkyNiwiZXhwIjoyMDcwNTg2OTI2fQ.XtLpxausFriraFJeX27ZzsdQsFv3uQKXBBggoz6P4D4"

    # Initialize scraper
    scraper = COSScraper(SUPABASE_URL, SUPABASE_KEY)

    # Determine what to scrape
    urls_to_scrape = []
    files_to_scrape = []
    limit = args.limit

    if args.config or (not args.json_file and not args.json_url):
        # Load from config.json
        config = load_config()
        if not config:
            return

        urls_to_scrape = config.get("urls", [])
        files_to_scrape = config.get("files", [])
        if limit is None:
            limit = config.get("limit")

        # Filter out placeholder URLs and files
        urls_to_scrape = [url for url in urls_to_scrape if not url.startswith("PASTE_")]
        files_to_scrape = [file for file in files_to_scrape if not file.startswith("PASTE_")]

        if not urls_to_scrape and not files_to_scrape:
            print("No valid URLs or files found in config.json")
            print("Please edit config.json and add your JSON URLs or files")
            return

    elif args.json_url:
        urls_to_scrape = [args.json_url]
    elif args.json_file:
        files_to_scrape = [args.json_file]
    else:
        print("ERROR: You must provide either --json-file, --json-url, or use --config")
        print("\nUsage examples:")
        print("  python cos_scraper.py --config  # Use config.json")
        print("  python cos_scraper.py --json-file 1.txt")
        print("  python cos_scraper.py --json-url 'https://api.cos.com/products'")
        return

    logger.info("Starting COS scraper...")

    # Run the appropriate scraping method
    import asyncio

    async def run_scraper():
        total_results = {"inserted": 0, "updated": 0, "errors": 0}

        # Process files
        for file_path in files_to_scrape:
            logger.info(f"Processing file: {file_path}")
            try:
                results = scraper.scrape_from_json_file(file_path, limit)
                total_results["inserted"] += results["inserted"]
                total_results["updated"] += results["updated"]
                total_results["errors"] += results["errors"]
            except Exception as e:
                logger.error(f"Failed to process file {file_path}: {e}")
                total_results["errors"] += 1

        # Process URLs
        for i, url in enumerate(urls_to_scrape, 1):
            logger.info(f"Processing URL {i}/{len(urls_to_scrape)}: {url}")
            try:
                results = await scraper.scrape_from_json_url(url, limit)
                total_results["inserted"] += results["inserted"]
                total_results["updated"] += results["updated"]
                total_results["errors"] += results["errors"]
            except Exception as e:
                logger.error(f"Failed to process URL {url}: {e}")
                total_results["errors"] += 1

        logger.info("Scraping completed!")
        logger.info(f"Total Results: {total_results}")
        return total_results

    # Run async function
    results = asyncio.run(run_scraper())
    return results

if __name__ == "__main__":
    main()
