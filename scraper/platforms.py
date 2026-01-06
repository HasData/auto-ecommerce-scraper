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
