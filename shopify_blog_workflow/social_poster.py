import requests
from blog_generator import BlogPost
import config


def post_to_social(blog: BlogPost, blog_url: str = "") -> dict:
    results = {}

    if config.INSTAGRAM_ACCESS_TOKEN and config.INSTAGRAM_ACCOUNT_ID:
        results["instagram"] = _post_instagram(blog, blog_url)

    if config.FACEBOOK_ACCESS_TOKEN and config.FACEBOOK_PAGE_ID:
        results["facebook"] = _post_facebook(blog, blog_url)

    if not results:
        raise ValueError(
            ".env に Instagram または Facebook の認証情報を設定してください。"
        )

    return results


def _post_instagram(blog: BlogPost, blog_url: str) -> dict:
    caption = f"{blog.title}\n\n{blog.meta_description}"
    if blog_url:
        caption += f"\n\n詳細はプロフィールのリンクから👆"
    if blog.tags:
        hashtags = " ".join(f"#{t.strip()}" for t in blog.tags if t.strip())
        caption += f"\n\n{hashtags}"

    base_url = f"https://graph.facebook.com/v18.0/{config.INSTAGRAM_ACCOUNT_ID}"

    container_resp = requests.post(
        f"{base_url}/media",
        params={
            "caption": caption,
            "access_token": config.INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=15,
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]

    publish_resp = requests.post(
        f"{base_url}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": config.INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=15,
    )
    publish_resp.raise_for_status()
    return publish_resp.json()


def _post_facebook(blog: BlogPost, blog_url: str) -> dict:
    message = f"{blog.title}\n\n{blog.meta_description}"
    if blog.tags:
        hashtags = " ".join(f"#{t.strip()}" for t in blog.tags if t.strip())
        message += f"\n\n{hashtags}"

    payload: dict = {
        "message": message,
        "access_token": config.FACEBOOK_ACCESS_TOKEN,
    }
    if blog_url:
        payload["link"] = blog_url

    resp = requests.post(
        f"https://graph.facebook.com/v18.0/{config.FACEBOOK_PAGE_ID}/feed",
        params=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
