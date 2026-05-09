import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from blog_generator import BlogPost
import config


def get_credentials() -> Credentials:
    creds = None

    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(config.CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"credentials.json が見つかりません: {config.CREDENTIALS_FILE}\n"
                    "Google Cloud Console からダウンロードして配置してください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CREDENTIALS_FILE, config.SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(config.TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def save_to_google_docs(blog: BlogPost) -> str:
    creds = get_credentials()
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    doc = docs_service.documents().create(body={"title": blog.title}).execute()
    doc_id = doc["documentId"]

    separator = "\n" + "─" * 40 + "\n"
    full_text = (
        f"{blog.title}\n\n"
        f"【メタディスクリプション】\n{blog.meta_description}\n\n"
        f"【タグ】\n{', '.join(blog.tags)}\n"
        f"{separator}"
        f"{blog.body}"
    )

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

    _apply_heading_style(docs_service, doc_id, blog.title)

    if config.GOOGLE_DOCS_FOLDER_ID:
        drive_service.files().update(
            fileId=doc_id,
            addParents=config.GOOGLE_DOCS_FOLDER_ID,
            removeParents="root",
        ).execute()

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    return doc_url


def _apply_heading_style(docs_service, doc_id: str, title: str) -> None:
    title_len = len(title)
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": 1, "endIndex": title_len + 1},
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "fields": "namedStyleType",
                    }
                }
            ]
        },
    ).execute()
