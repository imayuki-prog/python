# shopify_blog_workflow

## Phase 1: URL → Claude → Google Docs

### セットアップ

```bash
cd shopify_blog_workflow

# 依存パッケージをインストール
pip install -r requirements.txt

# .env を作成して編集
cp .env.example .env
```

`.env` を開いて以下を設定：

| 変数 | 内容 |
|------|------|
| `ANTHROPIC_API_KEY` | Claude APIキー（必須） |
| `GOOGLE_CREDENTIALS_PATH` | サービスアカウントJSONのパス（必須） |
| `GOOGLE_DRIVE_FOLDER_ID` | 保存先Driveフォルダーのid（任意） |
| `BLOG_WORD_COUNT` | 生成する記事の目標語数（デフォルト: 800） |

### Google API 認証設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. **Google Docs API** と **Google Drive API** を有効化
3. サービスアカウントを作成し、JSONキーをダウンロード
4. JSONファイルを `credentials/google_service_account.json` に配置
5. 保存先のGoogle Driveフォルダーをサービスアカウントのメールアドレスと共有

### 実行方法

```bash
# インタラクティブ
python main.py

# URLを直接指定
python main.py https://example.com/article
```

---

## ロードマップ

- **Phase 1** ✅ URL → Claude → Google Docs
- **Phase 2** クライアント承認フロー
- **Phase 3** 画像セレクト
- **Phase 4** Shopify に HTML で自動投稿
- **Phase 5** Facebook / Instagram への自動投稿
