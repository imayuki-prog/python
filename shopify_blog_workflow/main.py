#!/usr/bin/env python3
import argparse
import sys
import config


def main():
    parser = argparse.ArgumentParser(
        description="Shopify ブログ自動生成ワークフロー"
    )
    parser.add_argument("url", help="分析するブランドサイトのURL")
    parser.add_argument(
        "--lang",
        choices=["ja", "en"],
        default="ja",
        help="ブログ記事の言語 (デフォルト: ja)",
    )
    parser.add_argument(
        "--no-docs",
        action="store_true",
        help="Google Docs への保存をスキップしてターミナルに表示",
    )
    parser.add_argument(
        "--shopify",
        action="store_true",
        help="Shopify に下書きとして投稿する (Phase 2)",
    )
    parser.add_argument(
        "--social",
        action="store_true",
        help="Instagram/Facebook に投稿する (Phase 3)",
    )
    args = parser.parse_args()

    if not config.ANTHROPIC_API_KEY:
        print("[エラー] ANTHROPIC_API_KEY が設定されていません。")
        print("  .env ファイルに ANTHROPIC_API_KEY=sk-ant-... を追加してください。")
        sys.exit(1)

    # Step 1: Web スクレイピング
    print(f"\n[Step 1] サイトを分析中: {args.url}")
    from website_analyzer import fetch_website
    try:
        website_data = fetch_website(args.url)
        print(f"  ブランド名: {website_data.title}")
        print(f"  トーン: {website_data.brand_tone}")
    except Exception as e:
        print(f"[エラー] サイトの取得に失敗しました: {e}")
        sys.exit(1)

    # Step 2: Claude API でブログ生成
    print(f"\n[Step 2] ブログ記事を生成中 (言語: {args.lang})...")
    from blog_generator import generate_blog
    try:
        blog = generate_blog(website_data, language=args.lang)
        print(f"  タイトル: {blog.title}")
        print(f"  タグ: {', '.join(blog.tags)}")
    except Exception as e:
        print(f"[エラー] ブログ生成に失敗しました: {e}")
        sys.exit(1)

    # Step 3: Google Docs or ターミナル表示
    doc_url = ""
    if args.no_docs:
        print("\n" + "=" * 60)
        print(f"タイトル: {blog.title}")
        print(f"メタ: {blog.meta_description}")
        print(f"タグ: {', '.join(blog.tags)}")
        print("-" * 60)
        print(blog.body)
        print("=" * 60)
    else:
        print("\n[Step 3] Google Docs に保存中...")
        from google_docs_client import save_to_google_docs
        try:
            doc_url = save_to_google_docs(blog)
            print(f"  保存完了: {doc_url}")
        except FileNotFoundError as e:
            print(f"[エラー] {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[エラー] Google Docs への保存に失敗しました: {e}")
            sys.exit(1)

    # Phase 2: Shopify 投稿 (オプション)
    if args.shopify:
        print("\n[Phase 2] Shopify に投稿中...")
        from shopify_client import post_to_shopify
        try:
            result = post_to_shopify(blog, status="draft")
            article_id = result.get("article", {}).get("id", "不明")
            print(f"  投稿完了 (下書き) - Article ID: {article_id}")
        except Exception as e:
            print(f"[エラー] Shopify への投稿に失敗しました: {e}")

    # Phase 3: SNS 投稿 (オプション)
    if args.social:
        print("\n[Phase 3] SNS に投稿中...")
        from social_poster import post_to_social
        try:
            results = post_to_social(blog, blog_url=doc_url)
            for platform, result in results.items():
                print(f"  {platform}: 投稿完了 - {result}")
        except Exception as e:
            print(f"[エラー] SNS への投稿に失敗しました: {e}")

    print("\n完了!")


if __name__ == "__main__":
    main()
