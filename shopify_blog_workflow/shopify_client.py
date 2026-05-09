"""
Phase 2: Shopify Admin API でブログ記事を投稿する
"""
import requests
import os
from config import SHOPIFY_SHOP_URL, SHOPIFY_ADMIN_API_TOKEN


def post_to_shopify(blog: dict, image_url: str | None = None) -> str:
    """
    承認済みブログをShopifyに投稿し、記事URLを返す。

    事前準備:
    1. Shopify Admin → Settings → Apps and sales channels → Develop apps
    2. Custom app を作成し 'write_content' スコープを付与
    3. Admin API access token を取得して .env に設定
    """
    if not SHOPIFY_SHOP_URL or not SHOPIFY_ADMIN_API_TOKEN:
        raise EnvironmentError(
            "SHOPIFY_SHOP_URL と SHOPIFY_ADMIN_API_TOKEN を .env に設定してください"
        )

    # Shopify デフォルトブログのIDを取得
    blog_id = _get_default_blog_id()

    # Markdown → HTML 変換（簡易）
    html_content = _markdown_to_html(blog.get("content", ""))

    # 記事データ
    article_data = {
        "article": {
            "title": blog.get("title", ""),
            "body_html": html_content,
            "summary_html": blog.get("meta_description", ""),
            "tags": ", ".join(blog.get("tags", [])),
            "published": False,  # 下書きとして保存
        }
    }

    if image_url:
        article_data["article"]["image"] = {"src": image_url}

    url = f"https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/blogs/{blog_id}/articles.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_TOKEN,
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=article_data, headers=headers)
    response.raise_for_status()

    article = response.json()["article"]
    handle = article.get("handle", "")
    return f"https://{SHOPIFY_SHOP_URL}/blogs/news/{handle}"


def _get_default_blog_id() -> str:
    """ストアの最初のブログIDを取得する。"""
    url = f"https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/blogs.json"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ADMIN_API_TOKEN}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    blogs = response.json().get("blogs", [])
    if not blogs:
        raise RuntimeError("Shopifyにブログが見つかりません。管理画面でブログを作成してください。")
    return str(blogs[0]["id"])


def _markdown_to_html(markdown: str) -> str:
    """Markdownを簡易的にHTMLに変換する。"""
    lines = markdown.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        if line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:].strip()}</li>")
        elif line.strip() == "":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            # **bold** 変換
            text = line
            while "**" in text:
                text = text.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            html_lines.append(f"<p>{text}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)
