"""ドラフトを Shopify ブログ記事として投稿する"""
import html
import json
import os
import re
from urllib.parse import urlparse

import requests


def _esc(text) -> str:
    """HTML の本文・属性に埋め込む値をエスケープする"""
    return html.escape(str(text or ""), quote=True)


def _safe_url(url) -> str:
    """http(s) 以外の URL（javascript: など）は空文字にし、属性用にエスケープして返す"""
    url = str(url or "").strip()
    if urlparse(url).scheme.lower() not in ("http", "https"):
        return ""
    return _esc(url)


def build_cta_html(cta: dict) -> str:
    """CTA ボタンの HTML を返す（url が http(s) でない場合は出力しない）"""
    cta = cta or {}
    url = _safe_url(cta.get("url"))
    text = cta.get("text")
    if not url or not text:
        return ""
    return (
        '\n<div style="text-align:center;margin:2.5em 0;">'
        f'<a href="{url}" '
        f'style="display:inline-block;padding:14px 32px;background:#1a1a1a;color:#fff;'
        f'text-decoration:none;border-radius:4px;font-weight:600;letter-spacing:0.03em;">'
        f'{_esc(text)}</a></div>'
    )


def _inline_format(line: str) -> str:
    """エスケープ済みのテキストに太字・斜体を適用する"""
    line = _esc(line)
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
    # "</script>" などで script タグから抜け出せないよう <, >, & をエスケープする
    payload = (
        json.dumps(schema, indent=2, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return f'<script type="application/ld+json">\n{payload}\n</script>'


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
            html_lines.append(f"<h1>{_esc(line[2:].strip())}</h1>")

        elif line.startswith("## "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<h2>{_esc(line[3:].strip())}</h2>")
            # 1つおきに画像を挿入（2番目のH2、4番目のH2…）
            if h2_count % 2 == 1:
                img_url = _safe_url(next(image_iter, None))
                if img_url:
                    alt = _esc(next(alt_iter, ""))
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
            html_lines.append(f"<h3>{_esc(line[4:].strip())}</h3>")

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
    body_html += build_cta_html(draft.get("cta"))

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
        article_data["article"]["summary_html"] = f"<p>{_esc(meta_desc)}</p>"

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
