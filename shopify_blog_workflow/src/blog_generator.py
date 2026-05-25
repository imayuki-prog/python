import os
import anthropic


def generate_blog_draft(source: dict, word_count: int = 800) -> dict:
    """スクレイピングした内容をもとにアメリカ向け英語ブログ記事を生成する"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""You are an expert content strategist and SEO/GEO copywriter specializing in introducing Japanese brands to the US market.

The brand you are writing about is Japanese and has ZERO brand awareness in the United States. Your goal is to build awareness, drive website traffic, and encourage purchases — through storytelling, not hard selling.

Source URL: {source['url']}
Source Title: {source['title']}

Source Content:
{source['content'][:6000]}

---

ARTICLE STRUCTURE:
# [Compelling H1 title with target keyword — written for curiosity and search intent]

[Hook: 2-3 sentences that draw the reader in with a relatable problem, surprising fact, or cultural insight]

## [H2 — "What is...?" or "Why...?" format for GEO/AI search visibility]
[Clear, concise answer in the first 1-2 sentences, then expand]

## [H2 — The Japanese story: craftsmanship, heritage, or culture angle]
[Humanize the brand. Share the "why behind the product" — tradition, artisans, philosophy]

## [H2 — Why this matters for Americans / What makes it unique]
[Translate Japanese values into US-relevant benefits: sustainability, quality, uniqueness, wellness, etc.]

## [H2 — How to use it / What to expect]
[Practical, helpful content that builds trust]

## [H2 — FAQ format: 2-3 common questions with direct answers]
[Boosts GEO — AI search engines pull from FAQ-style content]

[Call to action: soft, friendly, not salesy. Invite readers to explore, learn more, or try it.]

---

SEO REQUIREMENTS:
- Naturally weave in 2-3 relevant English keywords based on the product/brand (identify from the source content)
- Include the primary keyword in the H1 title and at least one H2
- Write a strong opening paragraph that also works as a meta description (under 160 characters if possible)

GEO (Generative Engine Optimization) REQUIREMENTS:
- Use question-based H2 headings ("What is...?", "Why...?", "How does...?")
- Provide clear, direct answers immediately after each heading
- Include a FAQ section with 2-3 questions and concise answers
- Write authoritatively — AI search engines favor expert, trustworthy content

TONE & STYLE:
- Friendly, warm, and genuine — like a recommendation from a knowledgeable friend
- Storytelling-first: lead with the human story, not the product specs
- Avoid corporate jargon and pushy sales language
- Celebrate Japanese craftsmanship without being cliché ("samurai", "zen", etc.)
- Approximately {word_count} words
- Output in markdown (# for H1, ## for H2)
- Do NOT copy the source text — rewrite, interpret, and add cultural context

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
        "images": source.get("images", []),
    }
