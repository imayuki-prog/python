"""
Walmart在庫監視スクリプト。
在庫が閾値以下になったらメール/Slackで通知します。

使い方:
    python monitor.py               # 一回チェックして終了
    python monitor.py --watch 30    # 30分おきに繰り返し監視

環境変数: .env.exampleを参照
"""

import os
import sys
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv  # pip install python-dotenv

from walmart_api import WalmartAPIClient
from notifier import build_notifier_from_env


load_dotenv()


def check_inventory(client: WalmartAPIClient, threshold: int = 0) -> list[dict]:
    """
    全SKUの在庫をチェックし、threshold以下のものを返す。
    threshold=0 → 在庫ゼロのみ通知
    threshold=5 → 5個以下で通知
    """
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 在庫チェック中...")
    skus = client.get_all_skus()
    print(f"  {len(skus)}件のSKUを取得")

    low_stock = []
    for item in client.get_inventory_bulk(skus):
        qty = item.get("quantity")
        if qty is None:
            print(f"  WARNING: {item['sku']} の取得エラー - {item.get('error')}")
            continue
        if qty <= threshold:
            low_stock.append(item)
            print(f"  ⚠ {item['sku']}: 在庫 {qty}")

    return low_stock


def build_alert_message(low_stock: list[dict], threshold: int) -> tuple[str, str]:
    """アラートメール/Slackメッセージを生成する。"""
    zero = [i for i in low_stock if i["quantity"] == 0]
    low  = [i for i in low_stock if 0 < i["quantity"] <= threshold]

    lines = [f"Walmart在庫アラート ({datetime.now():%Y-%m-%d %H:%M:%S})\n"]

    if zero:
        lines.append(f"【在庫ゼロ】{len(zero)}件")
        for item in zero:
            lines.append(f"  SKU: {item['sku']}  数量: 0")

    if low and threshold > 0:
        lines.append(f"\n【在庫少】{len(low)}件 (閾値: {threshold})")
        for item in low:
            lines.append(f"  SKU: {item['sku']}  数量: {item['quantity']}")

    subject = f"[Walmart在庫アラート] {len(zero)}件ゼロ / {len(low)}件少"
    body = "\n".join(lines)
    return subject, body


def run_once(client: WalmartAPIClient, threshold: int, dry_run: bool = False):
    low_stock = check_inventory(client, threshold)

    if not low_stock:
        print("  すべて在庫あり。アラートなし。")
        return

    subject, body = build_alert_message(low_stock, threshold)
    print(f"\n{body}")

    if dry_run:
        print("\n[DRY RUN] 通知は送信しません。")
        return

    try:
        notifier = build_notifier_from_env()
        notifier.send(subject, body)
        print("通知を送信しました。")
    except Exception as e:
        print(f"通知送信エラー: {e}")


def run_watch(client: WalmartAPIClient, threshold: int, interval_minutes: int):
    print(f"監視モード開始 (チェック間隔: {interval_minutes}分, 在庫閾値: {threshold})")
    while True:
        try:
            run_once(client, threshold)
        except Exception as e:
            print(f"チェックエラー: {e}")
        print(f"次回チェック: {interval_minutes}分後\n")
        time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description="Walmart在庫監視")
    parser.add_argument("--watch", type=int, metavar="MINUTES",
                        help="継続監視モード（指定分おきに繰り返し）")
    parser.add_argument("--threshold", type=int, default=0,
                        help="アラートを出す在庫数の閾値（デフォルト: 0=ゼロのみ）")
    parser.add_argument("--dry-run", action="store_true",
                        help="通知を送らずチェックのみ実行")
    args = parser.parse_args()

    client_id     = os.environ.get("WALMART_CLIENT_ID")
    client_secret = os.environ.get("WALMART_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("エラー: WALMART_CLIENT_ID と WALMART_CLIENT_SECRET を設定してください。")
        sys.exit(1)

    client = WalmartAPIClient(client_id, client_secret)

    if args.watch:
        run_watch(client, args.threshold, args.watch)
    else:
        run_once(client, args.threshold, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
