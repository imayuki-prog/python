"""
Webサイトをスクレイピングしてブログ生成に必要な情報を抽出する
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def analyze_website(url: str) -> dict:
    """URLをスクレイピングしてサイト情報を返す。"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"URLの取得に失敗しました ({url}): {e}")

    soup = BeautifulSoup(response.text, "html.parser")

    # ノイズ除去
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()

    # タイトル
    title = soup.title.string.strip() if soup.title else ""

    # メタディスクリプション
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "").strip()

    # OGP情報
    og_title = ""
    og_desc = ""
    og_tag = soup.find("meta", property="og:title")
    if og_tag:
        og_title = og_tag.get("content", "").strip()
    og_desc_tag = soup.find("meta", property="og:description")
    if og_desc_tag:
        og_desc = og_desc_tag.get("content", "").strip()

    # メインコンテンツ抽出
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=lambda c: c and any(k in str(c) for k in ["content", "main", "product"]))
        or soup.find("body")
    )
    raw_text = main.get_text(separator=" ", strip=True) if main else ""
    # 連続スペース・改行を正規化
    content = " ".join(raw_text.split())

    # 長すぎる場合は先頭8000字
    if len(content) > 8000:
        content = content[:8000] + "..."

    # 画像のalt属性（商品名ヒント）
    images = [img.get("alt", "").strip() for img in soup.find_all("img", alt=True)]
    images = [alt for alt in images if len(alt) > 3][:20]

    # 商品・価格情報の断片
    prices = [tag.get_text(strip=True) for tag in soup.find_all(class_=lambda c: c and "price" in str(c).lower())][:10]

    return {
        "url": url,
        "domain": urlparse(url).netloc,
        "title": og_title or title,
        "meta_description": og_desc or meta_desc,
        "content": content,
        "images": images,
        "prices": prices,
    }
