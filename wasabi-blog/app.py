"""wasabi-blog ローカル管理アプリ"""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yaml
from dotenv import load_dotenv

from brand_manager import (
    create_brand,
    list_brands,
    load_brief,
    load_content_plan,
    save_brief,
    save_content_plan,
    write_next_task,
)
from draft_manager import list_drafts, load_draft, mark_published, mark_unpublished, save_preview_url, save_approval
from shopify_publisher import _build_faq_jsonld, _markdown_to_html, publish_to_shopify, unpublish_article

load_dotenv()

st.set_page_config(page_title="wasabi-blog", layout="wide", page_icon="🍱")

# ── ヘルパー ──────────────────────────────────────────────────────────────

def _normalize_published_url(url: str) -> str:
    if not url:
        return url
    blog_domain = os.environ.get("SHOPIFY_BLOG_DOMAIN")
    store = os.environ.get("SHOPIFY_STORE", "")
    if blog_domain and store and store in url:
        return url.replace(f"https://{store}", f"https://{blog_domain}")
    return url


def _parse_file(path: Path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    return yaml.safe_load(match.group(1)), match.group(2)


def update_content(path: Path, new_title: str, new_body: str):
    meta, _ = _parse_file(path)
    text = (
        f"---\n{yaml.dump(meta, default_flow_style=False, allow_unicode=True)}---\n\n"
        f"# {new_title}\n\n{new_body}"
    )
    path.write_text(text, encoding="utf-8")


def update_seo_cta(path: Path, cta_url: str, cta_text: str, meta_desc: str, keywords_str: str):
    meta, body = _parse_file(path)
    meta["cta"] = {"url": cta_url.strip(), "text": cta_text.strip()}
    meta.setdefault("seo", {})
    meta["seo"]["meta_description"] = meta_desc.strip()
    meta["seo"]["keywords"] = [k.strip() for k in keywords_str.split(",") if k.strip()]
    path.write_text(
        f"---\n{yaml.dump(meta, default_flow_style=False, allow_unicode=True)}---\n{body}",
        encoding="utf-8",
    )


def build_html(draft: dict) -> str:
    seo = draft.get("seo") or {}
    cta = draft.get("cta") or {}
    image_alts = seo.get("image_alts") or []

    body_html = _markdown_to_html(
        draft["full_text"],
        images=draft.get("images", []),
        image_alts=image_alts,
    )

    if cta.get("url") and cta.get("text"):
        body_html += (
            '\n<div style="text-align:center;margin:2.5em 0;">'
            f'<a href="{cta["url"]}" style="display:inline-block;padding:14px 32px;'
            f'background:#1a1a1a;color:#fff;text-decoration:none;border-radius:4px;'
            f'font-weight:600;letter-spacing:0.03em;">{cta["text"]}</a></div>'
        )

    faq_jsonld = _build_faq_jsonld(draft["full_text"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{draft['title']}</title>
  <meta name="description" content="{seo.get('meta_description', '')}">
  {faq_jsonld}
  <style>
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f9f9f7;color:#1a1a1a;line-height:1.75;}}
    .wrap{{max-width:740px;margin:32px auto;padding:0 24px 80px;background:#fff;border-radius:12px;box-shadow:0 2px 16px rgba(0,0,0,.07);}}
    h1{{font-size:1.9rem;font-weight:700;line-height:1.3;margin:32px 0 16px;}}
    h2{{font-size:1.3rem;font-weight:600;margin:36px 0 12px;border-left:4px solid #2563eb;padding-left:12px;}}
    h3{{font-size:1.05rem;font-weight:600;margin:24px 0 8px;}}
    p{{margin:0 0 16px;font-size:1rem;}}
    ul{{margin:0 0 16px 24px;}} li{{margin-bottom:8px;}}
    blockquote{{border-left:4px solid #e5e7eb;margin:24px 0;padding:12px 20px;color:#555;font-style:italic;}}
    hr{{border:none;border-top:1px solid #eee;margin:36px 0;}}
    figure{{margin:20px 0;}} figure img{{max-width:100%;height:auto;border-radius:8px;display:block;}}
    strong{{font-weight:600;}} em{{font-style:italic;}}
  </style>
</head>
<body><div class="wrap">{body_html}</div></body>
</html>"""


def _to_domain(path: Path) -> str:
    stem = path.stem.replace("_", "-")[:56].rstrip("-")
    return f"wasabi-{stem}.surge.sh"


def deploy_surge(draft: dict, path: Path):
    html = build_html(draft)
    tmpdir = tempfile.mkdtemp(prefix="wasabi-app-")
    try:
        (Path(tmpdir) / "index.html").write_text(html, encoding="utf-8")
        domain = _to_domain(path)
        result = subprocess.run(
            ["surge", tmpdir, domain],
            capture_output=True, text=True, timeout=60,
        )
        return result.returncode == 0, f"https://{domain}"
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── サイドバー ────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🍱 wasabi-blog")
    st.markdown("---")

    drafts = list_drafts()
    if not drafts:
        st.info("ドラフトがありません")
        st.stop()

    labels = []
    path_map = {}
    for d in drafts:
        icon = "✅" if d["status"] == "published" else "📝"
        label = f"{icon} {d['created']}  {d['title'][:30]}…"
        labels.append(label)
        path_map[label] = d["path"]

    if "selected" not in st.session_state or st.session_state.selected not in labels:
        st.session_state.selected = labels[0]

    selected = st.radio("ドラフト一覧", labels,
                        index=labels.index(st.session_state.selected))
    st.session_state.selected = selected

selected_path = path_map[selected]
draft = load_draft(selected_path)

# ── ヘッダー ──────────────────────────────────────────────────────────────

col_h, col_s = st.columns([4, 1])
with col_h:
    st.title(draft["title"])
with col_s:
    if draft["status"] == "published":
        st.success("published")
    else:
        st.warning("draft")

st.caption(f"Source: {draft['source_url']} · {draft['created']}")

if draft.get("preview_url"):
    st.info(f"**クライアント共有URL:** {draft['preview_url']}", icon="🔗")

st.divider()

# ── タブ ──────────────────────────────────────────────────────────────────

tab_brands, tab_list, tab_edit, tab_seo, tab_preview = st.tabs(
    ["🏢 Brands", "📊 管理一覧", "✏️ 記事編集", "🔍 SEO / CTA", "👁️ プレビュー & 投稿"]
)

# ── Brands ────────────────────────────────────────────────────────────────
with tab_brands:
    brands = list_brands()

    col_sel, col_new_name, col_new_btn = st.columns([3, 2, 1])
    with col_sel:
        selected_brand = st.selectbox(
            "ブランドを選択",
            options=[""] + brands,
            format_func=lambda x: "（ブランドを選択）" if x == "" else x,
        )
    with col_new_name:
        new_brand_slug = st.text_input(
            "新規ブランド名",
            placeholder="例: kyoto-mori",
            label_visibility="visible",
        )
    with col_new_btn:
        st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
        if st.button("＋ 追加", use_container_width=True) and new_brand_slug.strip():
            create_brand(new_brand_slug.strip())
            st.success(f"「{new_brand_slug.strip()}」を追加しました")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if not selected_brand:
        if not brands:
            st.info("まずブランドを追加してください。ブランド名（英数字・ハイフン）を入力して「＋ 追加」をクリックします。")
        st.stop()

    st.divider()

    # ── ブランドブリーフ ──────────────────────────────────────────────────
    st.subheader("ブランドブリーフ")
    st.caption("Claude Code でブランドサイトを分析して生成し、ここで確認・編集できます。")

    brief_text = load_brief(selected_brand)
    new_brief = st.text_area(
        "ブリーフ (Markdown)",
        value=brief_text,
        height=320,
        key=f"brief_{selected_brand}",
        label_visibility="collapsed",
    )
    if st.button("💾 ブリーフを保存", key="save_brief"):
        save_brief(selected_brand, new_brief)
        st.success("保存しました")

    st.divider()

    # ── コンテンツプラン ──────────────────────────────────────────────────
    st.subheader("コンテンツプラン")
    st.caption("記事のトピックリストを管理します。Claude Code で生成してここで状態を更新できます。")

    topics = load_content_plan(selected_brand)
    df_topics = (
        pd.DataFrame(topics, columns=["theme", "keyword", "status", "note"])
        if topics
        else pd.DataFrame(columns=["theme", "keyword", "status", "note"])
    )

    edited_topics = st.data_editor(
        df_topics,
        column_config={
            "theme":   st.column_config.TextColumn("テーマ", width="large"),
            "keyword": st.column_config.TextColumn("ターゲットキーワード", width="medium"),
            "status":  st.column_config.SelectboxColumn(
                "状態", options=["未着手", "進行中", "完了"], width="small"
            ),
            "note":    st.column_config.TextColumn("メモ", width="medium"),
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"plan_{selected_brand}",
    )

    if st.button("💾 プランを保存", type="primary", key="save_plan"):
        save_content_plan(selected_brand, edited_topics.to_dict("records"))
        st.success("保存しました")
        st.rerun()

    st.divider()

    # ── 記事生成 ─────────────────────────────────────────────────────────
    st.subheader("記事を生成する")

    pending = [t for t in topics if t.get("status") != "完了"]
    if not pending:
        st.success("すべてのトピックが完了しています 🎉")
    else:
        col_pick, col_btn = st.columns([5, 1])
        with col_pick:
            topic_labels = [
                f"{'🔄' if t['status'] == '進行中' else '⬜'} {t['theme']}"
                for t in pending
            ]
            chosen_idx = st.selectbox(
                "生成するトピックを選択",
                options=range(len(pending)),
                format_func=lambda i: topic_labels[i],
                key="gen_topic_select",
            )
        with col_btn:
            st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
            if st.button("📝 生成", type="primary", use_container_width=True, key="gen_btn"):
                chosen = pending[chosen_idx]
                write_next_task(selected_brand, chosen)
                st.success("準備完了！")
                st.info(
                    f"**Claude Code** のチャットで `次` と入力してください。\n\n"
                    f"📌 **{chosen['theme']}**"
                )
            st.markdown("</div>", unsafe_allow_html=True)

# ── 管理一覧 ──────────────────────────────────────────────────────────────
with tab_list:
    all_drafts = [load_draft(d["path"]) for d in list_drafts()]

    rows = []
    for d in all_drafts:
        appr = d.get("approval") or {}
        rows.append({
            "ブランドURL":    d["source_url"],
            "プレビューURL":  d.get("preview_url") or "",
            "公開URL":        _normalize_published_url(d.get("published_url") or ""),
            "承認":           appr.get("status", "未確認"),
            "確認申請日":     appr.get("requested_date", ""),
            "承認日":         appr.get("approved_date", ""),
            "コメント":       appr.get("comment", ""),
            "_path":          str(d["path"]),
        })

    df = pd.DataFrame(rows)
    display_df = df.drop(columns=["_path"])

    edited = st.data_editor(
        display_df,
        column_config={
            "ブランドURL":   st.column_config.LinkColumn("ブランドURL", width="medium"),
            "プレビューURL": st.column_config.LinkColumn("プレビューURL", width="medium"),
            "公開URL":       st.column_config.LinkColumn("公開URL", width="medium"),
            "承認":          st.column_config.SelectboxColumn(
                                "承認", options=["未確認", "承認", "却下"], width="small"),
            "確認申請日":    st.column_config.TextColumn("確認申請日", width="small"),
            "承認日":        st.column_config.TextColumn("承認日", width="small"),
            "コメント":      st.column_config.TextColumn("コメント", width="large"),
        },
        use_container_width=True,
        hide_index=True,
        key="approval_table",
    )

    col_save, col_dl = st.columns([2, 1])
    with col_save:
        if st.button("💾 一覧を保存", type="primary", use_container_width=True):
            for i, row in edited.iterrows():
                save_approval(
                    df.iloc[i]["_path"],
                    status=row["承認"],
                    requested_date=row["確認申請日"],
                    approved_date=row["承認日"],
                    comment=row["コメント"],
                )
            st.success("保存しました")
            st.rerun()
    with col_dl:
        csv_bytes = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Excelにエクスポート",
            data=csv_bytes,
            file_name="wasabi-blog-管理一覧.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ── 記事編集 ──────────────────────────────────────────────────────────────
with tab_edit:
    new_title = st.text_input("タイトル", value=draft["title"])
    new_body  = st.text_area("本文 (Markdown)", value=draft["body"], height=520)

    if st.button("💾 保存", type="primary"):
        update_content(selected_path, new_title, new_body)
        st.success("保存しました")
        st.rerun()

# ── SEO / CTA ─────────────────────────────────────────────────────────────
with tab_seo:
    seo = draft.get("seo") or {}
    cta = draft.get("cta") or {}

    st.subheader("CTA ボタン")
    c1, c2 = st.columns([3, 2])
    with c1:
        new_cta_url  = st.text_input("URL", value=cta.get("url", ""),
                                     placeholder="https://your-store.myshopify.com/products/...")
    with c2:
        new_cta_text = st.text_input("ボタンテキスト", value=cta.get("text", ""),
                                     placeholder="Shop Now →")

    st.divider()
    st.subheader("SEO")
    new_meta = st.text_input("メタディスクリプション", value=seo.get("meta_description", ""))
    n = len(new_meta)
    st.caption(f"{'🔴' if n > 160 else '🟢'}  {n} / 160 文字")

    kw_str    = ", ".join(seo.get("keywords") or [])
    new_kw    = st.text_input("キーワード (カンマ区切り)", value=kw_str)

    if st.button("💾 保存", type="primary", key="save_seo"):
        update_seo_cta(selected_path, new_cta_url, new_cta_text, new_meta, new_kw)
        st.success("保存しました")
        st.rerun()

# ── プレビュー & 投稿 ─────────────────────────────────────────────────────
with tab_preview:
    fresh = load_draft(selected_path)
    components.html(build_html(fresh), height=780, scrolling=True)

    st.divider()
    col_surge, col_shopify = st.columns(2)

    with col_surge:
        if st.button("🚀 Surge にデプロイ", use_container_width=True):
            with st.spinner("デプロイ中..."):
                ok, url = deploy_surge(fresh, selected_path)
            if ok:
                save_preview_url(selected_path, url)
                st.success("デプロイ完了!")
                st.code(url)
                st.markdown(f"[プレビューを開く →]({url})")
                st.rerun()
            else:
                st.error(f"失敗: {url}")

    with col_shopify:
        if fresh["status"] == "published":
            pub_url = _normalize_published_url(fresh['published_url'])
            st.markdown(f"[Shopify記事を開く →]({pub_url})")
            st.divider()
            if st.button("↩️ 下書きに戻す", use_container_width=True):
                with st.spinner("処理中..."):
                    try:
                        unpublish_article(fresh["published_url"])
                        mark_unpublished(selected_path)
                        st.success("下書きに戻しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")
        else:
            if st.button("📤 Shopify に投稿", type="primary", use_container_width=True):
                with st.spinner("投稿中..."):
                    try:
                        result = publish_to_shopify(fresh, published=True)
                        mark_published(selected_path, result["url"])
                        st.success("投稿完了!")
                        st.markdown(f"[Shopify記事を開く →]({result['url']})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")

    # 画像プレビュー & SNS投稿
    st.divider()
    images = fresh.get("images", [])
    if images:
        st.subheader("🖼️ 画像一覧")
        cols = st.columns(min(len(images), 3))
        for i, img_url in enumerate(images[:6]):
            with cols[i % 3]:
                st.image(img_url, use_container_width=True)

    if fresh["status"] == "published":
        st.subheader("📱 SNS投稿")
        col_fb, col_ig = st.columns(2)
        with col_fb:
            if st.button("📘 Facebookに投稿", use_container_width=True):
                with st.spinner("投稿中..."):
                    try:
                        from sns_publisher import post_to_facebook
                        post_to_facebook(fresh, _normalize_published_url(fresh["published_url"]))
                        st.success("✅ Facebook投稿完了!")
                    except Exception as e:
                        st.error(f"エラー: {e}")
        with col_ig:
            if st.button("📸 Instagramに投稿", use_container_width=True):
                with st.spinner("投稿中..."):
                    try:
                        from sns_publisher import post_to_instagram
                        post_to_instagram(fresh, fresh["published_url"])
                        st.success("✅ Instagram投稿完了!")
                    except Exception as e:
                        st.error(f"エラー: {e}")
