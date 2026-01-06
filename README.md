![Python](https://img.shields.io/badge/python-3.11+-blue)
![HasData](https://img.shields.io/badge/powered%20by-HasData-orange)

# Auto E-commerce Scraper

[![HasData_bannner](media/banner.png)](https://hasdata.com/)

A universal web scraper for e-commerce sites with automatic platform detection and intelligent data extraction.

## Table of Contents

- [Auto E-commerce Scraper](#auto-e-commerce-scraper)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#-installation)
  - [Requirements](#requirements)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [With HasData API](#with-hasdata-api)
- [How It Works](#how-it-works)
  - [1. Platform Detection](#1-platform-detection)
  - [2. Container Detection (Generic Mode)](#2-container-detection-generic-mode)
  - [3. Data Extraction](#3-data-extraction)
  - [4. Data Cleaning](#4-data-cleaning)
- [API Reference](#api-reference)
  - [AutoScraper Class](#autoscraper-class)
  - [Platform-Specific Scrapers](#platform-specific-scrapers)
- [Examples](#examples)
  - [Scraping a WooCommerce Store](#scraping-a-woocommerce-store)
  - [Using AI Extraction](#using-ai-extraction)
- [Tested Sites](#tested-sites)
- [Configuration](#configuration)
  - [Scraping Options](#scraping-options)
  - [AI Extraction Rules](#ai-extraction-rules)
- [Links](#-links)
- [Disclaimer](#disclaimer)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)


## Features

![Demo](media/demo.png)

-  **Intelligent Container Detection** - Finds repeating product cards without configuration
-  **HasData API Integration** - Optional API support for JavaScript rendering and advanced features
-  **AI Extraction** - Extract structured product data using AI (via HasData)
-  **Multiple Export Formats** - Export to CSV, JSON, and Excel
-  **User-Friendly Interface** - Built with Streamlit for easy interaction

##  Architecture

```
.
├── app.py                  # Main application entry point
├── scraper/
│   ├── core.py            # AutoScraper class and main logic
│   ├── platforms.py       # Platform-specific scrapers (WooCommerce, Shopify)
│   └── utils.py           # Helper functions for container detection
└── ui/
    ├── layout.py          # Sidebar and results rendering
    └── export.py          # Data export functionality
```

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/hasdata/auto-ecommerce-scraper.git
cd auto-ecommerce-scraper

# Install dependencies
pip install -r requirements.txt
```

### Requirements

```txt
streamlit>=1.30.0
pandas>=2.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
openpyxl>=3.1.0
```

##  Usage

### Basic Usage

```bash
streamlit run app.py
```

Then:
1. Enter a product listing page URL
2. Click "Start Scraping"
3. Review extracted data
4. Export to your preferred format

### With HasData API

For JavaScript-heavy sites or AI extraction:

1. Check "Use HasData API"
2. Enter your API key
3. Configure scraping options:
   - JS Rendering
   - Proxy settings
   - AI product extraction
   - Screenshot capture
   - Email/link extraction

##  How It Works

### 1. Platform Detection

The scraper automatically identifies the platform:
- **WooCommerce** - Looks for `woocommerce`, `product_type_`, etc.
- **Shopify** - Detects `shopify`, `product-card`, etc.
- **Generic** - Falls back to container detection

### 2. Container Detection (Generic Mode)

Scores potential product containers based on:
- Presence of images and links
- Text content length
- HTML structure complexity
- CSS class keywords
- Price indicators

### 3. Data Extraction

Extracts:
- Product titles
- Prices and original prices
- Product URLs
- Images
- Stock status
- Categories and tags
- SKUs
- Ratings and reviews

### 4. Data Cleaning

- Groups similar fields
- Removes low-frequency selectors
- Creates human-readable field names
- Handles links and images properly

## API Reference

### AutoScraper Class

```python
from scraper.core import AutoScraper

# Initialize scraper
scraper = AutoScraper(
    url="https://example.com/products",
    api_key="your_hasdata_key",  # Optional
    scrape_config={
        "jsRendering": True,
        "proxyType": "datacenter",
        "blockAds": True
    }
)

# Scrape data
result = scraper.scrape(
    container_index=0,      # Select container group
    force_generic=False     # Force generic method
)

# Access results
print(result['platform'])   # 'woocommerce', 'shopify', or 'generic'
print(result['data'])       # List of extracted items
```

### Platform-Specific Scrapers

```python
from scraper.platforms import scrape_woocommerce, scrape_shopify

# For WooCommerce sites
result = scrape_woocommerce(scraper)

# For Shopify sites
result = scrape_shopify(scraper)
```

##  Examples

### Scraping a WooCommerce Store

```python
scraper = AutoScraper("https://scrapeme.live/shop/")
result = scraper.scrape()

# result will contain:
# {
#   'platform': 'woocommerce',
#   'count': 48,
#   'data': [
#     {
#       'title': 'Product Name',
#       'price': '$19.99',
#       'url': 'https://...',
#       'image': 'https://...',
#       'stock_status': 'In Stock'
#     },
#     ...
#   ]
# }
```

### Using AI Extraction

```python
from scraper.core import UNIVERSAL_PRODUCT_RULES

scraper = AutoScraper(
    url="https://example.com/products",
    api_key="your_key",
    scrape_config={
        "jsRendering": True,
        "aiExtractRules": UNIVERSAL_PRODUCT_RULES
    }
)

result = scraper.scrape()
ai_data = scraper.get_hasdata_extras()['aiResponse']
```

## Tested Sites

- ✅ WooCommerce stores
- ✅ Shopify stores
- ✅ Custom e-commerce platforms
- ✅ Book stores (books.toscrape.com)
- ✅ Fashion marketplaces (Vinted)
- ✅ And many more...

##  Configuration

### Scraping Options

| Option | Description | Default |
|--------|-------------|---------|
| `jsRendering` | Enable JavaScript rendering | `true` |
| `screenshot` | Capture page screenshot | `false` |
| `extractEmails` | Extract email addresses | `false` |
| `extractLinks` | Extract all links | `false` |
| `blockResources` | Block images/fonts/media | `true` |
| `blockAds` | Block advertisements | `true` |
| `proxyType` | Proxy type (datacenter/residential/mobile) | `datacenter` |
| `proxyCountry` | Proxy country code | `US` |

### AI Extraction Rules

Define custom extraction schemas:

```python
custom_rules = {
    "products": {
        "type": "list",
        "description": "all products",
        "output": {
            "name": {"type": "string"},
            "price": {"type": "string"},
            "rating": {"type": "number"}
        }
    }
}
```

## 🔗 Links

- [How to Scrape E-Commerce in 2026](https://hasdata.com/blog/web-scraping-in-e-commerce)
- [HasData API Documentation](https://docs.hasdata.com/introduction)
- [Streamlit Documentation](https://docs.streamlit.io)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## Disclaimer

This tool is for **educational purposes** only. Learn more about [the legality of web scraping](https://hasdata.com/blog/is-web-scraping-legal).

## Troubleshooting

### Common Issues

**"Could not find repeating structures"**
- Try checking "Use generic method"
- Ensure the page has multiple similar items
- Try with HasData API for JS-rendered content

**"API Error"**
- Verify your HasData API key
- Check your API quota
- Ensure the URL is accessible

**Empty or incomplete data**
- Select a different container group
- Enable JS rendering
- Check if the site requires authentication

---

Made with ❤️ for the web scraping community