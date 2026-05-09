import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Google Docs OAuth
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]
GOOGLE_CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
GOOGLE_TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

# Phase 2: Shopify
SHOPIFY_SHOP_URL = os.getenv("SHOPIFY_SHOP_URL")
SHOPIFY_ADMIN_API_TOKEN = os.getenv("SHOPIFY_ADMIN_API_TOKEN")

# Phase 3: Meta
META_PAGE_ACCESS_TOKEN = os.getenv("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.getenv("META_PAGE_ID")
META_INSTAGRAM_ACCOUNT_ID = os.getenv("META_INSTAGRAM_ACCOUNT_ID")
