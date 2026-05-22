"""ブランドブリーフ・コンテンツプランのファイル管理"""
from pathlib import Path

import yaml

BRANDS_DIR = Path(__file__).parent / "brands"
TASK_FILE = Path(__file__).parent / "_next_task.txt"


def list_brands() -> list[str]:
    BRANDS_DIR.mkdir(exist_ok=True)
    return sorted([d.name for d in BRANDS_DIR.iterdir() if d.is_dir()])


def get_brand_dir(slug: str) -> Path:
    return BRANDS_DIR / slug


def create_brand(slug: str):
    brand_dir = get_brand_dir(slug)
    brand_dir.mkdir(parents=True, exist_ok=True)
    brief_path = brand_dir / "brief.md"
    plan_path = brand_dir / "content_plan.yaml"
    if not brief_path.exists():
        brief_path.write_text(
            "# ブランドブリーフ\n\n"
            "## ブランド概要\n\n"
            "## 主力商品\n\n"
            "## ターゲット顧客（US）\n\n"
            "## コンテンツの柱\n\n"
            "## トーン & NG表現\n\n"
            "## 競合との差別化\n",
            encoding="utf-8",
        )
    if not plan_path.exists():
        plan_path.write_text(
            yaml.dump({"topics": []}, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )


def load_brief(slug: str) -> str:
    path = get_brand_dir(slug) / "brief.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def save_brief(slug: str, content: str):
    path = get_brand_dir(slug) / "brief.md"
    path.write_text(content, encoding="utf-8")


def load_content_plan(slug: str) -> list[dict]:
    path = get_brand_dir(slug) / "content_plan.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    topics = data.get("topics") or []
    # 必須フィールドを保証
    for t in topics:
        t.setdefault("theme", "")
        t.setdefault("keyword", "")
        t.setdefault("status", "未着手")
        t.setdefault("note", "")
    return topics


def write_next_task(slug: str, topic: dict):
    """_next_task.txt に記事生成タスクを書き出す"""
    brief = load_brief(slug)

    # ブリーフからブランドURLを抽出
    brand_url = ""
    for line in brief.splitlines():
        if line.startswith("**Website:**"):
            brand_url = line.replace("**Website:**", "").strip()
            break

    content = (
        f"wasabi-blog 記事生成タスク\n"
        f"{'=' * 40}\n\n"
        f"ブランド: {slug}\n"
        f"ブランドサイト: {brand_url}\n"
        f"テーマ: {topic['theme']}\n"
        f"キーワード: {topic['keyword']}\n"
        f"メモ: {topic.get('note', '')}\n\n"
        f"## 手順\n"
        f"1. brands/{slug}/brief.md を読む（ブランド理解）\n"
        f"2. ブランドサイトの関連ページをスクレイプして素材を収集\n"
        f"3. CLAUDE.md の Article Structure に従って英語記事を生成\n"
        f"4. drafts/YYYY-MM-DD_slug.md として保存\n"
        f"5. 完了後、brands/{slug}/content_plan.yaml の該当トピックの status を「完了」に更新\n\n"
        f"## ブランドブリーフ（参考）\n"
        f"{brief}\n"
    )
    TASK_FILE.write_text(content, encoding="utf-8")


def save_content_plan(slug: str, topics: list[dict]):
    path = get_brand_dir(slug) / "content_plan.yaml"
    cleaned = [
        {
            "theme": str(t.get("theme") or ""),
            "keyword": str(t.get("keyword") or ""),
            "status": str(t.get("status") or "未着手"),
            "note": str(t.get("note") or ""),
        }
        for t in topics
        if t.get("theme")  # 空行は保存しない
    ]
    path.write_text(
        yaml.dump({"topics": cleaned}, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
