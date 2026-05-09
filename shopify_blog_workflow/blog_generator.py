import anthropic
from dataclasses import dataclass
from website_analyzer import WebsiteData
import config


@dataclass
class BlogPost:
    title: str
    body: str
    tags: list[str]
    meta_description: str
    language: str


def generate_blog(website_data: WebsiteData, language: str = "ja") -> BlogPost:
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    lang_instruction = (
        "日本語で書いてください。" if language == "ja" else "Please write in English."
    )
    products_text = "\n".join(f"- {p}" for p in website_data.products) or "不明"

    prompt = f"""
以下のブランド情報をもとに、SEOに最適化されたShopifyブログ記事を作成してください。

{lang_instruction}

【ブランド情報】
サイト名: {website_data.title}
URL: {website_data.url}
説明: {website_data.description}
ブランドトーン: {website_data.brand_tone}
主なコンテンツ・商品:
{products_text}

サイト本文抜粋:
{website_data.main_content[:1500]}

【出力フォーマット（必ずこの形式で）】
TITLE: <タイトル>
META: <メタディスクリプション（120文字以内）>
TAGS: <タグ1>, <タグ2>, <タグ3>
BODY:
<本文（800〜1200文字、H2見出し2〜3個を含む）>

【記事要件】
- 読者に価値を提供する実用的な内容
- 自然なSEOキーワードを含む
- ブランドのトーンに合わせた文体
- 商品やサービスへの自然な誘導
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text
    return _parse_response(raw, language)


def _parse_response(raw: str, language: str) -> BlogPost:
    lines = raw.strip().splitlines()
    title = ""
    meta = ""
    tags: list[str] = []
    body_lines: list[str] = []
    in_body = False

    for line in lines:
        if line.startswith("TITLE:"):
            title = line[len("TITLE:"):].strip()
        elif line.startswith("META:"):
            meta = line[len("META:"):].strip()
        elif line.startswith("TAGS:"):
            tags = [t.strip() for t in line[len("TAGS:"):].split(",")]
        elif line.startswith("BODY:"):
            in_body = True
        elif in_body:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    if not title:
        title = "ブランドストーリー" if language == "ja" else "Brand Story"
    if not body:
        body = raw

    return BlogPost(
        title=title,
        body=body,
        tags=tags,
        meta_description=meta,
        language=language,
    )
