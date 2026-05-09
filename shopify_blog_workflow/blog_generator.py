"""
Claude API を使ってブログ記事ドラフトを生成する
"""
import json
import os
import anthropic


SYSTEM_PROMPT = """あなたはShopifyブランド専門のプロブログライターです。
提供されたWebサイト情報を分析し、SEOに最適化されたブログ記事を作成してください。

【ブログの要件】
- 読者: ブランドの潜在顧客・既存顧客
- トーン: 親しみやすく、信頼感がある、専門的
- 構成: 導入 → 本文（H2/H3セクション2〜4個） → まとめ → CTA
- 文字数: 1500〜2500文字
- SEO: 自然な形でキーワードを含める

必ず以下のJSON形式のみで出力してください（```json ``` は不要）:
{
  "title": "キャッチーで検索されやすいタイトル",
  "meta_description": "SEO用メタディスクリプション（120〜155文字）",
  "content": "Markdown形式のブログ本文",
  "tags": ["タグ1", "タグ2", "タグ3"],
  "image_prompts": [
    "英語の画像生成プロンプト1（DALL-E/Midjourney用）",
    "英語の画像生成プロンプト2"
  ],
  "seo_keywords": ["メインキーワード", "サブキーワード1", "サブキーワード2"]
}"""


def generate_blog(site_data: dict, language: str = "ja") -> dict:
    """Claude API でブログドラフトを生成する。"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    lang_note = "日本語で" if language == "ja" else "in English"

    user_prompt = f"""以下のWebサイト情報を元に、{lang_note}ブログ記事を作成してください。

【サイト情報】
URL: {site_data['url']}
ブランド名 / タイトル: {site_data['title']}
概要: {site_data['meta_description']}
価格情報: {', '.join(site_data['prices']) if site_data['prices'] else 'なし'}
画像の説明: {', '.join(site_data['images'][:10]) if site_data['images'] else 'なし'}

【サイトコンテンツ（抜粋）】
{site_data['content'][:5000]}

JSON形式で出力してください。"""

    full_text = ""
    print()

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            print(text, end="", flush=True)

    print("\n")

    return _parse_blog_json(full_text, site_data)


def _parse_blog_json(raw: str, site_data: dict) -> dict:
    """レスポンスからJSONを抽出してパースする。"""
    # Markdownコードブロックを除去
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    # 先頭の { から末尾の } まで取り出す
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    try:
        blog = json.loads(text)
    except json.JSONDecodeError:
        # フォールバック: 生テキストをcontentとして返す
        blog = {
            "title": site_data.get("title", "ブログ記事"),
            "meta_description": site_data.get("meta_description", ""),
            "content": raw,
            "tags": [],
            "image_prompts": [],
            "seo_keywords": [],
        }

    blog["source_url"] = site_data["url"]
    return blog
