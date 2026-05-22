#!/usr/bin/env python3
"""
承認済みドラフトを Shopify に投稿する

使い方:
  python publish_draft.py                              # ドラフト一覧表示
  python publish_draft.py drafts/YYYY-MM-DD_slug.md   # 指定ドラフトを投稿
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

import re

from draft_manager import list_drafts, load_draft, mark_published
from shopify_publisher import publish_to_shopify


def _prompt_cta(draft_path: Path, draft: dict) -> dict:
    """CTAが未設定の場合、対話的に入力を求めてファイルに保存する"""
    cta = draft.get("cta") or {}
    if cta.get("url") and cta.get("text"):
        return draft

    print("\n--- CTA設定 ---")
    print("ShopifyストアのURLとボタンテキストを入力してください。")
    print("(スキップする場合はそのままEnter)\n")

    url = input("商品ページURL: ").strip()
    text = input("ボタンテキスト (例: Shop Now →): ").strip()

    if url and text:
        raw = draft_path.read_text(encoding="utf-8")
        raw = re.sub(
            r"cta:\n  text: ''\n  url: ''",
            f"cta:\n  text: '{text}'\n  url: {url}",
            raw,
        )
        draft_path.write_text(raw, encoding="utf-8")
        draft["cta"] = {"url": url, "text": text}
        print(f"CTAを設定しました: {text}")
    else:
        print("CTAなしで投稿します。")

    return draft


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        drafts = list_drafts()
        if not drafts:
            print("drafts/ フォルダにドラフトがありません。")
            return
        print("\n--- ドラフト一覧 ---")
        for d in drafts:
            print(f"  [{d['status']:9}] {d['created']}  {d['title']}")
            print(f"               {d['path']}")
        print("\n投稿するには: python publish_draft.py drafts/YYYY-MM-DD_slug.md")
        return

    draft_path = Path(sys.argv[1])
    if not draft_path.exists():
        print(f"ファイルが見つかりません: {draft_path}")
        sys.exit(1)

    draft = load_draft(draft_path)

    if draft["status"] == "published":
        print(f"すでに投稿済みです: {draft['title']}")
        print(f"URL: {draft['published_url']}")
        return

    print(f"\nタイトル: {draft['title']}")
    print(f"画像数: {len(draft['images'])}枚")

    draft = _prompt_cta(draft_path, draft)

    result = publish_to_shopify(draft, published=True)
    mark_published(draft_path, result["url"])

    print(f"\n完了!")
    print(f"Shopify URL: {result['url']}")
    # SNS投稿
    if os.environ.get("FACEBOOK_PAGE_ID") or os.environ.get("INSTAGRAM_ACCOUNT_ID"):
        sns_choice = input("\nSNSにも投稿しますか？ (y/n): ").strip().lower()
        if sns_choice == "y":
            from sns_publisher import post_to_facebook, post_to_instagram
            if os.environ.get("FACEBOOK_PAGE_ID"):
                post_to_facebook(draft, result["url"])
            if os.environ.get("INSTAGRAM_ACCOUNT_ID"):
                post_to_instagram(draft, result["url"])

if __name__ == "__main__":
    main()
