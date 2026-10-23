#!/usr/bin/env python3
"""
Shopify OAuthトークンを一度だけ取得するスクリプト。
取得したトークンは画面に表示せず、.env の SHOPIFY_ACCESS_TOKEN に直接保存します。
"""
import html
import os
import hashlib
import hmac
import re
import secrets
import sys
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qsl, urlencode
import requests
from dotenv import load_dotenv

from token_utils import mask, save_to_env

load_dotenv()

STORE = os.environ["SHOPIFY_STORE"].strip().lower()
CLIENT_ID = os.environ["SHOPIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SHOPIFY_CLIENT_SECRET"]
SCOPES = "write_content,read_content"
REDIRECT_URI = "http://localhost:3000/callback"

# 認可コードとClient Secretを別のホストに送らないよう、ストアのドメイン形式を限定する
if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.myshopify\.com", STORE):
    sys.exit(f"SHOPIFY_STORE は xxx.myshopify.com の形式で指定してください: {STORE}")

# CSRF 対策: 認証開始時に発行し、コールバックで一致を確認する
STATE = secrets.token_urlsafe(32)

token_result = {}


def _verify_hmac(params: dict) -> bool:
    """Shopify から届いたコールバックであることを HMAC 署名で確認する"""
    received = params.get("hmac", "")
    message = "&".join(
        f"{k.replace('%', '%25').replace('=', '%3D').replace('&', '%26')}"
        f"={v.replace('%', '%25').replace('&', '%26')}"
        for k, v in sorted(params.items())
        if k not in ("hmac", "signature")
    )
    digest = hmac.new(CLIENT_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    return bool(received) and hmac.compare_digest(digest, received)


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        code = params.get("code")

        if not hmac.compare_digest(params.get("state", ""), STATE):
            self._respond("❌ エラー: state が一致しません（不正なリクエストの可能性があります）。")
            return
        if params.get("shop", "").lower() != STORE:
            self._respond("❌ エラー: shop が設定中のストアと一致しません。")
            return
        if not _verify_hmac(params):
            self._respond("❌ エラー: HMAC 署名の検証に失敗しました。")
            return
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
            timeout=30,
        )
        data = resp.json()
        token = data.get("access_token")

        if token:
            token_result["token"] = token
            self._respond("✅ 成功！ブラウザを閉じてターミナルを確認してください。")
        else:
            error = data.get("error_description") or data.get("error") or f"HTTP {resp.status_code}"
            self._respond(f"❌ エラー: {error}")

        threading.Thread(target=self.server.shutdown).start()

    def _respond(self, message):
        body = f"<h2>{html.escape(str(message))}</h2>".encode()
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
            "state": STATE,
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
        save_to_env({"SHOPIFY_ACCESS_TOKEN": token})
        print("\n✅ アクセストークンを取得し、.env に保存しました。")
        print(f"SHOPIFY_ACCESS_TOKEN={mask(token)}")
    else:
        print("\n❌ トークンの取得に失敗しました。")


if __name__ == "__main__":
    main()
