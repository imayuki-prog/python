"""ドラフト（.md）の保存・読み込み・一覧表示を管理する"""
import re
from datetime import date
from pathlib import Path

import yaml

DRAFTS_DIR = Path(__file__).parent / "drafts"


def _slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:60]


def save_draft(title: str, body: str, source_url: str, images: list, seo: dict = None) -> Path:
    """ドラフトを drafts/<date>_<slug>.md に保存して Path を返す"""
    DRAFTS_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()
    slug = _slugify(title)
    filepath = DRAFTS_DIR / f"{today}_{slug}.md"

    meta = {
        "status": "draft",
        "source_url": source_url,
        "images": images[:5],
        "created": today,
        "published_url": None,
        "cta": {
            "url": "",
            "text": "",
        },
        "preview_url": None,
        "approval": {
            "status": "未確認",
            "requested_date": "",
            "approved_date": "",
            "comment": "",
        },
        "seo": seo or {
            "meta_description": "",
            "keywords": [],
            "image_alts": [],
        },
    }

    content = (
        f"---\n{yaml.dump(meta, default_flow_style=False, allow_unicode=True)}---\n\n"
        f"# {title}\n\n{body}"
    )
    filepath.write_text(content, encoding="utf-8")
    return filepath


def load_draft(path) -> dict:
    """ドラフトファイルを読み込んで dict を返す"""
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError(f"フロントマターが見つかりません: {path}")

    meta = yaml.safe_load(match.group(1))
    body = match.group(2).strip()

    lines = body.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    body_without_title = "\n".join(lines[1:]).strip() if len(lines) > 1 else body

    return {
        "title": title,
        "body": body_without_title,
        "full_text": body,
        "source_url": meta.get("source_url", ""),
        "images": meta.get("images") or [],
        "status": meta.get("status", "draft"),
        "created": meta.get("created"),
        "published_url": meta.get("published_url"),
        "seo": meta.get("seo") or {"meta_description": "", "keywords": [], "image_alts": []},
        "cta": meta.get("cta") or {"url": "", "text": ""},
        "preview_url": meta.get("preview_url"),
        "approval": meta.get("approval") or {
            "status": "未確認", "requested_date": "", "approved_date": "", "comment": ""
        },
        "path": path,
    }


def mark_published(path, published_url: str):
    """ドラフトのステータスを published に更新する"""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"status: draft", "status: published", text)
    text = re.sub(r"published_url: null", f"published_url: {published_url}", text)
    path.write_text(text, encoding="utf-8")


def mark_unpublished(path):
    """ドラフトのステータスを draft に戻す"""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"status: published", "status: draft", text)
    path.write_text(text, encoding="utf-8")


def save_preview_url(path, preview_url: str):
    """Surge のプレビューURLをドラフトに保存する"""
    path = Path(path)
    meta, body = _load_raw(path)
    meta["preview_url"] = preview_url
    path.write_text(
        f"---\n{yaml.dump(meta, default_flow_style=False, allow_unicode=True)}---\n{body}",
        encoding="utf-8",
    )


def save_approval(path, status: str, requested_date: str, approved_date: str, comment: str):
    """承認情報をドラフトに保存する"""
    path = Path(path)
    meta, body = _load_raw(path)
    meta["approval"] = {
        "status": status,
        "requested_date": requested_date,
        "approved_date": approved_date,
        "comment": comment,
    }
    path.write_text(
        f"---\n{yaml.dump(meta, default_flow_style=False, allow_unicode=True)}---\n{body}",
        encoding="utf-8",
    )


def _load_raw(path: Path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    return yaml.safe_load(match.group(1)), match.group(2)


def list_drafts() -> list:
    """drafts/ 内の全 .md ファイルを一覧で返す"""
    if not DRAFTS_DIR.exists():
        return []
    results = []
    for f in sorted(DRAFTS_DIR.glob("*.md")):
        try:
            d = load_draft(f)
            results.append({
                "path": f,
                "title": d["title"],
                "status": d["status"],
                "created": d["created"],
                "published_url": d["published_url"],
            })
        except Exception:
            pass
    return results
