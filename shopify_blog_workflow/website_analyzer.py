import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional


@dataclass
class WebsiteData:
    url: str
    title: str
    description: str
    main_content: str
    products: list[str]
    brand_tone: str


def fetch_website(url: str) -> WebsiteData:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = _extract_title(soup)
    description = _extract_description(soup)
    main_content = _extract_main_content(soup)
    products = _extract_products(soup)
    brand_tone = _infer_brand_tone(soup)

    return WebsiteData(
        url=url,
        title=title,
        description=description,
        main_content=main_content[:3000],
        products=products[:10],
        brand_tone=brand_tone,
    )


def _extract_title(soup: BeautifulSoup) -> str:
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"]
    if soup.title:
        return soup.title.string or ""
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else "Unknown Brand"


def _extract_description(soup: BeautifulSoup) -> str:
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        return og_desc["content"]
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        return meta_desc["content"]
    return ""


def _extract_main_content(soup: BeautifulSoup) -> str:
    for selector in ["main", "article", "#content", ".content", ".main"]:
        element = soup.select_one(selector)
        if element:
            return element.get_text(separator=" ", strip=True)
    return soup.get_text(separator=" ", strip=True)


def _extract_products(soup: BeautifulSoup) -> list[str]:
    products = []
    for tag in soup.find_all(["h2", "h3", "h4"]):
        text = tag.get_text(strip=True)
        if text and len(text) < 100:
            products.append(text)
    return products


def _infer_brand_tone(soup: BeautifulSoup) -> str:
    text = soup.get_text(separator=" ", strip=True).lower()
    if any(w in text for w in ["luxury", "premium", "exclusive", "haute"]):
        return "luxury"
    if any(w in text for w in ["fun", "playful", "kids", "happy", "joy"]):
        return "playful"
    if any(w in text for w in ["organic", "natural", "eco", "sustainable", "green"]):
        return "eco-conscious"
    if any(w in text for w in ["professional", "enterprise", "business", "corporate"]):
        return "professional"
    return "friendly"
