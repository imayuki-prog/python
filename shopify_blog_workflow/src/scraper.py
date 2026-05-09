import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# アイコン・ロゴ等を除外するキーワード
_EXCLUDE_KEYWORDS = ["logo", "icon", "banner", "sprite", "placeholder", "spacer", "pixel", "tracking"]

# 除外する拡張子
_EXCLUDE_EXTENSIONS = [".svg", ".gif", ".ico"]


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    """ページから商品・コンテンツ画像のURLリストを抽出する"""
    seen = set()
    images = []

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not src:
            continue

        # 絶対URLに変換
        abs_url = urljoin(base_url, src)

        # 重複除外
        if abs_url in seen:
            continue
        seen.add(abs_url)

        # 拡張子チェック
        path = urlparse(abs_url).path.lower()
        if any(path.endswith(ext) for ext in _EXCLUDE_EXTENSIONS):
            continue

        # ロゴ・アイコン系を除外
        combined = (abs_url + " " + (img.get("alt") or "") + " " + (img.get("class") or [""])[0]).lower()
        if any(kw in combined for kw in _EXCLUDE_KEYWORDS):
            continue

        images.append(abs_url)

    return images[:10]  # 最大10枚


def scrape_url(url: str) -> dict:
    """URLのコンテンツと画像を取得して返す"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 画像を先に抽出（不要タグ除去前）
    images = _extract_images(soup, url)

    # 不要なタグを除去
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else ""

    # メインコンテンツを取得（article > main > body の優先順位）
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find("body")
    )
    text = main.get_text(separator="\n", strip=True) if main else ""

    # 連続する空行を1行に圧縮
    lines = [line for line in text.splitlines() if line.strip()]
    content = "\n".join(lines)

    return {"url": url, "title": title, "content": content, "images": images}
