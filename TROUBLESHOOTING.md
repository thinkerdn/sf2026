# Salesforce Client Credentials Lambda - トラブルシューティングガイド

## エラー: AppFlowで「invalid_client_id」/ "コンシューマキーパラメーターがありません"

### 問題の説明

```
エラー: invalid_client_id
Salesforceログイン履歴: 失敗：コンシューマキーパラメーターがありません
```

このエラーは、`sf-connect-t.py`などで生成されたJWTトークンをAppFlowで直接使用しようとした際に発生します。

### 原因

**AppFlowはJWTトークンを直接受け付けません。**

AppFlowの認証方式：
- OAuth 2.0フローを使用
- Consumer Key（Client ID）とConsumer Secret（Client Secret）を設定
- AppFlowが自動的にトークンを取得・管理

JWT Bearer認証（sf-connect-t.py）：
- JWTトークンを生成してSalesforceに送信
- アクセストークンを取得
- 主にサーバー間通信で使用

### 解決方法

#### 方法1: Salesforce標準コネクタを使用【最も簡単・推奨】

1. **AppFlow Console → Connections → Create connection**
2. **Salesforceを選択**
3. **接続情報の入力**
   ```
   Connection name: salesforce-oauth-connection
   Environment: Sandbox（または Production）
   ```
4. **OAuth認証**
   - 「Connect」をクリック
   - Salesforceログイン画面でユーザーでログイン
   - 「許可」をクリック
5. **フローの作成**
   - Flows → Create flow
   - Source: Salesforce
   - Connection: salesforce-oauth-connection

#### 方法2: JWT Bearer用のカスタムコネクタを作成

JWT Bearer認証を使用する場合は、カスタムコネクタ（Lambda関数）を作成する必要があります。

1. **Lambda関数を作成**
   - JWT Bearer認証ロジックを実装
   - 環境変数に認証情報を設定：
     - SALESFORCE_USERNAME
     - SALESFORCE_CONSUMER_KEY
     - SALESFORCE_PRIVATE_KEY
     - SALESFORCE_TOKEN_URL
     - SALESFORCE_AUDIENCE

2. **AppFlowカスタムコネクタを登録**
   - AppFlow Console → Connectors → Create custom connector
   - Lambda関数を選択

3. **接続プロファイルを作成**
   - Connections → Create connection
   - カスタムコネクタを選択

詳細な実装方法は `SOLUTION_APPFLOW_JWT_ERROR.md` を参照してください。

#### 方法3: Client Credentials方式のカスタムコネクタを使用

既存の `lambda_appflow_connector.py` を使用：

```bash
# デプロイ
sam build -t template-appflow.yaml
sam deploy -t template-appflow.yaml --guided

# 環境変数に設定:
# SALESFORCE_CLIENT_ID: Consumer Key
# SALESFORCE_CLIENT_SECRET: Consumer Secret
# SALESFORCE_TOKEN_URL: Token URL
```

### 重要なポイント

❌ **間違った方法**:
```
AppFlowに直接JWTトークンを入力
→ AppFlowはJWTトークンを直接受け付けません
```

✅ **正しい方法**:
```
1. Salesforce標準コネクタでOAuth認証を使用
2. カスタムコネクタ（Lambda）でJWT認証を実装
3. Consumer KeyとSecretをLambda環境変数に設定
```

### 関連ドキュメント

- `SOLUTION_APPFLOW_JWT_ERROR.md` - 詳細な解決方法とサンプルコード
- `README_APPFLOW.md` - AppFlowカスタムコネクタの使用方法

---

## エラー: "user hasn't approved this consumer"

### 問題の説明

```
Response Status: 400
Response Body: {"error":"invalid_grant","error_description":"user hasn't approved this consumer"}
```

このエラーは、JWT Bearer認証フロー（`sf-connect.py`）を使用する際に発生します。

### 原因

Salesforceの接続アプリケーション（Connected App）に対して、指定されたユーザーが承認を行っていないことが原因です。JWT Bearer認証では、ユーザーが事前に接続アプリケーションを承認する必要があります。

### 解決方法

#### 方法1: 事前承認（Pre-Authorization）を設定する【推奨】

Salesforce管理者が接続アプリケーションに事前承認を設定することで、ユーザーの手動承認を不要にできます。

1. **Salesforce Setupにログイン**
   - 管理者アカウントでログイン

2. **接続アプリケーションの設定を開く**
   ```
   Setup → App Manager → [Your Connected App] → Edit
   ```

3. **OAuth設定を確認**
   - 「OAuth Settings」セクションで以下を確認:
     - ✅ Enable OAuth Settings がチェックされている
     - ✅ Callback URL が設定されている（例: `https://login.salesforce.com/services/oauth2/callback`）
     - ✅ Selected OAuth Scopes に以下が含まれている:
       - `api` - REST APIへのアクセス
       - `refresh_token, offline_access` - リフレッシュトークン
       - `full` - すべてのデータへのアクセス（必要に応じて）

4. **管理者承認済みユーザーを設定**
   - 「OAuth Settings」セクションで:
     - ✅ 「Admin approved users are pre-authorized」をチェック
   - 保存

5. **権限セットまたはプロファイルを割り当て**
   - 接続アプリケーションの詳細ページで「Manage」をクリック
   - 「Manage Profiles」または「Manage Permission Sets」をクリック
   - 使用するユーザー（`conn_test@thinkerdn.net`）のプロファイルまたは権限セットを選択
   - 保存

#### 方法2: ユーザーによる手動承認

事前承認を設定できない場合は、ユーザーが手動で承認を行います。

1. **承認URLを生成**
   
   以下のURLをブラウザで開きます（値を実際の設定に置き換えてください）:
   
   ```
   https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com/services/oauth2/authorize?response_type=code&client_id=3MVG9HtWXcDGV.nEIQERv68uqfRaaJag3_LzlSUyLGPzOUqAWAVpBPKABo7QeFDRyrXIltqlaeZ.hgyDMt.QM&redirect_uri=https://login.salesforce.com/services/oauth2/callback
   ```
   
   パラメータ:
   - `client_id`: Consumer Key（`sf-connect.py`の`consumer_key`の値）
   - `redirect_uri`: 接続アプリケーションで設定したCallback URL

2. **ユーザーでログインして承認**
   - 対象ユーザー（`conn_test@thinkerdn.net`）でログイン
   - 「許可」ボタンをクリックして接続アプリケーションを承認

3. **再度スクリプトを実行**
   ```bash
   python sf-connect.py
   ```

#### 方法3: 接続アプリケーションのポリシー設定を確認

1. **接続アプリケーションの管理画面を開く**
   ```
   Setup → App Manager → [Your Connected App] → Manage
   ```

2. **OAuth Policiesを確認**
   - 「Permitted Users」を確認:
     - 「All users may self-authorize」に設定（開発環境の場合）
     - または「Admin approved users are pre-authorized」に設定して、ユーザーを追加

3. **IP制限を確認**
   - 「IP Relaxation」を「Relax IP restrictions」に設定（開発環境の場合）

### 確認事項チェックリスト

- [ ] 接続アプリケーションで「Admin approved users are pre-authorized」がチェックされている
- [ ] ユーザーのプロファイルまたは権限セットが接続アプリケーションに割り当てられている
- [ ] OAuth Scopesに必要な権限（api, refresh_token等）が含まれている
- [ ] ユーザー名（`username`）が正しい
- [ ] Consumer Key（`consumer_key`）が正しい
- [ ] 秘密鍵ファイル（`sf-dev.key`）が正しい
- [ ] Token URLとAudience URLが一致している

### デバッグ用のPythonスクリプト

承認状況を確認するためのスクリプト:

```python
# check-oauth-approval.py
import webbrowser

consumer_key = '3MVG9HtWXcDGV.nEIQERv68uqfRaaJag3_LzlSUyLGPzOUqAWAVpBPKABo7QeFDRyrXIltqlaeZ.hgyDMt.QM'
redirect_uri = 'https://login.salesforce.com/services/oauth2/callback'
auth_url = 'https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com'

approval_url = f"{auth_url}/services/oauth2/authorize?response_type=code&client_id={consumer_key}&redirect_uri={redirect_uri}"

print("以下のURLをブラウザで開いて、ユーザーで承認してください:")
print(approval_url)
print("\n承認後、再度 sf-connect.py を実行してください。")

# 自動的にブラウザを開く場合
# webbrowser.open(approval_url)
```

### 関連エラー

このエラーと関連する可能性のある他のエラー:

- `invalid_client_id`: Consumer Keyが間違っている
- `invalid_client`: 接続アプリケーションの設定が正しくない
- `invalid_grant`: JWT署名が正しくない、または有効期限切れ

---

## エラー: "sObject type 'Account' is not supported"

### 問題の説明

```json
{
  "error": "Internal server error",
  "message": "Salesforce API Error (Status 400): sObject type 'Account' is not supported",
  "errorCode": "INVALID_TYPE"
}
```

### 原因

Client Credentials方式で取得したアクセストークンには、以下の制限があります：

1. **標準オブジェクトへのアクセス制限**
   - Account, Contact, Opportunity などの標準オブジェクトに直接アクセスできない場合があります
   - これはSalesforceのセキュリティポリシーによる制限です

2. **接続アプリケーションの権限設定**
   - Connected Appに設定されたスコープとユーザー権限に依存します
   - Client Credentials用のユーザーに適切な権限が付与されていない可能性があります

### 解決方法

#### 方法1: Salesforce側の設定を確認・変更

1. **接続アプリケーション（Connected App）の設定**
   ```
   Setup → App Manager → [Your Connected App] → Edit
   ```

2. **Client Credentials Flowの設定を確認**
   - 「Enable Client Credentials Flow」がチェックされていることを確認
   - 「Run As」でClient Credentials用のユーザーを設定
   - このユーザーに適切な権限プロファイルを割り当て

3. **OAuth スコープの設定**
   - 必要なスコープを追加:
     - `api` - REST APIへのアクセス
     - `full` - すべてのデータへのアクセス（開発環境のみ推奨）
     - `refresh_token` - リフレッシュトークンの取得

4. **ユーザー権限の確認**
   - Client Credentials用のユーザーに以下の権限を付与:
     - 「API Enabled」
     - 「View All Data」または必要なオブジェクトへの読み取り権限
     - カスタム権限セットの割り当て

#### 方法2: アクセス可能なオブジェクトを使用

Client Credentials方式でアクセス可能なオブジェクト例：

```python
# ✅ ユーザー情報（通常アクセス可能）
soql = "SELECT Id, Username, Email FROM User LIMIT 5"

# ✅ カスタムオブジェクト
soql = "SELECT Id, Name FROM MyCustomObject__c LIMIT 5"

# ✅ メタデータ情報
soql = "SELECT Id, DeveloperName FROM CustomObject LIMIT 5"

# ✅ 組織情報
soql = "SELECT Id, Name FROM Organization"

# ❌ 標準オブジェクト（権限設定が必要）
soql = "SELECT Id, Name FROM Account LIMIT 5"
```

#### 方法3: JWT Bearer方式を使用

標準オブジェクトへのフルアクセスが必要な場合は、JWT Bearer方式（`sf-connect.py`）を使用してください：

```python
# JWT Bearer方式の利点:
# - ユーザーコンテキストで実行
# - 標準オブジェクトへのフルアクセス
# - より柔軟な権限管理
```

### テスト用のSOQLクエリ例

```python
# Lambda関数のテストイベント

# 1. ユーザー情報取得（推奨）
{
  "action": "query",
  "soql": "SELECT Id, Username, Email, Profile.Name FROM User WHERE IsActive = true LIMIT 5"
}

# 2. 組織情報取得
{
  "action": "query",
  "soql": "SELECT Id, Name, OrganizationType, InstanceName FROM Organization"
}

# 3. カスタムオブジェクト（存在する場合）
{
  "action": "query",
  "soql": "SELECT Id, Name FROM MyCustomObject__c LIMIT 5"
}

# 4. プロファイル情報
{
  "action": "query",
  "soql": "SELECT Id, Name FROM Profile LIMIT 10"
}

# 5. 権限セット情報
{
  "action": "query",
  "soql": "SELECT Id, Name, Label FROM PermissionSet LIMIT 10"
}
```

## エラー: "no client credentials user enabled"

### 原因
接続アプリケーションでClient Credentials Flowが有効になっていない、またはユーザーが設定されていません。

### 解決方法

1. Salesforce Setup → App Manager
2. 接続アプリケーションを選択 → Edit
3. 「Enable Client Credentials Flow」をチェック
4. 「Run As」でユーザーを選択
5. 保存

## エラー: "invalid_client"

### 原因
Client IDまたはClient Secretが間違っています。

### 解決方法

1. Salesforce Setup → App Manager
2. 接続アプリケーションを選択 → View
3. Consumer KeyとConsumer Secretを確認
4. Lambda関数の環境変数を更新:
   ```bash
   aws lambda update-function-configuration \
     --function-name salesforce-client-credentials \
     --environment Variables="{SALESFORCE_CLIENT_ID=YOUR_CLIENT_ID,SALESFORCE_CLIENT_SECRET=YOUR_CLIENT_SECRET,SALESFORCE_TOKEN_URL=YOUR_TOKEN_URL}"
   ```

## エラー: "request not supported on this domain"

### 原因
Token URLが間違っています。

### 解決方法

Developer Edition環境の場合、カスタムドメインURLを使用してください：

```
❌ 間違い: https://login.salesforce.com/services/oauth2/token
❌ 間違い: https://test.salesforce.com/services/oauth2/token

✅ 正しい: https://[your-domain].develop.my.salesforce.com/services/oauth2/token
```

## パフォーマンスの最適化

### 1. トークンのキャッシュ

アクセストークンは一定期間有効なので、キャッシュすることで API呼び出しを削減できます：

```python
import time

# グローバル変数でトークンをキャッシュ
cached_token = None
token_expiry = 0

def get_cached_token():
    global cached_token, token_expiry
    
    current_time = time.time()
    if cached_token and current_time < token_expiry:
        return cached_token
    
    # トークンを取得
    token_info = get_salesforce_access_token()
    cached_token = token_info
    token_expiry = current_time + 3600  # 1時間キャッシュ
    
    return cached_token
```

### 2. 接続プーリング

requestsのSessionを使用して接続を再利用：

```python
import requests

session = requests.Session()

def query_salesforce_optimized(access_token, instance_url, soql_query):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    query_url = f"{instance_url}/services/data/v66.0/query"
    params = {'q': soql_query}
    
    response = session.get(query_url, headers=headers, params=params)
    return response.json()
```

## セキュリティのベストプラクティス

### 1. 環境変数の使用

機密情報はハードコードせず、環境変数を使用：

```python
SALESFORCE_CLIENT_ID = os.environ.get('SALESFORCE_CLIENT_ID')
SALESFORCE_CLIENT_SECRET = os.environ.get('SALESFORCE_CLIENT_SECRET')
```

### 2. AWS Secrets Managerの使用

より安全な方法として、AWS Secrets Managerを使用：

```python
import boto3
import json

def get_salesforce_credentials():
    secret_name = "salesforce/client-credentials"
    region_name = "ap-northeast-1"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    
    return {
        'client_id': secret['client_id'],
        'client_secret': secret['client_secret'],
        'token_url': secret['token_url']
    }
```

### 3. IAMロールの最小権限

Lambda関数のIAMロールには必要最小限の権限のみを付与：

```yaml
Policies:
  - Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - logs:CreateLogGroup
          - logs:CreateLogStream
          - logs:PutLogEvents
        Resource: !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/*'
      - Effect: Allow
        Action:
          - secretsmanager:GetSecretValue
        Resource: !Sub 'arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:salesforce/*'
```

## デバッグのヒント

### 1. CloudWatch Logsの確認

```bash
# 最新のログを表示
aws logs tail /aws/lambda/salesforce-client-credentials --follow

# 特定の時間範囲のログを表示
aws logs filter-log-events \
  --log-group-name /aws/lambda/salesforce-client-credentials \
  --start-time $(date -d '1 hour ago' +%s)000
```

### 2. 詳細なエラーログの有効化

Lambda関数にデバッグログを追加：

```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    logger.debug(f"Event: {json.dumps(event)}")
    logger.debug(f"Context: {context}")
    # ... 処理 ...
```

### 3. ローカルテスト

SAM CLIを使用してローカルでテスト：

```bash
# ローカルで関数を実行
sam local invoke SalesforceClientCredentialsFunction \
  --event test-event.json

# ローカルでAPI Gatewayをエミュレート
sam local start-api
```

## よくある質問（FAQ）

### Q1: Client Credentials方式とJWT Bearer方式の違いは？

**Client Credentials方式:**
- シンプルな認証フロー
- サーバー間通信に適している
- 一部のオブジェクトへのアクセスに制限がある場合がある

**JWT Bearer方式:**
- より柔軟な権限管理
- ユーザーコンテキストで実行
- 標準オブジェクトへのフルアクセス

### Q2: アクセストークンの有効期限は？

通常、Salesforceのアクセストークンは発行から約2時間有効です。Lambda関数では毎回新しいトークンを取得するか、キャッシュして再利用することができます。

### Q3: レート制限はありますか？

はい、SalesforceにはAPI呼び出しの制限があります：
- Developer Edition: 1日あたり5,000回
- Enterprise Edition: 1日あたり1,000回 × ライセンス数

詳細は[Salesforce API制限ドキュメント](https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm)を参照してください。

## サポート

問題が解決しない場合は、以下の情報を含めてお問い合わせください：

1. エラーメッセージの全文
2. Lambda関数のCloudWatch Logs
3. Salesforce接続アプリケーションの設定（機密情報を除く）
4. 使用しているSOQLクエリ
5. Salesforce組織のエディション（Developer, Enterprise等）
