import os
import re
import requests


def _markdown_to_html(text: str) -> str:
    """MarkdownをShopify用のHTMLに変換する"""
    lines = text.strip().splitlines()
    html_lines = []
    in_ul = False

    for line in lines:
        if line.startswith("# "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<h1>{line[2:].strip()}</h1>")
        elif line.startswith("## "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("### "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("- "):
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{line[2:].strip()}</li>")
        elif line.startswith("> "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<blockquote><p>{line[2:].strip()}</p></blockquote>")
        elif line.strip() == "---":
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append("<hr>")
        elif line.strip() == "":
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
        else:
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            # インライン装飾
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
            line = re.sub(r"_(.+?)_", r"<em>\1</em>", line)
            html_lines.append(f"<p>{line.strip()}</p>")

    if in_ul:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def publish_to_shopify(draft: dict, published: bool = False) -> dict:
    """ブログ草稿をShopifyに投稿する"""
    store = os.environ["SHOPIFY_STORE"]
    token = os.environ["SHOPIFY_ACCESS_TOKEN"]
    blog_id = os.environ["SHOPIFY_BLOG_ID"]

    body_html = _markdown_to_html(draft["full_text"])

    # 画像があればアイキャッチとして使用
    image_payload = {}
    if draft.get("images"):
        image_payload = {"image": {"src": draft["images"][0]}}

    article_data = {
        "article": {
            "title": draft["title"],
            "body_html": body_html,
            "published": published,
            "tags": "Japanese Craftsmanship, Made in Japan, Sustainability",
            **image_payload,
        }
    }

    response = requests.post(
        f"https://{store}/admin/api/2026-04/blogs/{blog_id}/articles.json",
        headers={
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        },
        json=article_data,
    )
    response.raise_for_status()

    article = response.json()["article"]
    article_url = f"https://{store}/blogs/our-journal/{article['handle']}"

    print(f"Shopify に投稿しました: {article_url}")
    return {"article_id": article["id"], "handle": article["handle"], "url": article_url}
