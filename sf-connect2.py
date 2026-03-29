import jwt
import time
import requests
from cryptography.hazmat.primitives import serialization

# --- 設定値 ---
username = 'data.renkei@f.flect.co.jp.salesdxpjt.fldevcrm'
consumer_key = '3MVG96vIeT8jJWjKWnpDfYnzfJQVTuNk01izNssLf86jiSZoDnJb72NTCi_.NdmXPDkJWWzc3qw1KVTuFeNSo'
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
    'exp': 1775047037  # 5分間有効
}
assertion = jwt.encode(payload, private_key, algorithm='RS256')
print(f"exp: {int(time.time()) + 300000}")
print(f"assertion: {assertion}")

# --- 3. アクセストークンの取得 ---
