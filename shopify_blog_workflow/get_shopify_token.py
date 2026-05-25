#!/usr/bin/env python3
"""
Shopify OAuthトークンを一度だけ取得するスクリプト。
取得後は .env に SHOPIFY_ACCESS_TOKEN を追加してください。
"""
import os
import hashlib
import hmac
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from dotenv import load_dotenv

load_dotenv()

STORE = os.environ["SHOPIFY_STORE"]
CLIENT_ID = os.environ["SHOPIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SHOPIFY_CLIENT_SECRET"]
SCOPES = "write_content,read_content"
REDIRECT_URI = "http://localhost:3000/callback"

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
            self._respond("エラー: codeが取得できませんでした。")
            return

        # コードをアクセストークンに交換
        resp = requests.post(
            f"https://{STORE}/admin/oauth/access_token",
            json={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
            },
        )
        data = resp.json()
        token = data.get("access_token")

        if token:
            token_result["token"] = token
            self._respond(f"✅ 成功！ブラウザを閉じてターミナルを確認してください。")
        else:
            self._respond(f"❌ エラー: {data}")

        threading.Thread(target=self.server.shutdown).start()

    def _respond(self, message):
        body = f"<h2>{message}</h2>".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # ログ出力を抑制


def main():
    auth_url = (
        f"https://{STORE}/admin/oauth/authorize?"
        + urlencode({
            "client_id": CLIENT_ID,
            "scope": SCOPES,
            "redirect_uri": REDIRECT_URI,
        })
    )

    print("ブラウザでShopifyの認証ページを開きます...")
    print(f"URL: {auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 3000), CallbackHandler)
    print("認証待機中... (ブラウザで「インストール」をクリックしてください)")
    server.serve_forever()

    token = token_result.get("token")
    if token:
        print(f"\n✅ アクセストークンが取得できました！\n")
        print(f"SHOPIFY_ACCESS_TOKEN={token}\n")
        print(".env に上記を追加してください。")
    else:
        print("\n❌ トークンの取得に失敗しました。")


if __name__ == "__main__":
    main()
