import os
import anthropic


def generate_blog_draft(source: dict, word_count: int = 800) -> dict:
    """スクレイピングした内容をもとにアメリカ向け英語ブログ記事を生成する"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""You are a professional content writer specializing in blog articles for the US market.

Based on the following source content from a website, write an engaging blog article in English.

Source URL: {source['url']}
Source Title: {source['title']}

Source Content:
{source['content'][:6000]}

Requirements:
- Write approximately {word_count} words
- Target audience: US readers
- Tone: friendly, informative, and engaging
- Include a compelling title (H1)
- Structure with clear H2 subheadings
- End with a call-to-action paragraph
- Do NOT copy the source text directly — rewrite and add value
- Output the article in plain text with markdown-style headings (# for H1, ## for H2)

Write the blog article now:"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    article_text = message.content[0].text

    # タイトルを1行目から抽出
    lines = article_text.strip().splitlines()
    title = lines[0].lstrip("# ").strip() if lines else "Blog Draft"
    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else article_text

    return {
        "title": title,
        "body": body,
        "full_text": article_text,
        "source_url": source["url"],
    }
