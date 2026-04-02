import jwt
import time
import requests
from cryptography.hazmat.primitives import serialization

# --- 設定値 ---
username = 'conn_test@thinkerdn.net'
# consumer_key = '3MVG9HtWXcDGV.nEIQERv68uqfXcPAvD.uUACicp1wEcD6s9U54eKfKi3Ijz9S8iZMiaSKW4mY6mFw16FffGd'
consumer_key = '3MVG9HtWXcDGV.nEIQERv68uqfRaaJag3_LzlSUyLGPzOUqAWAVpBPKABo7QeFDRyrXIltqlaeZ.hgyDMt.QM'
key_file = 'sf-dev.key'  # 秘密鍵ファイルへのパス
token_url = "https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com/services/oauth2/token"
# token_url = 'https://login.salesforce.com/services/oauth2/token' # 本番環境
# token_url = 'https://test.salesforce.com/services/oauth2/token' # Sandbox

# --- 1. 秘密鍵の読み込み ---
with open(key_file, 'rb') as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

# --- 2. JWTの生成 ---
payload = {
    'iss': consumer_key,
    'sub': username,
    'aud': 'https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com', # 本番: login.salesforce.com, Sandbox: test.salesforce.com
    'exp': int(time.time()) + 300  # 5分間有効
}
assertion = jwt.encode(payload, private_key, algorithm='RS256')
print(f"assertion: {assertion}")

# --- 3. アクセストークンの取得 ---
params = {
    'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
    'assertion': assertion
}
response = requests.post(token_url, data=params)
print(f"Response Status: {response.status_code}")
print(f"Response Body: {response.text}")
response.raise_for_status()
access_token = response.json()['access_token']
instance_url = response.json()['instance_url']

print(f"Token: {access_token}")
print(f"Instance URL: {instance_url}")
