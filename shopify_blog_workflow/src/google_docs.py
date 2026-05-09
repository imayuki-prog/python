import os
from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


def _get_service():
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials/google_service_account.json")
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return build("docs", "v1", credentials=creds), build("drive", "v3", credentials=creds)


def create_draft_doc(draft: dict, folder_id: str = None) -> str:
    """ブログ草稿をGoogle Docsに保存してURLを返す"""
    docs_service, drive_service = _get_service()

    # ドキュメント作成
    doc = docs_service.documents().create(body={"title": f"[DRAFT] {draft['title']}"}).execute()
    doc_id = doc["documentId"]

    # 本文を書き込む
    full_text = f"{draft['title']}\n\n{draft['body']}\n\n---\nSource: {draft['source_url']}"
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": full_text,
                    }
                }
            ]
        },
    ).execute()

    # フォルダに移動（指定がある場合）
    if folder_id:
        file = drive_service.files().get(fileId=doc_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents", []))
        drive_service.files().update(
            fileId=doc_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"Google Docs に保存しました: {doc_url}")
    return doc_url
