#!/usr/bin/env python3
"""
Facebook / Instagram アクセストークンを一度だけ取得するスクリプト。
取得した値は画面に表示せず、.env に直接保存します：
  META_ACCESS_TOKEN=（ページアクセストークン）
  META_USER_ACCESS_TOKEN=（長期ユーザーアクセストークン）
  FACEBOOK_PAGE_ID=（ページID）
  INSTAGRAM_ACCOUNT_ID=（InstagramアカウントID）
"""
import hmac
import html
import os
import secrets
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from dotenv import load_dotenv

from token_utils import mask, save_to_env

load_dotenv()

APP_ID = os.environ["META_APP_ID"]
APP_SECRET = os.environ["META_APP_SECRET"]
# ページが /me/accounts で取得できない場合に使うビジネスポートフォリオID（任意）
BUSINESS_ID = os.environ.get("META_BUSINESS_ID", "").strip()
REDIRECT_URI = "http://localhost:3000/callback"
SCOPES = "pages_show_list,pages_manage_posts,pages_read_engagement,instagram_content_publish,business_management"
GRAPH = "https://graph.facebook.com/v19.0"
TIMEOUT = 30

# CSRF 対策: 認証開始時に発行し、コールバックで一致を確認する
STATE = secrets.token_urlsafe(32)

token_result = {}


def _api_error(data: dict) -> str:
    """レスポンスからトークンを含まないエラーメッセージだけを取り出す"""
    error = data.get("error") or {}
    return error.get("message", "不明なエラー") if isinstance(error, dict) else str(error)


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]

        if not hmac.compare_digest(params.get("state", [""])[0], STATE):
            self._respond("❌ エラー: state が一致しません（不正なリクエストの可能性があります）。")
            return

        if not code:
            self._respond("❌ エラー: codeが取得できませんでした。")
            return

        # ユーザーアクセストークンを取得
        token_res = requests.get(
            f"{GRAPH}/oauth/access_token",
            params={
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            timeout=TIMEOUT,
        )
        data = token_res.json()
        user_token = data.get("access_token")

        if not user_token:
            self._respond(f"❌ エラー: {_api_error(data)}")
            return

        # 長期トークンに交換
        long_res = requests.get(
            f"{GRAPH}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "fb_exchange_token": user_token,
            },
            timeout=TIMEOUT,
        )
        long_token = long_res.json().get("access_token", user_token)

        # ページ一覧を取得
        pages_res = requests.get(
            f"{GRAPH}/me/accounts",
            params={"access_token": long_token},
            timeout=TIMEOUT,
        )
        pages = pages_res.json().get("data", [])

        # ビジネスポートフォリオ経由で取得を試みる
        if not pages and BUSINESS_ID:
            biz_res = requests.get(
                f"{GRAPH}/{BUSINESS_ID}/owned_pages",
                params={"access_token": long_token, "fields": "id,name,access_token"},
                timeout=TIMEOUT,
            )
            biz_data = biz_res.json()
            if "error" in biz_data:
                print(f"⚠️  ビジネスポートフォリオからの取得に失敗: {_api_error(biz_data)}")
            pages = biz_data.get("data", [])

        token_result["user_token"] = long_token
        token_result["pages"] = pages

        self._respond("✅ 成功！ブラウザを閉じてターミナルを確認してください。")
        threading.Thread(target=self.server.shutdown).start()

    def _respond(self, message):
        body = f"<h2>{html.escape(str(message))}</h2>".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def _get_instagram_id(page_id: str, page_token: str, user_token: str):
    ig_res = requests.get(
        f"{GRAPH}/{page_id}",
        params={
            "fields": "instagram_business_account",
            "access_token": page_token,
        },
        timeout=TIMEOUT,
    )
    ig_id = ig_res.json().get("instagram_business_account", {}).get("id")

    # ビジネスポートフォリオ経由でInstagramアカウントを取得 (user_token使用)
    if not ig_id and BUSINESS_ID:
        biz_ig_res = requests.get(
            f"{GRAPH}/{BUSINESS_ID}/instagram_accounts",
            params={"access_token": user_token, "fields": "id,username"},
            timeout=TIMEOUT,
        )
        biz_ig_data = biz_ig_res.json().get("data", [])
        if biz_ig_data:
            ig_id = biz_ig_data[0]["id"]

    return ig_id


def _choose_page(pages: list) -> dict:
    if len(pages) == 1:
        return pages[0]
    print("複数のFacebookページが見つかりました。保存するページを選んでください：")
    for i, page in enumerate(pages, 1):
        print(f"  {i}. {page['name']} (ID: {page['id']})")
    while True:
        choice = input("番号: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(pages):
            return pages[int(choice) - 1]


def main():
    auth_url = (
        "https://www.facebook.com/dialog/oauth?"
        + urlencode({
            "client_id": APP_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "response_type": "code",
            "state": STATE,
        })
    )

    print("ブラウザでFacebookの認証ページを開きます...")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 3000), CallbackHandler)
    print("認証待機中... (ブラウザで「許可」をクリックしてください)\n")
    server.serve_forever()

    pages = token_result.get("pages", [])
    user_token = token_result.get("user_token")

    if not user_token:
        print("❌ トークンの取得に失敗しました。")
        return

    values = {"META_USER_ACCESS_TOKEN": user_token}

    if not pages:
        save_to_env(values)
        print("⚠️  Facebookページが見つかりませんでした。")
        print("ユーザートークンのみ .env に保存しました。")
        print(f"META_USER_ACCESS_TOKEN={mask(user_token)}")
        return

    page = _choose_page(pages)
    values["FACEBOOK_PAGE_ID"] = page["id"]
    values["META_ACCESS_TOKEN"] = page["access_token"]

    ig_id = _get_instagram_id(page["id"], page["access_token"], user_token)
    if ig_id:
        values["INSTAGRAM_ACCOUNT_ID"] = ig_id

    save_to_env(values)

    print("\n✅ 取得完了！ 以下の値を .env に保存しました。\n")
    print("=" * 60)
    print(f"Facebookページ: {page['name']}")
    for key, value in values.items():
        shown = value if key.endswith("_ID") else mask(value)
        print(f"{key}={shown}")
    if not ig_id:
        print("⚠️  InstagramビジネスアカウントがこのFacebookページに連携されていません。")
    print("=" * 60)


if __name__ == "__main__":
    main()
