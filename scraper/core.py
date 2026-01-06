"""
Core scraping functionality with automatic platform detection.

This module provides the main AutoScraper class that handles:
- Page fetching (direct or via HasData API)
- Platform detection (WooCommerce, Shopify, Generic)
- Data extraction orchestration
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .platforms import scrape_woocommerce, scrape_shopify
from .utils import (
    find_repeating_containers,
    extract_data_from_containers,
    clean_and_group_data,
)


# Universal product schema for AI extraction
# This can be sent to HasData API for structured extraction
UNIVERSAL_PRODUCT_RULES = {
    "products": {
        "type": "list",
        "description": "list of all products on the page",
        "output": {
            "name": {
                "type": "string",
                "description": "product name or title",
            },
            "price": {
                "type": "string",
                "description": "current price",
            },
            "originalPrice": {
                "type": "string",
                "description": "original price before discount",
            },
            "currency": {
                "type": "string",
                "description": "currency symbol or code",
            },
            "url": {
                "type": "string",
                "description": "product page URL",
            },
            "image": {
                "type": "string",
                "description": "main product image URL",
            },
            "availability": {
                "type": "string",
                "description": "in stock, out of stock, or availability status",
            },
            "rating": {
                "type": "number",
                "description": "product rating (e.g., 4.5)",
            },
            "reviewCount": {
                "type": "number",
                "description": "number of reviews",
            },
            "brand": {
                "type": "string",
                "description": "brand or manufacturer name",
            },
            "category": {
                "type": "string",
                "description": "product category",
            },
            "description": {
                "type": "string",
                "description": "short product description",
            },
            "sku": {
                "type": "string",
                "description": "product SKU or ID",
            },
        },
    }
}


class AutoScraper:
    """
    Universal web scraper with automatic platform detection.
    
    Supports:
    - Direct HTTP requests
    - HasData API integration for JS rendering
    - Platform-specific scrapers (WooCommerce, Shopify)
    - Generic container-based extraction
    """
    
    def __init__(self, url, api_key=None, scrape_config=None):
        """
        Initialize the scraper.
        
        Args:
            url (str): Target URL to scrape
            api_key (str, optional): HasData API key for advanced features
            scrape_config (dict, optional): Configuration for HasData API
        """
        self.url = url
        self.api_key = api_key
        self.scrape_config = scrape_config or {}
        
        # Internal state
        self.soup = None                    # BeautifulSoup object
        self.raw_data = []                  # Unprocessed extracted data
        self.clean_data = []                # Cleaned and grouped data
        self.platform = None                # Detected platform
        self.hasdata_response = None        # Full HasData API response

    def fetch_page(self):
        """
        Fetch page content using appropriate method.
        
        Returns:
            BeautifulSoup: Parsed HTML content
        """
        if self.api_key:
            return self._fetch_with_hasdata()
        return self._fetch_with_requests()

    def _fetch_with_requests(self):
        """
        Fetch page using standard HTTP request.
        
        Returns:
            BeautifulSoup: Parsed HTML content
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }
        response = requests.get(self.url, headers=headers, timeout=10)
        response.raise_for_status()
        
        self.soup = BeautifulSoup(response.content, "html.parser")
        self.platform = self._detect_platform()
        return self.soup

    def _fetch_with_hasdata(self):
        """
        Fetch page using HasData API.
        
        Supports:
        - JavaScript rendering
        - Proxy rotation
        - Screenshot capture
        - Email/link extraction
        - AI-powered data extraction
        
        Returns:
            BeautifulSoup: Parsed HTML content
        """
        import json
        import requests

        api_url = "https://api.hasdata.com/scrape/web"
        
        # Build API payload
        payload = {
            "url": self.url,
            "jsRendering": self.scrape_config.get("jsRendering", True),
            "proxyType": self.scrape_config.get("proxyType", "datacenter"),
            "proxyCountry": self.scrape_config.get("proxyCountry", "US"),
            "blockResources": self.scrape_config.get("blockResources", True),
            "blockAds": self.scrape_config.get("blockAds", True),
            "screenshot": self.scrape_config.get("screenshot", False),
            "extractEmails": self.scrape_config.get("extractEmails", False),
            "extractLinks": self.scrape_config.get("extractLinks", False),
        }
        
        # Add AI extraction rules if provided
        if self.scrape_config.get("aiExtractRules"):
            payload["aiExtractRules"] = self.scrape_config["aiExtractRules"]

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        self.hasdata_response = response.json()

        # Parse HTML from API response
        html_content = self.hasdata_response.get("content", "")
        self.soup = BeautifulSoup(html_content, "html.parser")
        self.platform = self._detect_platform()
        return self.soup

    def get_hasdata_extras(self):
        """
        Get additional data from HasData API response.
        
        Returns:
            dict: Extra data including screenshots, emails, links, AI response
            None: If no HasData response available
        """
        if not self.hasdata_response:
            return None

        extras = {}
        for key in ("screenshot", "emails", "links", "aiResponse"):
            if key in self.hasdata_response:
                extras[key] = self.hasdata_response[key]
        return extras

    def _detect_platform(self):
        """
        Detect e-commerce platform from HTML content.
        
        Returns:
            str: Platform name ('woocommerce', 'shopify', or 'generic')
        """
        html_text = str(self.soup)
        
        # Check for WooCommerce indicators
        woo_indicators = [
            "woocommerce",
            "product_type_",
            "woocommerce-loop-product",
            "add_to_cart_button",
        ]
        if any(indicator in html_text for indicator in woo_indicators):
            return "woocommerce"

        # Check for Shopify indicators
        shopify_indicators = [
            "shopify",
            "product-card",
            "variant-",
            "Shopify.theme",
        ]
        if any(indicator in html_text for indicator in shopify_indicators):
            return "shopify"

        return "generic"

    def scrape(self, container_index=0, force_generic=False):
        """
        Main scraping method.
        
        Process:
        1. Fetch page content
        2. Try platform-specific scraper (if not forced to generic)
        3. Fall back to generic container detection
        4. Extract and clean data
        
        Args:
            container_index (int): Index of container group to extract
            force_generic (bool): Skip platform-specific scrapers
            
        Returns:
            dict: Scraping results with platform, candidates, and data
            None: If no repeating structures found
        """
        self.fetch_page()

        # Try platform-specific scrapers first
        if not force_generic:
            if self.platform == "woocommerce":
                result = scrape_woocommerce(self)
                if result:
                    return result
            elif self.platform == "shopify":
                result = scrape_shopify(self)
                if result:
                    return result

        # Fall back to generic container detection
        candidates = find_repeating_containers(self)
        if not candidates:
            return None

        # Validate container index
        if container_index >= len(candidates):
            container_index = 0

        # Extract data from selected container group
        selected = candidates[container_index]
        self.raw_data = extract_data_from_containers(self, selected["elements"])
        self.clean_data = clean_and_group_data(self)

        return {
            "platform": self.platform,
            "candidates": candidates,          # All found container groups
            "selected_index": container_index,  # Currently selected index
            "selected": selected,               # Selected container info
            "data": self.clean_data,           # Extracted data
        }