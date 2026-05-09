"""
Google Docs API でブログドラフトを保存する
初回実行時にブラウザでOAuth認証が必要
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GOOGLE_SCOPES, GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE


def _get_credentials() -> Credentials:
    """OAuth2認証を行いCredentialsを返す。"""
    creds = None

    if os.path.exists(GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Google credentials.json が見つかりません: {GOOGLE_CREDENTIALS_FILE}\n"
                    "セットアップ手順:\n"
                    "1. Google Cloud Console → APIs & Services → Credentials\n"
                    "2. 'OAuth 2.0 Client ID' を作成 (Desktop app)\n"
                    "3. credentials.json をダウンロードして shopify_blog_workflow/ に配置"
                )
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)

        with open(GOOGLE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def create_google_doc(blog: dict) -> str:
    """ブログドラフトをGoogle Docとして作成し、URLを返す。"""
    creds = _get_credentials()
    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)

    # ドキュメント作成
    title = blog.get("title", "ブログドラフト")
    doc = docs.documents().create(body={"title": f"[Draft] {title}"}).execute()
    doc_id = doc["documentId"]

    # コンテンツ構築
    content_lines = _build_doc_text(blog)
    full_text = "\n".join(content_lines)

    # テキスト挿入
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": full_text,
            }
        }
    ]

    # スタイル適用（タイトル: Heading1）
    title_end = len(title) + 1  # +1 for newline
    requests.append(
        {
            "updateParagraphStyle": {
                "range": {"startIndex": 1, "endIndex": title_end},
                "paragraphStyle": {"namedStyleType": "HEADING_1"},
                "fields": "namedStyleType",
            }
        }
    )

    docs.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests},
    ).execute()

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    return doc_url


def _build_doc_text(blog: dict) -> list[str]:
    """Google Docに挿入するテキストを構築する。"""
    lines = []

    # タイトル
    lines.append(blog.get("title", "ブログドラフト"))
    lines.append("")

    # メタ情報セクション
    lines.append("━" * 60)
    lines.append("【SEO情報】")
    lines.append(f"メタディスクリプション: {blog.get('meta_description', '')}")
    lines.append(f"SEOキーワード: {', '.join(blog.get('seo_keywords', []))}")
    lines.append(f"タグ: {', '.join(blog.get('tags', []))}")
    lines.append(f"参照URL: {blog.get('source_url', '')}")
    lines.append("━" * 60)
    lines.append("")

    # 本文
    lines.append("【ブログ本文】")
    lines.append("")
    lines.append(blog.get("content", ""))
    lines.append("")

    # 画像プロンプト
    image_prompts = blog.get("image_prompts", [])
    if image_prompts:
        lines.append("━" * 60)
        lines.append("【画像生成プロンプト（DALL-E / Midjourney用）】")
        lines.append("※ 以下のプロンプトで画像を生成し、記事に手動でアップロードしてください")
        lines.append("")
        for i, prompt in enumerate(image_prompts, 1):
            lines.append(f"画像{i}: {prompt}")
        lines.append("")

    # クライアント確認用メモ
    lines.append("━" * 60)
    lines.append("【クライアント確認事項】")
    lines.append("□ タイトルの承認")
    lines.append("□ 本文の内容確認・修正")
    lines.append("□ 画像のアップロード・配置")
    lines.append("□ タグ・カテゴリの確認")
    lines.append("□ 公開日時の設定")
    lines.append("")
    lines.append("承認後、Shopifyへの投稿とSNS配信を実行します。")

    return lines
