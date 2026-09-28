from urllib.parse import urljoin


def scrape_woocommerce(scraper):
    soup = scraper.soup
    url = scraper.url

    products = soup.find_all(
        "li",
        class_=lambda x: x and "product" in x and "type-product" in x,
    )
    if not products:
        products = soup.find_all("li", class_="product")
    if not products:
        return None

    scraper.raw_data = []

    for product in products:
        data = {}

        title_elem = product.find(
            ["h2", "h3"],
            class_=lambda x: x
            and "product" in str(x).lower()
            and "title" in str(x).lower(),
        )
        if not title_elem:
            title_elem = product.find(["h2", "h3"])
        if title_elem:
            data["title"] = title_elem.get_text(strip=True)

        link = product.find("a", class_="woocommerce-LoopProduct-link")
        if not link:
            link = product.find("a", href=True)
        if link:
            data["url"] = urljoin(url, link.get("href"))

        price_elem = product.find("span", class_="price")
        if price_elem:
            amount = price_elem.find("span", class_="woocommerce-Price-amount")
            if amount:
                data["price"] = amount.get_text(strip=True)
            else:
                data["price"] = price_elem.get_text(strip=True)

        img = product.find("img")
        if img:
            src = img.get("src") or img.get("data-src")
            if src:
                data["image"] = urljoin(url, src)
            alt = img.get("alt", "")
            if alt:
                data["image_alt"] = alt

        if "instock" in product.get("class", []):
            data["stock_status"] = "In Stock"
        elif "outofstock" in product.get("class", []):
            data["stock_status"] = "Out of Stock"

        classes = product.get("class", [])
        categories = [
            c.replace("product_cat-", "") for c in classes if c.startswith("product_cat-")
        ]
        if categories:
            data["categories"] = ", ".join(categories)

        tags = [
            c.replace("product_tag-", "") for c in classes if c.startswith("product_tag-")
        ]
        if tags:
            data["tags"] = ", ".join(tags)

        sku = product.get("data-product_sku") or product.find(
            attrs={"data-product_sku": True}
        )
        if sku:
            data["sku"] = sku if isinstance(sku, str) else sku.get("data-product_sku")

        rating = product.find("div", class_="star-rating")
        if rating:
            rating_text = rating.get("aria-label", "")
            if rating_text:
                data["rating"] = rating_text

        if data:
            scraper.raw_data.append(data)

    scraper.clean_data = scraper.raw_data
    return {
        "platform": "woocommerce",
        "count": len(products),
        "data": scraper.clean_data,
    }


def scrape_shopify(scraper):
    soup = scraper.soup
    url = scraper.url

    products = soup.find_all(
        ["div", "article"],
        class_=lambda x: x and "product-card" in str(x).lower(),
    )
    if not products:
        products = soup.find_all(["div", "article"], attrs={"data-product-id": True})
    if not products:
        return None

    scraper.raw_data = []

    for product in products:
        data = {}

        title = product.find(
            ["h2", "h3", "h4", "a"],
            class_=lambda x: x and "title" in str(x).lower(),
        )
        if title:
            data["title"] = title.get_text(strip=True)

        link = product.find("a", href=True)
        if link:
            data["url"] = urljoin(url, link.get("href"))

        price = product.find(
            ["span", "div"],
            class_=lambda x: x and "price" in str(x).lower(),
        )
        if price:
            data["price"] = price.get_text(strip=True)

        img = product.find("img")
        if img:
            src = img.get("src") or img.get("data-src")
            if src:
                data["image"] = urljoin(url, src)

        vendor = product.find(class_=lambda x: x and "vendor" in str(x).lower())
        if vendor:
            data["vendor"] = vendor.get_text(strip=True)

        if data:
            scraper.raw_data.append(data)

    scraper.clean_data = scraper.raw_data
    return {
        "platform": "shopify",
        "count": len(products),
        "data": scraper.clean_data,
    }


def scrape_shopify_products_json(scraper, limit=250, max_pages=8):
    """Pull the catalogue from the storefront's own /products.json.

    Every Shopify storefront serves it unless the merchant disabled it,
    and one request replaces the whole HTML-card parse. Returns None when
    the endpoint is missing or empty so the HTML route can take over.
    """
    import json
    from urllib.parse import urlsplit

    import requests

    parts = urlsplit(scraper.url)
    base = f"{parts.scheme}://{parts.netloc}"
    items = []
    for page in range(1, max_pages + 1):
        try:
            resp = requests.get(
                f"{base}/products.json",
                params={"limit": limit, "page": page},
                headers={"User-Agent": scraper.scrape_config.get("user_agent", "Mozilla/5.0")
                         if isinstance(getattr(scraper, "scrape_config", None), dict) else "Mozilla/5.0"},
                timeout=20,
            )
        except requests.RequestException:
            return None
        if resp.status_code != 200:
            return None
        try:
            batch = resp.json().get("products", [])
        except (ValueError, json.JSONDecodeError):
            return None
        if not batch:
            break
        for prod in batch:
            variant = (prod.get("variants") or [{}])[0]
            image = (prod.get("images") or [{}])[0]
            data = {
                "title": prod.get("title"),
                "url": f"{base}/products/{prod.get('handle')}" if prod.get("handle") else None,
                "price": variant.get("price"),
                "sku": variant.get("sku") or None,
                "vendor": prod.get("vendor") or None,
                "image": image.get("src") if isinstance(image, dict) else None,
                "available": variant.get("available"),
            }
            items.append({k: v for k, v in data.items() if v not in (None, "")})
        if len(batch) < limit:
            break
    if not items:
        return None

    scraper.raw_data = items
    scraper.clean_data = items
    return {
        "platform": "shopify",
        "source": "products.json",
        "count": len(items),
        "data": items,
    }


def scrape_microdata(scraper):
    """Extract schema.org Product microdata, the platform-agnostic route.

    Any theme that marks its cards with itemtype=schema.org/Product gets
    parsed here without a single site-specific selector. Returns None when
    the page carries no Product microdata.
    """
    soup = scraper.soup
    url = scraper.url

    cards = soup.find_all(attrs={"itemtype": lambda v: v and "schema.org/Product" in v})
    if not cards:
        return None

    scraper.raw_data = []
    for card in cards:
        data = {}

        name = card.find(attrs={"itemprop": "name"})
        if name:
            data["title"] = name.get("content") or name.get_text(strip=True)

        link = card.find(attrs={"itemprop": "url"}) or card.find("a", href=True)
        if link:
            href = link.get("href") or link.get("content")
            if href:
                data["url"] = urljoin(url, href)

        price = card.find(attrs={"itemprop": "price"})
        if price:
            data["price"] = price.get("content") or price.get_text(strip=True)

        currency = card.find(attrs={"itemprop": "priceCurrency"})
        if currency:
            data["currency"] = currency.get("content") or currency.get_text(strip=True)

        image = card.find(attrs={"itemprop": "image"})
        if image:
            src = image.get("src") or image.get("content")
            if src:
                data["image"] = urljoin(url, src)

        sku = card.find(attrs={"itemprop": "sku"})
        if sku:
            data["sku"] = sku.get("content") or sku.get_text(strip=True)

        if data:
            scraper.raw_data.append(data)

    if not scraper.raw_data:
        return None

    scraper.clean_data = scraper.raw_data
    return {
        "platform": "microdata",
        "count": len(scraper.raw_data),
        "data": scraper.clean_data,
    }
