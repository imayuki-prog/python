# SMS 2FA → メール転送の設定方法

SMSで2FAが届く場合は、まずSMSをメールに転送する設定が必要です。

## 方法1: キャリアのSMS→メール転送（無料）

多くのキャリアはSMSをメール転送できます。

| キャリア (US) | 転送アドレス形式 |
|---|---|
| AT&T | `電話番号@txt.att.net` |
| T-Mobile | `電話番号@tmomail.net` |
| Verizon | `電話番号@vtext.com` |
| Sprint | `電話番号@messaging.sprintpcs.com` |

**設定**: 相手がそのメールアドレスにSMSを送ると、あなたのメール受信箱に届きます。

## 方法2: Google Voice（推奨）

1. [voice.google.com](https://voice.google.com) で無料番号取得
2. 設定 → メッセージ → 「メールでSMSを転送」を有効化
3. AmazonやWalmartの2FA電話番号をGoogle Voice番号に変更
4. SMSが自動でGmailに転送される

## 方法3: Twilio（API連携・有料）

Twilioの仮想番号を使えば、SMSをPythonで直接受信できます。

```python
# pip install twilio flask
from flask import Flask, request

app = Flask(__name__)

@app.route("/sms", methods=["POST"])
def receive_sms():
    body = request.form["Body"]
    print(f"SMS received: {body}")
    # OTPを抽出してDBや一時ファイルに保存
    return "", 204
```

Twilioコンソールで受信URLに `http://あなたのサーバー/sms` を設定します。

## 推奨構成

```
AmazonのSMS → Google Voice番号 → Gmail転送 → otp_fetcher.py で自動取得
```

この構成が最も簡単で無料です。
