"""Surge.sh へのプレビュー公開・削除を管理する

プレビューURLは推測されないよう末尾にランダムな文字列を付ける。
一度発行したURLはドラフトの preview_url に保存し、再デプロイ時も同じURLを使う。
"""
import re
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

# wasabi-<slug>-<16桁のランダム16進数>.surge.sh
_DOMAIN_RE = re.compile(r"^wasabi-[a-z0-9-]*-[0-9a-f]{16}\.surge\.sh$")

ROBOTS_TXT = "User-agent: *\nDisallow: /\n"
NOINDEX_META = '<meta name="robots" content="noindex, nofollow, noarchive">'


def _host(preview_url) -> str:
    return (urlparse(str(preview_url or "")).hostname or "").lower()


def preview_domain(draft_path: Path, preview_url=None) -> str:
    """保存済みのランダムURLがあればそれを使い、なければ新しく発行する"""
    host = _host(preview_url)
    if _DOMAIN_RE.match(host):
        return host
    # DNS label max = 63 chars: "wasabi-"(7) + slug(30) + "-"(1) + token(16) = 54
    slug = re.sub(r"[^a-z0-9-]", "-", draft_path.stem.lower().replace("_", "-"))
    slug = re.sub(r"-+", "-", slug)[:30].strip("-")
    return f"wasabi-{slug}-{secrets.token_hex(8)}.surge.sh"


def deploy(html: str, domain: str, capture_output: bool = False) -> subprocess.CompletedProcess:
    """HTML と robots.txt を Surge にデプロイする"""
    tmpdir = tempfile.mkdtemp(prefix="wasabi-preview-")
    try:
        (Path(tmpdir) / "index.html").write_text(html, encoding="utf-8")
        (Path(tmpdir) / "robots.txt").write_text(ROBOTS_TXT, encoding="utf-8")
        return subprocess.run(
            ["surge", tmpdir, domain],
            capture_output=capture_output, text=True, timeout=120,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def teardown(preview_url) -> bool:
    """Surge 上のプレビューを削除する（*.surge.sh 以外は何もしない）"""
    host = _host(preview_url)
    if not host.endswith(".surge.sh"):
        return False
    try:
        result = subprocess.run(
            ["surge", "teardown", host],
            capture_output=True, text=True, timeout=60,
        )
    except Exception:
        return False
    return result.returncode == 0


def teardown_if_replaced(old_preview_url, new_domain: str):
    """旧形式（推測可能）のプレビューURLから移行した場合、古いほうを削除する"""
    old_host = _host(old_preview_url)
    if old_host and old_host != new_domain:
        teardown(old_preview_url)
