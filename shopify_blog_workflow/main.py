#!/usr/bin/env python3
"""
shopify_blog_workflow - Phase 1
URL → スクレイピング → Claude でブログ草稿生成 → Google Docs に保存
"""
import os
import sys
from dotenv import load_dotenv

from src.scraper import scrape_url
from src.blog_generator import generate_blog_draft
from src.google_docs import create_draft_doc


def main():
    load_dotenv()

    # 引数またはインタラクティブ入力でURLを受け取る
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("ブログのネタ元URLを入力してください: ").strip()

    if not url:
        print("URLが入力されていません。終了します。")
        sys.exit(1)

    google_folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    word_count = int(os.environ.get("BLOG_WORD_COUNT", 800))

    print(f"\n[1/3] URLをスクレイピング中: {url}")
    source = scrape_url(url)
    print(f"      タイトル取得: {source['title']}")
    print(f"      画像取得数: {len(source['images'])}枚")
    if source["images"]:
        print(f"      先頭画像: {source['images'][0]}")

    print(f"\n[2/3] Claude でブログ草稿を生成中 (目標: {word_count}語)...")
    draft = generate_blog_draft(source, word_count=word_count)
    print(f"      生成タイトル: {draft['title']}")

    print("\n[3/3] Google Docs に保存中...")
    doc_url = create_draft_doc(draft, folder_id=google_folder_id)

    print(f"\n完了！")
    print(f"Google Docs URL: {doc_url}")
    if draft.get("images"):
        print(f"\n画像候補 ({len(draft['images'])}枚) はGoogle Docsの末尾に記載されています。")


if __name__ == "__main__":
    main()
