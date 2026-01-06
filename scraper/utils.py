"""
Utility functions for generic container detection and data extraction.

This module provides the intelligence for finding repeating product containers
on any website without prior knowledge of the structure.
"""

from collections import defaultdict, Counter
from urllib.parse import urljoin


def find_repeating_containers(scraper):
    """
    Find all repeating HTML structures that might be product containers.
    
    Algorithm:
    1. Group elements by CSS signature (tag + classes)
    2. Keep groups with 3+ elements
    3. Score each group by product-like characteristics
    4. Sort by score (best first)
    
    Args:
        scraper (AutoScraper): Scraper instance with loaded page
        
    Returns:
        list: Sorted list of candidate container groups with scores
    """
    soup = scraper.soup
    containers_by_signature = defaultdict(list)

    # Group elements by their CSS signature
    for element in soup.find_all(True):
        # Skip non-content elements
        if element.name in ["svg", "path", "script", "style", "br", "hr"]:
            continue
            
        classes = element.get("class", [])
        if classes:
            # Create signature: tag.class1.class2...
            signature = f"{element.name}.{'.'.join(sorted(classes))}"
            containers_by_signature[signature].append(element)

    # Score and filter candidates
    candidates = []
    for signature, elements in containers_by_signature.items():
        # Only consider groups with 3+ elements
        if len(elements) >= 3:
            score = _score_container_group(elements)
            if score > 0:
                candidates.append(
                    {
                        "signature": signature,     # CSS signature
                        "elements": elements,       # List of HTML elements
                        "count": len(elements),     # Number of elements
                        "score": score,             # Quality score
                    }
                )

    # Sort by score (best candidates first)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates


def _score_container_group(elements):
    """
    Score a group of elements for product container likelihood.
    
    Scoring factors:
    - Count (5-50 optimal, penalize 100+)
    - Has images (+200)
    - Has links (+150)
    - Text length (30-1000 chars optimal)
    - HTML complexity (15+ descendants good)
    - Product-related CSS classes (+200)
    - Anti-patterns (menu, nav, etc.) (-200)
    - Contains prices (+200)
    
    Args:
        elements (list): List of BeautifulSoup elements
        
    Returns:
        int: Score (0 = bad, higher = better)
    """
    tag = elements[0].name
    
    # Skip small inline elements
    if tag in ["span", "i", "button", "input"]:
        return 0

    score = 0
    count = len(elements)

    # Optimal count: 5-50 items
    if 5 <= count <= 50:
        score += 100
    elif count > 100:
        return 0  # Too many items, likely not products

    first = elements[0]
    
    # Images are strong product indicators
    has_images = len(first.find_all("img")) > 0
    if has_images:
        score += 200
    else:
        score -= 100

    # Links suggest clickable product cards
    has_links = len(first.find_all("a")) > 0
    if has_links:
        score += 150

    # Text length - products have descriptions
    text_length = len(first.get_text(strip=True))
    if 30 < text_length < 1000:
        score += 100
    elif text_length < 10:
        return 0  # Too short, likely not a product

    # HTML complexity - products have structured content
    complexity = len(list(first.descendants))
    if complexity > 15:
        score += 150
    elif complexity < 5:
        return 0  # Too simple

    # Check CSS classes for product-related keywords
    classes = " ".join(first.get("class", [])).lower()
    good_keywords = ["product", "item", "card", "article", "tile"]
    if any(kw in classes for kw in good_keywords):
        score += 200

    # Penalize UI elements
    bad_keywords = ["icon", "menu", "nav", "header", "footer", "button"]
    if any(kw in classes for kw in bad_keywords):
        score -= 200

    # Check for price indicators
    price_symbols = ["$", "€", "£", "₽"]
    sample = elements[: min(10, len(elements))]
    with_prices = sum(1 for el in sample if any(sym in el.get_text() for sym in price_symbols))
    if with_prices >= len(sample) * 0.5:  # 50%+ have prices
        score += 200

    return max(0, score)


def extract_data_from_containers(scraper, containers):
    """
    Extract data from each container element.
    
    Process:
    1. For each container, iterate through all child elements
    2. Extract leaf text nodes (no nested text)
    3. Handle links (extract URL + text)
    4. Handle images (extract src)
    5. Create CSS selector path for each field
    
    Args:
        scraper (AutoScraper): Scraper instance
        containers (list): List of container elements to process
        
    Returns:
        list: List of dictionaries with extracted data
    """
    raw_data = []

    for container in containers:
        row = {}
        
        # Process each element inside the container
        for element in container.find_all():
            text = element.get_text(strip=True)
            if not text:
                continue

            # Skip elements that have child elements with text
            # (we only want leaf nodes)
            has_text_children = any(
                child.get_text(strip=True) for child in element.find_all()
            )
            if has_text_children:
                continue

            # Create unique selector for this field
            selector = _create_selector(element)

            # Extract links with both text and URL
            if element.name == "a" and element.get("href"):
                row[selector] = {
                    "text": text,
                    "url": urljoin(scraper.url, element.get("href")),
                }
            # Extract image URLs
            elif element.name == "img" and element.get("src"):
                row[selector] = urljoin(scraper.url, element.get("src"))
            # Extract plain text
            else:
                row[selector] = text

        if row:
            raw_data.append(row)

    return raw_data


def _create_selector(element):
    """
    Create a simplified CSS selector path for an element.
    
    Creates a path like: "div.product > h2.title > a.link"
    Uses up to 3 levels of parent hierarchy.
    
    Args:
        element (BeautifulSoup element): HTML element
        
    Returns:
        str: CSS selector path
    """
    parts = []
    current = element
    
    # Go up 3 levels max
    for _ in range(3):
        if not current or current.name == "[document]":
            break
            
        classes = current.get("class", [])
        if classes:
            # Use first class for simplicity
            main_class = classes[0]
            parts.insert(0, f"{current.name}.{main_class}")
        else:
            parts.insert(0, current.name)
            
        current = current.parent
        
    return " > ".join(parts[-3:])


def clean_and_group_data(scraper):
    """
    Clean extracted data and create human-readable field names.
    
    Process:
    1. Analyze selector frequency across all rows
    2. Filter out low-frequency selectors (<30% coverage)
    3. Filter out selectors with no variation (same value everywhere)
    4. Create simple field names from selectors
    5. Handle duplicate names
    6. Separate link URLs into separate fields
    
    Args:
        scraper (AutoScraper): Scraper with raw_data
        
    Returns:
        list: Cleaned data with simple field names
    """
    raw_data = scraper.raw_data
    if not raw_data:
        return []

    # Count selector frequency and collect unique values
    selector_frequency = Counter()
    selector_values = defaultdict(set)

    for row in raw_data:
        for selector, value in row.items():
            selector_frequency[selector] += 1
            if isinstance(value, dict):
                selector_values[selector].add(value.get("text", ""))
            else:
                selector_values[selector].add(str(value))

    total_rows = len(raw_data)
    valid_selectors = {}

    # Filter selectors
    for selector, freq in selector_frequency.items():
        # Must appear in at least 30% of rows
        if freq < total_rows * 0.3:
            continue
        # Must have more than one unique value
        if len(selector_values[selector]) <= 1:
            continue
        valid_selectors[selector] = True

    # Create human-readable field names
    field_mapping = {}
    used_names = set()

    for selector in valid_selectors.keys():
        # Extract simple name from selector
        # "div.product > h2.title > a" -> "title"
        parts = selector.split(" > ")
        simple_name = parts[-1].replace(".", " ").strip()
        if " " in simple_name:
            simple_name = simple_name.split(" ", 1)[1]

        # Handle duplicate names
        original_name = simple_name
        counter = 1
        while simple_name in used_names:
            simple_name = f"{original_name}_{counter}"
            counter += 1

        field_mapping[selector] = simple_name
        used_names.add(simple_name)

    # Apply field mapping to all rows
    clean_data = []
    for row in raw_data:
        clean_row = {}
        for selector, new_name in field_mapping.items():
            if selector in row:
                value = row[selector]
                if isinstance(value, dict):
                    # Split links into text and URL fields
                    clean_row[new_name] = value.get("text", "")
                    clean_row[f"{new_name}_url"] = value.get("url", "")
                else:
                    clean_row[new_name] = value
        if clean_row:
            clean_data.append(clean_row)

    scraper.clean_data = clean_data
    return clean_data