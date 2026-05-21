#!/usr/bin/env python3
"""
Shopify投稿テスト用スクリプト
記事タイトルと本文を手動入力してShopifyに投稿します
"""
import os
from dotenv import load_dotenv
from src.shopify_publisher import publish_to_shopify


def main():
    load_dotenv()

    print("=== Shopify 投稿テスト ===\n")

    title = input("記事タイトルを入力してください: ").strip()
    print("本文を入力してください（Markdown形式）。入力完了後、空行で 'END' と入力してください：")
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    body = "\n".join(lines)

    image_url = input("\nアイキャッチ画像のURL（不要な場合はそのままEnter）: ").strip()

    draft = {
        "title": title,
        "body": body,
        "full_text": f"# {title}\n\n{body}",
        "source_url": "",
        "images": [image_url] if image_url else [],
    }

    publish_now = input("\n今すぐ公開しますか？ (y=公開 / n=下書き保存): ").strip().lower()
    published = publish_now == "y"

    print("\nShopifyに投稿中...")
    result = publish_to_shopify(draft, published=published)

    print(f"\n✅ 完了！")
    print(f"記事URL: {result['url']}")


if __name__ == "__main__":
    main()
