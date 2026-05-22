#!/usr/bin/env python3
"""
Facebook / Instagram アクセストークンを一度だけ取得するスクリプト。
取得後は .env に以下を追加してください：
  META_ACCESS_TOKEN=（ページアクセストークン）
  FACEBOOK_PAGE_ID=（ページID）
  INSTAGRAM_ACCOUNT_ID=（InstagramアカウントID）
"""
import os
import json
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ["META_APP_ID"]
APP_SECRET = os.environ["META_APP_SECRET"]
REDIRECT_URI = "http://localhost:3000/callback"
SCOPES = "pages_manage_posts,pages_read_engagement,instagram_content_publish"

token_result = {}


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]

        if not code:
            self._respond("❌ エラー: codeが取得できませんでした。")
            return

        # ユーザーアクセストークンを取得
        token_res = requests.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
        )
        data = token_res.json()
        user_token = data.get("access_token")

        if not user_token:
            self._respond(f"❌ エラー: {data}")
            return

        # 長期トークンに交換
        long_res = requests.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "fb_exchange_token": user_token,
            },
        )
        long_token = long_res.json().get("access_token", user_token)

        # ページ一覧を取得
        pages_res = requests.get(
            "https://graph.facebook.com/v19.0/me/accounts",
            params={"access_token": long_token},
        )
        pages = pages_res.json().get("data", [])

        token_result["user_token"] = long_token
        token_result["pages"] = pages

        self._respond("✅ 成功！ブラウザを閉じてターミナルを確認してください。")
        threading.Thread(target=self.server.shutdown).start()

    def _respond(self, message):
        body = f"<h2>{message}</h2>".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def main():
    auth_url = (
        "https://www.facebook.com/dialog/oauth?"
        + urlencode({
            "client_id": APP_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "response_type": "code",
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

    print("\n✅ 取得完了！\n")
    print("=" * 60)

    if not pages:
        print("⚠️  Facebookページが見つかりませんでした。")
        print(f"ユーザートークン: {user_token}")
        return

    for page in pages:
        page_id = page["id"]
        page_name = page["name"]
        page_token = page["access_token"]

        print(f"Facebookページ: {page_name}")
        print(f"FACEBOOK_PAGE_ID={page_id}")
        print(f"META_ACCESS_TOKEN={page_token}")

        # InstagramアカウントIDを取得
        ig_res = requests.get(
            f"https://graph.facebook.com/v19.0/{page_id}",
            params={
                "fields": "instagram_business_account",
                "access_token": page_token,
            },
        )
        ig_data = ig_res.json()
        ig_account = ig_data.get("instagram_business_account", {})
        ig_id = ig_account.get("id")

        if ig_id:
            print(f"INSTAGRAM_ACCOUNT_ID={ig_id}")
        else:
            print("⚠️  InstagramビジネスアカウントがこのFacebookページに連携されていません。")

        print("=" * 60)

    print("\n上記の値を .env に追加してください。")


if __name__ == "__main__":
    main()
