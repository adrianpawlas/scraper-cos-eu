# COS EU Fashion Store Scraper

A comprehensive scraper for COS EU that extracts product data, generates image embeddings, and imports everything to Supabase.

## Features

- ✅ **Complete Product Data Extraction**: Scrapes all product information including title, price, images, categories, gender, etc.
- ✅ **768-Dim Image Embeddings**: Uses `google/siglip-base-patch16-384` model for high-quality image embeddings
- ✅ **Supabase Integration**: Direct import to your Supabase database with upsert logic
- ✅ **Error Handling**: Robust error handling and logging
- ✅ **Configurable**: Command-line options for testing and customization

## Database Schema

The scraper imports data matching this Supabase table structure:

```sql
create table public.products (
  id text not null,
  source text null,  -- Set to "scraper"
  product_url text null,
  affiliate_url text null,
  image_url text not null,
  brand text null,  -- Set to "COS"
  title text not null,
  description text null,
  category text null,
  gender text null,  -- "MAN" or "WOMAN"
  price double precision null,
  currency text null,  -- "EUR"
  metadata text null,  -- JSON with detailed product info
  created_at timestamp with time zone null default now(),
  size text null,
  second_hand boolean null default false,  -- Set to FALSE
  embedding public.vector null,  -- 768-dim vector
  country text null,  -- Set to "EU"
  compressed_image_url text null,
  tags text[] null,
  constraint products_pkey primary key (id),
  constraint products_source_product_url_key unique (source, product_url)
)
```

## Installation

1. **Clone/Download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The scraper uses these default settings (configured in `cos_scraper.py`):

- **Supabase URL**: `https://yqawmzggcgpeyaaynrjk.supabase.co`
- **Supabase Key**: Your provided service role key
- **Default JSON file**: `1.txt` (your captured network data)

## Usage

### 🚀 Quick Start - GitHub Automation!

**Easiest way**: Just edit `config.json` and push to GitHub!

### 🎯 Automated GitHub Setup

1. **Edit `config.json`** - paste your JSON URLs there
2. **Push to GitHub** - the scraper runs automatically
3. **Daily updates** - runs every day at 2 AM UTC
4. **Manual runs** - use GitHub Actions tab

### 📝 Config File Setup

Edit `config.json`:
```json
{
  "urls": [
    "https://your-mens-json-url-here",
    "https://your-womens-json-url-here"
  ],
  "limit": null,
  "run_on_push": true
}
```

### Manual Usage Options

#### From Config File
```bash
python cos_scraper.py --config
# or simply:
python run_scraper.py
```

#### From Single URL
```bash
python cos_scraper.py --json-url "PASTE_YOUR_URL_HERE"
```

#### From Local JSON File
```bash
python cos_scraper.py --json-file your_data.json
```

#### Testing with Limited Products
```bash
python cos_scraper.py --json-url "https://your-captured-url" --limit 5
```

## 🎯 Getting JSON URLs from COS

### Step-by-Step Guide

1. **Open your browser** and go to a COS page:
   - Men: `https://www.cos.com/en-eu/men/view-all`
   - Women: `https://www.cos.com/en-eu/women/view-all`
   - Or any category page

2. **Open Developer Tools**:
   - Press `F12` or right-click → "Inspect"
   - Go to the **Network** tab

3. **Scroll the page** or interact to load products

4. **Find the JSON request**:
   - Look for requests to URLs containing `/api/` or JSON responses
   - Filter by "XHR" or "Fetch" in Network tab
   - Look for responses with product data (you'll see "items" array)

5. **Copy the URL**:
   - Right-click the request → "Copy" → "Copy link address"
   - This is your JSON URL!

6. **Paste it into the scraper**:
   ```bash
   python cos_scraper.py --json-url "https://your-copied-url-here"
   ```

### Example URLs

COS typically uses URLs like:
```
https://api.cos.com/en-eu/products/search?category=men&limit=100
https://search.cos.com/api/catalog/v1/en_GB/categories/.../products
```

### Alternative: Save as File

If you prefer to save the JSON locally:
1. Click the network request
2. Go to "Response" tab
3. Right-click → "Copy response"
4. Save to a `.json` file
5. Use: `python cos_scraper.py --json-file your_file.json`

## 🎯 Quick Commands

**For Men's Products:**
```bash
# Get the JSON URL from https://www.cos.com/en-eu/men/view-all
python cos_scraper.py --json-url "https://your-captured-url-here"
```

**For Women's Products:**
```bash
# Get the JSON URL from https://www.cos.com/en-eu/women/view-all
python cos_scraper.py --json-url "https://your-captured-url-here"
```

**Test with just 5 products:**
```bash
python cos_scraper.py --json-url "https://your-url-here" --limit 5
```

## 🔧 GitHub Setup

### 1. Add Secrets to Repository

Go to your GitHub repo → Settings → Secrets and variables → Actions:

Add these secrets:
- `SUPABASE_URL`: `https://yqawmzggcgpeyaaynrjk.supabase.co`
- `SUPABASE_KEY`: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxYXdtemdnY2dwZXlhYXlucmprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTAxMDkyNiwiZXhwIjoyMDcwNTg2OTI2fQ.XtLpxausFriraFJeX27ZzsdQsFv3uQKXBBggoz6P4D4`

### 2. Edit config.json

Replace the placeholder URLs with your actual COS JSON URLs:

```json
{
  "urls": [
    "https://your-actual-mens-json-url",
    "https://your-actual-womens-json-url"
  ],
  "limit": null,
  "run_on_push": true
}
```

### 3. Push to GitHub

The scraper will run automatically when you push changes to `config.json`!

## 📁 Files Included

- `config.json` - **EDIT THIS FILE** with your URLs
- `cos_scraper.py` - Main scraper
- `run_scraper.py` - Simple runner script
- `test_scraper.py` - Test all components
- `demo_url_scraper.py` - Demo of URL usage
- `requirements.txt` - Dependencies
- `.github/workflows/scrape.yml` - GitHub Actions automation
- `README.md` - This documentation
- `INSTRUCTIONS.txt` - Quick setup guide

## Output

The scraper will:
- ✅ Load and parse JSON product data
- ✅ Download product images and generate 768-dim embeddings
- ✅ Transform data to match your database schema
- ✅ Insert/update products in Supabase (upsert on `source, product_url`)
- ✅ Log progress and results

Example output:
```
INFO - Processing 25 products from JSON
INFO - Generating embedding for product 1333150003: SLIM RIBBED COTTON LONG-SLEEVED HENLEY T-SHIRT
INFO - Inserted/Updated product: SLIM RIBBED COTTON LONG-SLEEVED HENLEY T-SHIRT
INFO - Results: {'inserted': 25, 'updated': 0, 'errors': 0}
```

## Testing

Run the test suite to validate all components:
```bash
python test_scraper.py
```

This will test:
- ✅ Embedding generation
- ✅ Data processing
- ✅ Supabase connection

## Data Processing Details

### Product Fields Mapping

| COS JSON Field | Database Field | Processing |
|----------------|----------------|------------|
| `id` | `id` | Prefixed with `cos_` |
| `name` | `title` | Direct mapping |
| `price` | `price` | Converted to float |
| `primaryImage.src` | `image_url` | Direct mapping |
| Categories | `gender` | "MAN" if men's categories present |
| Categories | `category` | Simplified category name |
| All metadata | `metadata` | JSON string with full details |
| Generated | `embedding` | 768-dim vector from image |

### Automatic Values

- `source`: "scraper"
- `brand`: "COS"
- `currency`: "EUR"
- `country`: "EU"
- `second_hand`: `false`

### Image Embeddings

- **Model**: `google/siglip-base-patch16-384`
- **Dimensions**: 768
- **Input**: Product primary image
- **Processing**: RGB conversion, model inference

## Performance

- **Embedding Generation**: ~2-3 seconds per image (CPU)
- **Database Insert**: ~0.1-0.2 seconds per product
- **Total for 25 products**: ~1-2 minutes

## Error Handling

- **Network timeouts**: 10-second timeout for image downloads
- **Invalid data**: Graceful skipping of malformed products
- **Database errors**: Detailed logging with error counts
- **Embedding failures**: Continues processing other products

## Extending the Scraper

### Adding New Data Sources

1. **Capture new JSON**: Save network responses as JSON files
2. **Update file path**: Use `--json-file` parameter
3. **Test processing**: Run with `--limit 1` first

### Adding New Fields

1. **Update ProductData class**: Add new fields to the dataclass
2. **Update processing**: Modify `COSDataProcessor.process_product()`
3. **Update database**: Ensure Supabase table has the new columns

### API Integration

The scraper includes async methods for API integration:
```python
results = await scraper.scrape_from_api("https://api.cos.com/products")
```

## Troubleshooting

### Common Issues

1. **"Access Denied" on direct requests**: COS has bot protection - use captured JSON data
2. **Embedding generation fails**: Check internet connection for image downloads
3. **Supabase connection fails**: Verify URL and API key
4. **Unicode errors**: Ensure JSON files are UTF-8 encoded

### Logs

Check the console output for detailed logs including:
- Processing progress
- Embedding generation status
- Database operation results
- Error details

## Requirements

- Python 3.8+
- 4GB+ RAM (for model loading)
- Internet connection (for image downloads)
- Supabase account with pgvector extension

## Dependencies

- `torch`: Machine learning framework
- `transformers`: Hugging Face models
- `Pillow`: Image processing
- `requests`: HTTP client
- `supabase`: Database client
- `aiohttp`: Async HTTP (for future API integration)
