"""OAuth トークン取得スクリプト共通の処理（.env への保存・表示用マスク）"""
import os
from pathlib import Path

from dotenv import set_key

ENV_PATH = Path(__file__).parent / ".env"


def mask(value: str) -> str:
    """画面表示用に末尾4文字以外を伏せる"""
    value = str(value or "")
    return "****" if len(value) <= 8 else f"{'*' * 8}{value[-4:]}"


def save_to_env(values: dict):
    """値を .env に書き込み、本人以外が読めないよう権限を 600 にする"""
    ENV_PATH.touch(mode=0o600, exist_ok=True)
    for key, value in values.items():
        set_key(str(ENV_PATH), key, str(value), quote_mode="never")
    # set_key は一時ファイル経由で書き換えるため、最後に権限を付け直す
    os.chmod(ENV_PATH, 0o600)
