"""
Phase 3: Meta Graph API で Instagram / Facebook に投稿する
"""
import requests
import anthropic
import os
from config import META_PAGE_ACCESS_TOKEN, META_PAGE_ID, META_INSTAGRAM_ACCOUNT_ID


def post_to_social(blog: dict, image_url: str, shopify_article_url: str) -> dict:
    """
    ブログ記事をSNSに投稿する。

    事前準備:
    1. Meta for Developers → My Apps → Graph API
    2. Facebook Page Access Token を取得（publish_pages, instagram_basic, instagram_content_publish）
    3. .env に META_PAGE_ACCESS_TOKEN, META_PAGE_ID, META_INSTAGRAM_ACCOUNT_ID を設定
    必要な権限:
    - pages_manage_posts
    - instagram_content_publish
    """
    if not META_PAGE_ACCESS_TOKEN:
        raise EnvironmentError("META_PAGE_ACCESS_TOKEN を .env に設定してください")

    # SNS用キャプション生成
    fb_caption, ig_caption = _generate_captions(blog, shopify_article_url)

    results = {}

    # Facebook投稿
    if META_PAGE_ID:
        fb_result = _post_to_facebook(fb_caption, image_url)
        results["facebook"] = fb_result
        print(f"Facebook投稿完了: {fb_result.get('id')}")

    # Instagram投稿
    if META_INSTAGRAM_ACCOUNT_ID and image_url:
        ig_result = _post_to_instagram(ig_caption, image_url)
        results["instagram"] = ig_result
        print(f"Instagram投稿完了: {ig_result.get('id')}")

    return results


def _generate_captions(blog: dict, article_url: str) -> tuple[str, str]:
    """Claude APIでSNS用キャプションを生成する。"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""以下のブログ記事をSNSで宣伝するキャプションを作成してください。

タイトル: {blog.get('title')}
概要: {blog.get('meta_description')}
タグ: {', '.join(blog.get('tags', []))}
記事URL: {article_url}

JSON形式で出力:
{{
  "facebook": "Facebookキャプション（300文字以内、URLと絵文字含む）",
  "instagram": "Instagramキャプション（ハッシュタグ10個以上含む、改行あり）"
}}""",
            }
        ],
    )

    import json
    text = response.content[0].text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    return data.get("facebook", ""), data.get("instagram", "")


def _post_to_facebook(caption: str, image_url: str | None) -> dict:
    """Facebookページに投稿する。"""
    url = f"https://graph.facebook.com/v18.0/{META_PAGE_ID}/feed"
    payload = {
        "message": caption,
        "access_token": META_PAGE_ACCESS_TOKEN,
    }
    if image_url:
        # 画像付き投稿
        url = f"https://graph.facebook.com/v18.0/{META_PAGE_ID}/photos"
        payload["url"] = image_url

    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()


def _post_to_instagram(caption: str, image_url: str) -> dict:
    """Instagramに画像投稿する（2ステップ: メディア作成 → 公開）。"""
    # Step 1: メディアコンテナ作成
    container_url = f"https://graph.facebook.com/v18.0/{META_INSTAGRAM_ACCOUNT_ID}/media"
    container_resp = requests.post(container_url, data={
        "image_url": image_url,
        "caption": caption,
        "access_token": META_PAGE_ACCESS_TOKEN,
    })
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]

    # Step 2: 公開
    publish_url = f"https://graph.facebook.com/v18.0/{META_INSTAGRAM_ACCOUNT_ID}/media_publish"
    publish_resp = requests.post(publish_url, data={
        "creation_id": container_id,
        "access_token": META_PAGE_ACCESS_TOKEN,
    })
    publish_resp.raise_for_status()
    return publish_resp.json()
