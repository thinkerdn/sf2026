import jwt
import time
import requests
from cryptography.hazmat.primitives import serialization

# --- 設定値 ---
username = 'data.renkei@f.flect.co.jp.salesdxpjt.fldevcrm'
consumer_key = '3MVG96vIeT8jJWjKWnpDfYnzfJcAZElDNcNWeQlUWpj_UrZllv0ID7LciPDLG6wctBdQ5kKHeg4wxEFj7iJQG'
key_file = 'sf-dev.key'  # 秘密鍵ファイルへのパス
token_url = "https://dd500000bpcm3eaf--fldevcrm.sandbox.my.salesforce.com/services/oauth2/token"
# token_url = 'https://login.salesforce.com/services/oauth2/token' # 本番環境
# token_url = 'https://test.salesforce.com/services/oauth2/token' # Sandbox

# --- 1. 秘密鍵の読み込み ---
with open(key_file, 'rb') as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

# --- 2. JWTの生成 ---
payload = {
    'iss': consumer_key,
    'sub': username,
    'aud': 'https://dd500000bpcm3eaf--fldevcrm.sandbox.my.salesforce.com', # 本番: login.salesforce.com, Sandbox: test.salesforce.com
    'exp': 1807259693 # int(time.time()) + 60 * 60 * 24 * 365  # 1年間有効
}
assertion = jwt.encode(payload, private_key, algorithm='RS256')
print(f"exp: {int(time.time()) + 60 * 60 * 24 * 365}")
print(f"assertion: {assertion}")

# --- 3. アクセストークンの取得 ---
# exp: 1807259812
# assertion: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzTVZHOTZ2SWVUOGpKV2pLV25wRGZZbnpmSmNBWkVsRE5jTldlUWxVV3BqX1VyWmxsdjBJRDdMY2lQRExHNndjdEJkUTVrS0hlZzR3eEVGajdpSlFHIiwic3ViIjoiZGF0YS5yZW5rZWlAZi5mbGVjdC5jby5qcC5zYWxlc2R4cGp0LmZsZGV2Y3JtIiwiYXVkIjoiaHR0cHM6Ly9kZDUwMDAwMGJwY20zZWFmLS1mbGRldmNybS5zYW5kYm94Lm15LnNhbGVzZm9yY2UuY29tIiwiZXhwIjoxODA3MjU5NjkzfQ.Gu7DIQ4eUgJVrKWVwpUgzlP08HPO5_qFpfuhdiRWCfOmcoE1NGNJf1irlkgimcX0uBg-RSJjBPJ8U4-PchBzXwO8vkwSMGoW8z0DmHVFGkMHKwqqoyKX9sKQX75T7URoGX-KluXU0p4KskO0WuE5Rk0mI0Pl1k0OQ7gMYwu2CG_rHknqoEHACM3OEZpEes2fmv7A-cobfZQAv6Ab41as29A8AI021qYxKHflnrMnMljY0OhYhFPnV9cOAmU2qq0G6fwCXwpQJQ7PuOtBS4eGX7vy2yaYxyZ5oe4EOFyyfiN_1RtbM0SnqPuZrczCxiLQoTPsOsRImEAd8rzYhqN8pA