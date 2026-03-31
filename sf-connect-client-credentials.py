import requests
import jwt
import time
import base64
import json

# --- 設定値 ---
# OAuth グラントタイプ: Client Credentials
client_id = '3MVG9HtWXcDGV.nEIQERv68uqfeoto.hXr79io4W6pyO4DFXgnRRXmDFegJ70U0G7tj54wr5NsFAcenrr83wp'  # コンシューマ鍵
client_secret = '245C545D423DB3D770CE104B02B9DE6D81BBF41F802413FEE84B724B88359C70'  # コンシューマの秘密
token_url = 'https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com/services/oauth2/token'  # トークンエンドポイント

# 本番環境の場合は以下を使用
# token_url = 'https://login.salesforce.com/services/oauth2/token'

# Sandbox環境の場合は以下を使用
# token_url = 'https://test.salesforce.com/services/oauth2/token'

print("="*70)
print("=== AppFlow用 Client Credentials設定情報 ===")
print("="*70)
print("\nAppFlowでSalesforce接続を作成する際に、以下の情報を使用してください:\n")
print(f"【認証方式】")
print(f"  OAuth 2.0 Client Credentials\n")
print(f"【クライアント ID (Consumer Key)】")
print(f"  {client_id}\n")
print(f"【クライアントシークレット (Consumer Secret)】")
print(f"  {client_secret}\n")
print(f"【トークンエンドポイント (Token URL)】")
print(f"  {token_url}\n")
print(f"【重要な注意事項】")
print(f"  1. AppFlowの設定で、トークンURLを正しく指定してください")
print(f"  2. Developer Edition環境の場合、カスタムドメインURLを使用")
print(f"  3. Salesforce側でClient Credentials方式が有効になっている必要があります")
print(f"  4. 接続アプリケーション(Connected App)の設定を確認してください:")
print(f"     - 「OAuth設定の有効化」がチェックされている")
print(f"     - 「Client Credentials Flow」が有効になっている")
print(f"     - 適切なスコープが設定されている")
print("="*70)

# --- 1. JWT形式のトークンを生成（参考用） ---
jwt_payload = {
    'iss': client_id,  # Issuer: クライアントID
    'aud': 'https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com',  # Audience: Salesforce組織
    'sub': client_id,  # Subject: クライアントID（Client Credentialsの場合）
    'iat': int(time.time()),  # Issued At
    'exp': int(time.time()) + 30000,  # Expiration: 長めに設定
    'client_id': client_id,
    'client_secret': client_secret
}

# JWTトークンを生成（参考用 - HS256でclient_secretを使用）
jwt_token = jwt.encode(jwt_payload, client_secret, algorithm='HS256')

print("\n" + "="*70)
print("=== JWT Token（参考情報） ===")
print("="*70)
print(f"JWT Token: {jwt_token}")
print(f"\nJWT Payload:")
print(json.dumps(jwt_payload, indent=2, ensure_ascii=False))

# --- 2. アクセストークンの取得（Client Credentials方式） ---
params = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret
}

print("\n" + "="*50)
print("Requesting access token using Client Credentials...")
response = requests.post(token_url, data=params)
print(f"Response Status: {response.status_code}")
print(f"Response Body: {response.text}")

# エラーチェック（エラーでも続行）
if response.status_code == 200:
    # レスポンスからトークン情報を取得
    token_data = response.json()
    access_token = token_data['access_token']
    instance_url = token_data['instance_url']

    print("\n--- 認証成功 ---")
    print(f"Access Token: {access_token}")
    print(f"Instance URL: {instance_url}")
else:
    print("\n--- 認証失敗 ---")
    print("注意: Client Credentials方式が有効になっていない可能性があります。")
    print("上記のJWTトークンをAppFlowで使用してください。")
    access_token = None
    instance_url = None

# --- 3. (オプション) APIリクエストの例 ---
if access_token and instance_url:
    # 取得したトークンを使用してSalesforce APIにアクセス
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # 例: REST APIバージョン情報の取得
    api_response = requests.get(f"{instance_url}/services/data/", headers=headers)
    if api_response.status_code == 200:
        print("\n--- API接続テスト成功 ---")
        versions = api_response.json()
        if versions:
            latest_version = versions[-1]
            print(f"Latest API Version: {latest_version['version']}")
            print(f"API URL: {latest_version['url']}")
    else:
        print(f"\nAPI接続テスト失敗: {api_response.status_code}")
        print(f"Response: {api_response.text}")
