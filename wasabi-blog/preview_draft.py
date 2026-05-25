#!/usr/bin/env python3
"""
ドラフトをHTMLに変換してSurge.shにデプロイし、共有URLを表示する

使い方:
  python preview_draft.py drafts/YYYY-MM-DD_slug.md
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from draft_manager import load_draft
from shopify_publisher import _build_faq_jsonld, _markdown_to_html

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{meta_description}">
  <meta name="keywords" content="{keywords}">
  {faq_jsonld}
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f9f9f7;
      color: #1a1a1a;
      line-height: 1.75;
    }}
    .preview-bar {{
      background: #2563eb;
      color: white;
      text-align: center;
      padding: 10px;
      font-size: 13px;
      letter-spacing: 0.05em;
    }}
    .container {{
      max-width: 740px;
      margin: 48px auto;
      padding: 0 24px 80px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    }}
    .meta {{
      font-size: 13px;
      color: #888;
      padding: 28px 0 8px;
      border-bottom: 1px solid #eee;
      margin-bottom: 32px;
    }}
    h1 {{
      font-size: 2rem;
      font-weight: 700;
      line-height: 1.3;
      margin: 32px 0 16px;
      color: #111;
    }}
    h2 {{
      font-size: 1.35rem;
      font-weight: 600;
      margin: 40px 0 12px;
      color: #222;
      border-left: 4px solid #2563eb;
      padding-left: 12px;
    }}
    h3 {{
      font-size: 1.1rem;
      font-weight: 600;
      margin: 28px 0 8px;
      color: #333;
    }}
    p {{
      margin: 0 0 16px;
      font-size: 1.05rem;
    }}
    ul {{
      margin: 0 0 16px 24px;
    }}
    li {{
      margin-bottom: 8px;
      font-size: 1.05rem;
    }}
    blockquote {{
      border-left: 4px solid #e5e7eb;
      margin: 24px 0;
      padding: 12px 20px;
      color: #555;
      font-style: italic;
    }}
    hr {{
      border: none;
      border-top: 1px solid #eee;
      margin: 40px 0;
    }}
    figure {{
      margin: 24px 0;
    }}
    figure img {{
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      display: block;
    }}
    strong {{ font-weight: 600; }}
    em {{ font-style: italic; }}
  </style>
</head>
<body>
  <div class="preview-bar">DRAFT PREVIEW — Not yet published</div>
  <div class="container">
    <div class="meta">Source: {source_url} &nbsp;·&nbsp; Created: {created}</div>
    {body_html}
  </div>
</body>
</html>"""


def _draft_to_domain(draft_path: Path) -> str:
    # DNS label max = 63 chars. prefix "wasabi-" = 7 chars → 56 chars remaining
    stem = draft_path.stem.replace("_", "-")[:56].rstrip("-")
    return f"wasabi-{stem}.surge.sh"


def main():
    if len(sys.argv) < 2:
        print("使い方: python preview_draft.py drafts/YYYY-MM-DD_slug.md")
        sys.exit(1)

    draft_path = Path(sys.argv[1])
    if not draft_path.exists():
        print(f"ファイルが見つかりません: {draft_path}")
        sys.exit(1)

    draft = load_draft(draft_path)
    seo = draft.get("seo") or {}
    image_alts = seo.get("image_alts") or []

    body_html = _markdown_to_html(
        draft["full_text"],
        images=draft.get("images", []),
        image_alts=image_alts,
    )

    # CTA ボタン
    cta = draft.get("cta") or {}
    if cta.get("url") and cta.get("text"):
        body_html += (
            '\n<div style="text-align:center;margin:2.5em 0;">'
            f'<a href="{cta["url"]}" '
            f'style="display:inline-block;padding:14px 32px;background:#1a1a1a;color:#fff;'
            f'text-decoration:none;border-radius:4px;font-weight:600;letter-spacing:0.03em;">'
            f'{cta["text"]}</a></div>'
        )

    faq_jsonld = _build_faq_jsonld(draft["full_text"])

    html = HTML_TEMPLATE.format(
        title=draft["title"],
        meta_description=seo.get("meta_description", ""),
        keywords=", ".join(seo.get("keywords") or []),
        faq_jsonld=faq_jsonld,
        source_url=draft["source_url"],
        created=draft["created"],
        body_html=body_html,
    )

    # 一時ディレクトリにHTMLを書き出す
    tmpdir = tempfile.mkdtemp(prefix="wasabi-preview-")
    html_path = Path(tmpdir) / "index.html"
    html_path.write_text(html, encoding="utf-8")

    domain = _draft_to_domain(draft_path)
    url = f"https://{domain}"

    print(f"\nデプロイ中: {url}")
    result = subprocess.run(
        ["surge", tmpdir, domain],
        capture_output=False,
    )

    shutil.rmtree(tmpdir, ignore_errors=True)

    if result.returncode == 0:
        print(f"\n共有URL: {url}")
    else:
        print("\nデプロイに失敗しました。`surge login` を実行済みか確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main()
