import requests
from bs4 import BeautifulSoup


def scrape_url(url: str) -> dict:
    """URLのコンテンツを取得してテキストとタイトルを返す"""
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

    return {"url": url, "title": title, "content": content}
