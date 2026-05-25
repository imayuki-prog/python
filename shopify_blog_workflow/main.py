#!/usr/bin/env python3
"""
shopify_blog_workflow
URL → スクレイピング → Claude でブログ生成 → Google Docs → Shopify → SNS
"""
import os
import sys
from dotenv import load_dotenv

from src.scraper import scrape_url
from src.blog_generator import generate_blog_draft
from src.google_docs import create_draft_doc
from src.shopify_publisher import publish_to_shopify
from src.sns_publisher import generate_sns_caption, post_to_facebook, post_to_instagram


def main():
    load_dotenv()

    # URLを受け取る
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("ブログのネタ元URLを入力してください: ").strip()

    if not url:
        print("URLが入力されていません。終了します。")
        sys.exit(1)

    google_folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    word_count = int(os.environ.get("BLOG_WORD_COUNT", 800))

    # ── Step 1: スクレイピング ──────────────────────────────
    print(f"\n[1/5] URLをスクレイピング中: {url}")
    source = scrape_url(url)
    print(f"      タイトル取得: {source['title']}")
    print(f"      画像取得数: {len(source['images'])}枚")

    # ── Step 2: ブログ生成 ─────────────────────────────────
    print(f"\n[2/5] Claude でブログ草稿を生成中 (目標: {word_count}語)...")
    draft = generate_blog_draft(source, word_count=word_count)
    print(f"      生成タイトル: {draft['title']}")

    # ── Step 3: Google Docs に保存 ─────────────────────────
    print("\n[3/5] Google Docs に保存中...")
    doc_url = create_draft_doc(draft, folder_id=google_folder_id)

    # ── Step 4: Shopify に投稿 ─────────────────────────────
    print("\n[4/5] Shopify に投稿中...")
    shopify_result = publish_to_shopify(draft, published=True)
    article_url = shopify_result["url"]

    # ── Step 5: SNS に投稿 ────────────────────────────────
    print("\n[5/5] SNS キャプションを生成してFacebook・Instagramに投稿中...")
    captions = generate_sns_caption(draft, article_url)

    image_url = draft["images"][0] if draft.get("images") else None

    fb_env = os.environ.get("FACEBOOK_PAGE_ID")
    ig_env = os.environ.get("INSTAGRAM_ACCOUNT_ID")

    if fb_env:
        post_to_facebook(captions["facebook"], image_url=image_url)
    else:
        print("      Facebook: FACEBOOK_PAGE_ID が未設定のためスキップ")

    if ig_env and image_url:
        post_to_instagram(captions["instagram"], image_url=image_url)
    else:
        print("      Instagram: INSTAGRAM_ACCOUNT_ID または画像が未設定のためスキップ")

    # ── 完了 ──────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("完了！")
    print(f"Google Docs : {doc_url}")
    print(f"Shopify記事 : {article_url}")
    print("=" * 50)

    print("\n--- Facebook キャプション ---")
    print(captions["facebook"])
    print("\n--- Instagram キャプション ---")
    print(captions["instagram"])


if __name__ == "__main__":
    main()
