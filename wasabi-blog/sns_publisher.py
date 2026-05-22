import os
import requests


def _build_caption(draft: dict, article_url: str, platform: str) -> str:
    title = draft.get("title", "")
    keywords = draft.get("seo", {}).get("keywords", [])
    meta_desc = draft.get("seo", {}).get("meta_description", "")
    hashtags = " ".join(f"#{kw.replace(' ', '').replace('-', '')}" for kw in keywords[:8])

    if platform == "facebook":
        return f"{title}\n\n{meta_desc}\n\nRead more: {article_url}\n\n{hashtags}"
    else:
        return f"{title}\n\n{meta_desc}\n\nLink in bio 🔗\n\n{hashtags} #japaneseculture #madeinJapan"


def post_to_facebook(draft: dict, article_url: str):
    page_id = os.environ["FACEBOOK_PAGE_ID"]
    access_token = os.environ["META_ACCESS_TOKEN"]
    caption = _build_caption(draft, article_url, "facebook")
    image_url = (draft.get("images") or [None])[0]

    if image_url:
        endpoint = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        payload = {"message": caption, "url": image_url, "access_token": access_token}
    else:
        endpoint = f"https://graph.facebook.com/v19.0/{page_id}/feed"
        payload = {"message": caption, "access_token": access_token}

    response = requests.post(endpoint, data=payload)
    response.raise_for_status()
    print(f"✅ Facebookに投稿しました: {response.json().get('id')}")


def post_to_instagram(draft: dict, article_url: str):
    ig_id = os.environ["INSTAGRAM_ACCOUNT_ID"]
    access_token = os.environ["META_ACCESS_TOKEN"]
    image_url = (draft.get("images") or [None])[0]

    if not image_url:
        print("⚠️  Instagram: 画像がないためスキップ")
        return

    caption = _build_caption(draft, article_url, "instagram")

    container_res = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": access_token},
    )
    container_res.raise_for_status()
    container_id = container_res.json()["id"]

    publish_res = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_id}/media_publish",
        data={"creation_id": container_id, "access_token": access_token},
    )
    publish_res.raise_for_status()
    print(f"✅ Instagramに投稿しました: {publish_res.json().get('id')}")