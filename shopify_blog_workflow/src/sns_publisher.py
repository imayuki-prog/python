import os
import anthropic
import requests


def generate_sns_caption(draft: dict, article_url: str) -> dict:
    """ブログ内容からFacebook・Instagram用キャプションをClaudeで生成する"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""You are a social media expert specializing in introducing Japanese brands to the US market.

Based on the following blog article, write TWO social media captions:

Blog Title: {draft['title']}
Blog URL: {article_url}

Blog Content (first 2000 chars):
{draft['full_text'][:2000]}

---

Write exactly in this format:

FACEBOOK:
[Facebook caption here — 150-250 words, storytelling tone, 1-2 relevant emojis, end with the blog URL and 3-5 hashtags]

INSTAGRAM:
[Instagram caption here — 100-150 words, punchy and visual, 3-5 emojis, end with "Link in bio" and 10-15 hashtags on a new line]

Rules:
- Highlight the Japanese craftsmanship and unique story
- Speak to US audience values: sustainability, quality, authenticity
- Never sound like an ad — sound like a discovery
- Use natural, conversational English
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text

    facebook_caption = ""
    instagram_caption = ""

    if "FACEBOOK:" in text and "INSTAGRAM:" in text:
        parts = text.split("INSTAGRAM:")
        facebook_caption = parts[0].replace("FACEBOOK:", "").strip()
        instagram_caption = parts[1].strip()
    else:
        facebook_caption = text
        instagram_caption = text

    return {"facebook": facebook_caption, "instagram": instagram_caption}


def post_to_facebook(caption: str, image_url: str = None) -> str:
    """Facebook ページに投稿する"""
    page_id = os.environ["FACEBOOK_PAGE_ID"]
    access_token = os.environ["META_ACCESS_TOKEN"]

    if image_url:
        endpoint = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        payload = {"message": caption, "url": image_url, "access_token": access_token}
    else:
        endpoint = f"https://graph.facebook.com/v19.0/{page_id}/feed"
        payload = {"message": caption, "access_token": access_token}

    response = requests.post(endpoint, data=payload)
    response.raise_for_status()
    post_id = response.json().get("id")
    print(f"Facebook に投稿しました: post_id={post_id}")
    return post_id


def post_to_instagram(caption: str, image_url: str) -> str:
    """Instagram ビジネスアカウントに投稿する"""
    ig_account_id = os.environ["INSTAGRAM_ACCOUNT_ID"]
    access_token = os.environ["META_ACCESS_TOKEN"]

    # Step 1: メディアコンテナを作成
    container_res = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_account_id}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
    )
    container_res.raise_for_status()
    container_id = container_res.json()["id"]

    # Step 2: 投稿を公開
    publish_res = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_account_id}/media_publish",
        data={"creation_id": container_id, "access_token": access_token},
    )
    publish_res.raise_for_status()
    post_id = publish_res.json().get("id")
    print(f"Instagram に投稿しました: post_id={post_id}")
    return post_id
