#!/usr/bin/env python3
"""
Shopify Blog Workflow Automation
使い方: python main.py <URL> [オプション]
"""
import argparse
import sys
import json

from website_analyzer import analyze_website
from blog_generator import generate_blog
from google_docs_client import create_google_doc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WebサイトURLからShopifyブログドラフトを自動生成してGoogle Docsに保存します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python main.py https://example-brand.com
  python main.py https://example-brand.com --lang en
  python main.py https://example-brand.com --no-docs --output blog.json
        """,
    )
    parser.add_argument("url", help="分析するWebサイトのURL")
    parser.add_argument(
        "--lang",
        default="ja",
        choices=["ja", "en"],
        help="ブログの言語 (デフォルト: ja)",
    )
    parser.add_argument(
        "--no-docs",
        action="store_true",
        help="Google Docsへの保存をスキップ（標準出力に表示）",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="ブログデータをJSONファイルに保存する（例: blog.json）",
    )
    args = parser.parse_args()

    # Step 1: Webサイト分析
    print(f"\n{'='*60}")
    print(f"  Step 1: Webサイト分析")
    print(f"{'='*60}")
    print(f"URL: {args.url}")

    try:
        site_data = analyze_website(args.url)
    except RuntimeError as e:
        print(f"\nエラー: {e}", file=sys.stderr)
        return 1

    print(f"ブランド名: {site_data['title']}")
    print(f"概要: {site_data['meta_description'][:80]}...")

    # Step 2: ブログ生成
    print(f"\n{'='*60}")
    print(f"  Step 2: ブログ記事生成 (Claude claude-opus-4-7)")
    print(f"{'='*60}")
    print("生成中... ", end="", flush=True)

    try:
        blog = generate_blog(site_data, language=args.lang)
    except Exception as e:
        print(f"\nエラー: ブログ生成に失敗しました: {e}", file=sys.stderr)
        return 1

    print(f"タイトル  : {blog['title']}")
    print(f"文字数    : {len(blog.get('content', ''))} 文字")
    print(f"タグ      : {', '.join(blog.get('tags', []))}")
    print(f"キーワード: {', '.join(blog.get('seo_keywords', []))}")

    if blog.get("image_prompts"):
        print(f"\n【画像生成プロンプト (DALL-E / Midjourney用)】")
        for i, prompt in enumerate(blog["image_prompts"], 1):
            print(f"  画像{i}: {prompt}")

    # JSONファイル保存（オプション）
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(blog, f, ensure_ascii=False, indent=2)
        print(f"\nJSONファイルを保存しました: {args.output}")

    # Step 3: Google Docs保存
    if args.no_docs:
        print(f"\n{'='*60}")
        print("【ブログ本文プレビュー】")
        print(f"{'='*60}")
        print(blog.get("content", ""))
    else:
        print(f"\n{'='*60}")
        print(f"  Step 3: Google Docsへ保存")
        print(f"{'='*60}")
        print("Google Docsにアップロード中...")

        try:
            doc_url = create_google_doc(blog)
        except FileNotFoundError as e:
            print(f"\nエラー: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"\nエラー: Google Docsへの保存に失敗しました: {e}", file=sys.stderr)
            return 1

        print(f"\n✅ 完了！")
        print(f"{'='*60}")
        print(f"Google Docs URL:")
        print(f"  {doc_url}")
        print(f"{'='*60}")
        print("\nクライアントにURLを共有して確認・承認をもらってください。")
        print("承認後は以下のコマンドでShopify投稿ができます（Phase 2）:")
        print("  python post_to_shopify.py <doc_url>")

    return 0


if __name__ == "__main__":
    sys.exit(main())
