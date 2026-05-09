import requests
from blog_generator import BlogPost
import config


def post_to_shopify(blog: BlogPost, status: str = "draft") -> dict:
    """
    status: "draft" | "published"
    """
    if not config.SHOPIFY_SHOP_URL or not config.SHOPIFY_ADMIN_API_TOKEN:
        raise ValueError(
            ".env に SHOPIFY_SHOP_URL と SHOPIFY_ADMIN_API_TOKEN を設定してください。"
        )

    url = f"https://{config.SHOPIFY_SHOP_URL}/admin/api/2024-01/articles.json"
    headers = {
        "X-Shopify-Access-Token": config.SHOPIFY_ADMIN_API_TOKEN,
        "Content-Type": "application/json",
    }

    body_html = blog.body.replace("\n", "<br>")

    payload = {
        "article": {
            "title": blog.title,
            "body_html": body_html,
            "tags": ", ".join(blog.tags),
            "metafields": [
                {
                    "key": "description_tag",
                    "value": blog.meta_description,
                    "type": "single_line_text_field",
                    "namespace": "global",
                }
            ],
            "published": status == "published",
        }
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()
