"""ドラフトを Shopify ブログ記事として投稿する"""
import json
import os
import re

import requests


def _inline_format(line: str) -> str:
    line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
    line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
    line = re.sub(r"_(.+?)_", r"<em>\1</em>", line)
    return line


def _build_faq_jsonld(text: str) -> str:
    """FAQセクションから schema.org FAQPage JSON-LD を生成する"""
    faq_match = re.search(r"## FAQ.*?\n(.*?)(?=\n## |\Z)", text, re.DOTALL | re.IGNORECASE)
    if not faq_match:
        return ""

    faq_text = faq_match.group(1)
    qa_pairs = re.findall(r"\*\*(.+?)\*\*\n(.+?)(?=\n\*\*|\Z)", faq_text, re.DOTALL)
    if not qa_pairs:
        return ""

    items = [
        {
            "@type": "Question",
            "name": q.strip(),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": re.sub(r"\*(.+?)\*", r"\1", a.strip()),
            },
        }
        for q, a in qa_pairs
    ]

    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items}
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'


def _markdown_to_html(text: str, images: list = None, image_alts: list = None) -> str:
    """Markdown を Shopify 用 HTML に変換し、H2 の後に画像を挿入する"""
    lines = text.strip().splitlines()
    html_lines = []
    in_ul = False
    image_iter = iter(images or [])
    alt_iter = iter(image_alts or [])
    h2_count = 0

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
            # 1つおきに画像を挿入（2番目のH2、4番目のH2…）
            if h2_count % 2 == 1:
                img_url = next(image_iter, None)
                if img_url:
                    alt = next(alt_iter, "")
                    html_lines.append(
                        f'<figure style="margin:1.5em 0;">'
                        f'<img src="{img_url}" alt="{alt}" loading="lazy" '
                        f'style="max-width:100%;height:auto;border-radius:8px;"></figure>'
                    )
            h2_count += 1

        elif line.startswith("### "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")

        elif line.startswith("- "):
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{_inline_format(line[2:].strip())}</li>")

        elif line.startswith("> "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<blockquote><p>{_inline_format(line[2:].strip())}</p></blockquote>")

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
            html_lines.append(f"<p>{_inline_format(line.strip())}</p>")

    if in_ul:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def publish_to_shopify(draft: dict, published: bool = True) -> dict:
    """ドラフトを Shopify に投稿する"""
    store = os.environ["SHOPIFY_STORE"]
    token = os.environ["SHOPIFY_ACCESS_TOKEN"]
    blog_id = os.environ["SHOPIFY_BLOG_ID"]

    seo = draft.get("seo") or {}
    image_alts = seo.get("image_alts") or []

    body_html = _markdown_to_html(
        draft["full_text"],
        images=draft.get("images", []),
        image_alts=image_alts,
    )

    # CTA ボタンを末尾に追加
    cta = draft.get("cta") or {}
    if cta.get("url") and cta.get("text"):
        body_html += (
            '\n<div style="text-align:center;margin:2.5em 0;">'
            f'<a href="{cta["url"]}" '
            f'style="display:inline-block;padding:14px 32px;background:#1a1a1a;color:#fff;'
            f'text-decoration:none;border-radius:4px;font-weight:600;letter-spacing:0.03em;">'
            f'{cta["text"]}</a></div>'
        )

    # FAQ JSON-LD を末尾に追加（GEO対応）
    faq_jsonld = _build_faq_jsonld(draft["full_text"])
    if faq_jsonld:
        body_html += "\n" + faq_jsonld

    article_data = {
        "article": {
            "title": draft["title"],
            "body_html": body_html,
            "published": published,
            "tags": "Japanese Craftsmanship, Made in Japan",
        }
    }

    # メタディスクリプション（summary_htmlとして設定）
    meta_desc = seo.get("meta_description", "")
    if meta_desc:
        article_data["article"]["summary_html"] = f"<p>{meta_desc}</p>"

    # 最初の画像をアイキャッチに設定
    if draft.get("images"):
        article_data["article"]["image"] = {
            "src": draft["images"][0],
            "alt": image_alts[0] if image_alts else draft["title"],
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
    blog_domain = os.environ.get("SHOPIFY_BLOG_DOMAIN") or store
    article_url = f"https://{blog_domain}/blogs/our-journal/{article['handle']}"
    print(f"Shopify に投稿しました: {article_url}")
    return {"article_id": article["id"], "handle": article["handle"], "url": article_url}


def _get_headers():
    return {
        "X-Shopify-Access-Token": os.environ["SHOPIFY_ACCESS_TOKEN"],
        "Content-Type": "application/json",
    }


def find_article_by_handle(handle: str):
    """ハンドルで Shopify 記事を検索して返す"""
    store = os.environ["SHOPIFY_STORE"]
    blog_id = os.environ["SHOPIFY_BLOG_ID"]

    response = requests.get(
        f"https://{store}/admin/api/2026-04/blogs/{blog_id}/articles.json",
        headers=_get_headers(),
        params={"limit": 250},
    )
    response.raise_for_status()
    articles = response.json().get("articles", [])
    return next((a for a in articles if a["handle"] == handle), None)


def unpublish_article(published_url: str) -> bool:
    """公開済み記事を下書きに戻す（published_url からハンドルを抽出）"""
    store = os.environ["SHOPIFY_STORE"]
    blog_id = os.environ["SHOPIFY_BLOG_ID"]

    handle = published_url.rstrip("/").split("/")[-1]
    article = find_article_by_handle(handle)
    if not article:
        raise ValueError(f"記事が見つかりません: {handle}")

    response = requests.put(
        f"https://{store}/admin/api/2026-04/blogs/{blog_id}/articles/{article['id']}.json",
        headers=_get_headers(),
        json={"article": {"id": article["id"], "published": False}},
    )
    response.raise_for_status()
    return True
