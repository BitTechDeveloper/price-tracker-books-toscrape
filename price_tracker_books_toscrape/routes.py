import re

from crawlee.crawlers import BeautifulSoupCrawlingContext
from crawlee.router import Router

router = Router[BeautifulSoupCrawlingContext]()


@router.default_handler
async def default_handler(context: BeautifulSoupCrawlingContext) -> None:
    """Default request handler."""
    context.log.info(f"Processing {context.request.url} ...")
    title = context.soup.find("title")
    data = {
        "url": context.request.loaded_url,
        "title": title.text if title else None,
    }
    # await context.push_data(data)

    # await context.enqueue_links(selector="li.next a")
    await context.enqueue_links(
        selector="article.product_pod h3 a", label="detail", limit=1
    )


# ... existing imports in routes.py ...


@router.handler(label="detail")
async def detail_handler(context: BeautifulSoupCrawlingContext) -> None:
    """Detail page handler: extracts product details with corrected types and description."""
    context.log.info(f"Processing detail page: {context.request.url}")
    context.log.info(f"Proxy: {context.proxy_info}")
    context.log.info(f"Session ID: {context.session.id}")

    soup = context.soup

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Price as float (e.g., "£51.77" -> 51.77)
    price_tag = soup.find("p", class_="price_color")
    price = None
    if price_tag:
        price_text = price_tag.get_text(strip=True)
        # Remove currency symbol and convert to float
        price = float(re.sub(r"[^\d.]", "", price_text))

    # Rating as int (e.g., "Three" -> 3)
    rating_map = {
        "Zero": 0,
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5,
    }
    rating_div = soup.find("p", class_=re.compile(r"^star-rating"))
    rating = None
    if rating_div:
        classes = rating_div.get("class", [])
        rating_str = next((c for c in classes if c in rating_map), None)
        if rating_str:
            rating = rating_map[rating_str]

    # Stock quantity as int
    availability_tag = soup.find("p", class_=re.compile(r"instock availability"))
    quantity = None
    if availability_tag:
        text = availability_tag.get_text(strip=True)
        match = re.search(r"\((\d+) available\)", text)
        if match:
            quantity = int(match.group(1))

    # Description (fixed: inside <div id="product_description">, next <p> after <h2>)
    description = None
    product_desc_div = soup.find("div", id="product_description")
    if product_desc_div:
        desc_p = product_desc_div.find_next_sibling("p")
        if desc_p:
            description = desc_p.get_text(strip=True)

    data = {
        "url": context.request.loaded_url or context.request.url,
        "title": title,
        "price": price,  # float or None
        "rating": rating,  # int 0-5 or None
        "stock_quantity": quantity,  # int or None
        "description": description,
    }
    context.log.info(data)

    await context.push_data(data)
