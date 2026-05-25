# wasabi-blog — Project Guidelines

## Project Overview
Shopify blog automation for a Japanese brand store targeting the US market.
The workflow introduces Japanese products/brands with zero US brand awareness through storytelling-first content.

## Quick Command: 「次」

ユーザーが `次` または `次の記事` と入力したとき:
1. `_next_task.txt` を読み込む
2. ファイルに記載された手順をそのまま実行する（ブランドブリーフ参照 → スクレイプ → 記事生成 → 保存 → content_plan更新）
3. 完了後、`_next_task.txt` を削除する

---

## Workflow
1. User provides a Japanese website URL
2. Claude fetches the URL, generates a blog draft, saves to `drafts/YYYY-MM-DD_slug.md`
3. User runs `venv/bin/python preview_draft.py drafts/xxx.md` → deploys to Surge.sh for client review
4. After approval, user runs `venv/bin/python publish_draft.py drafts/xxx.md` → posts to Shopify

## Brand Brief & Content Planning

Before generating an article, always check if a brand brief exists for that client:

```
brands/{slug}/brief.md          ← brand analysis (generated once, reused)
brands/{slug}/content_plan.yaml ← topic list with status tracking
```

**If a brief exists:** Read it before writing the article to ensure consistent tone, content pillars, and avoid topic overlap.

**Generating a new brand brief** (when user asks or when no brief exists for a URL):
1. Scrape the brand's website (homepage + key product pages)
2. Generate `brands/{slug}/brief.md` with the following sections:
   - ブランド概要 (brand overview, founding story, values)
   - 主力商品 (key products and differentiators)
   - ターゲット顧客（US） (US target customer profile)
   - コンテンツの柱 (3-4 content pillars aligned with the brand)
   - トーン & NG表現 (voice/tone guidance and words to avoid)
   - 競合との差別化 (what makes this brand unique in the US market)
3. Generate `brands/{slug}/content_plan.yaml` with 8-10 topic ideas:
   ```yaml
   topics:
     - theme: "Why Japanese Fermented Foods Are Good for Your Gut"
       keyword: "japanese fermented foods gut health"
       status: "未着手"
       note: ""
   ```

**Slug convention:** Use kebab-case matching the brand folder name (e.g., `kyoto-mori`, `kikusui-sangyo`)

## Key Scripts
- `preview_draft.py` — generates HTML preview and deploys to Surge.sh
- `publish_draft.py` — posts approved draft to Shopify
- `draft_manager.py` — draft file I/O (save / load / list / mark published)
- `shopify_publisher.py` — Markdown→HTML conversion + Shopify API
- `scraper.py` — scrapes URL for content and images

## Article Structure (always follow this)

```
# [H1: compelling title with primary keyword]

[Hook: 2-3 sentences — relatable problem, surprising fact, or cultural insight]

## What is...? / Why...?
[Direct answer in 1-2 sentences, then expand — GEO: AI search pulls direct answers]

## The Japanese Story
[Craftsmanship, heritage, history — humanize the brand]

## Why This Matters for Americans
[Translate Japanese values into US-relevant benefits: sustainability, quality, wellness]

## How to Use It / What to Expect
[Practical, trust-building content — use bullet points]

## FAQ: [Topic]
[2-3 Q&A pairs in **Question?** / Answer format — critical for GEO]

[Soft CTA — invite to explore, not a hard sell]
```

## SEO Requirements
- Primary keyword in H1 and at least one H2
- 2-3 keywords woven naturally throughout
- Opening paragraph doubles as meta description (under 160 characters)
- Target ~800 words

## GEO (Generative Engine Optimization) Requirements
- H2 headings in question format: "What is...?", "Why...?", "How does...?"
- Provide clear, direct answers immediately after each heading
- FAQ section with 2-3 Q&A pairs (generates schema.org FAQPage JSON-LD automatically)
- Write authoritatively — AI search engines favor expert, trustworthy content

## Tone & Style
- Friendly, warm, genuine — like a recommendation from a knowledgeable friend
- Storytelling-first: lead with the human story, not product specs
- Avoid corporate jargon and pushy sales language
- Celebrate Japanese craftsmanship without clichés ("samurai", "zen", etc.)
- Write in English for US audience
- Do NOT copy source text — rewrite, interpret, and add cultural context

## Draft Frontmatter (required fields)
```yaml
status: draft          # draft / published
source_url: https://...
images:                # up to 5 image URLs from source site (PC versions preferred)
  - https://...
created: YYYY-MM-DD
published_url: null
seo:
  meta_description: "..." # under 160 chars, include primary keyword
  keywords:
    - primary keyword
    - secondary keyword
  image_alts:
    - "Descriptive alt text for each image"
```

## Image Handling
- Use PC-sized images from source site (prefer `*PC.jpg` over `*SP.jpg`)
- Generate meaningful alt text describing the image content and brand context
- Images are auto-inserted after every 2nd H2 heading in HTML output
- First image is used as the Shopify article featured image

## CTA (Call to Action)
- Each draft has a `cta` field in frontmatter — left empty at draft creation
- User fills in `url` and `text` after creating the product in Shopify
- CTA renders as a dark button centered below the article body
- Example:
  ```yaml
  cta:
    url: https://your-store.myshopify.com/products/kyoto-mori-tsukemono
    text: Shop Kyoto Mori Tsukemono →
  ```
- If `url` or `text` is empty, no CTA is rendered

## Surge.sh Preview URLs
- Format: `https://wasabi-{YYYY-MM-DD}-{slug}.surge.sh`
- Re-running `preview_draft.py` overwrites the same URL
- URLs are public and permanent (no expiry) — safe to share with clients
