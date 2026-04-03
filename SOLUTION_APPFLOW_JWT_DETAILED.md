# AppFlow JWT認証「コンシューマキーパラメーターがありません」エラーの解決方法

## エラー内容

```
エラー: invalid_client_id
Salesforceログイン履歴: 失敗：コンシューマキーパラメーターがありません
```

## 問題の原因

AppFlowのJWT認証画面で生成されたJWTトークン（assertion）を入力していますが、**AppFlowはJWTトークンだけでは認証できません**。

### なぜエラーが発生するのか

1. **JWTトークンには署名が含まれているが、Consumer Keyが明示的に送信されていない**
   - JWTのペイロードには`iss`（issuer = Consumer Key）が含まれていますが、AppFlowはこれを正しく抽出・送信できていません

2. **Salesforce側の期待値**
   - Salesforceは、JWT Bearer認証時に以下のパラメータを期待しています：
     ```
     grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
     assertion=[JWTトークン]
     client_id=[Consumer Key]  ← これが不足している！
     ```

3. **AppFlowの制限**
   - AppFlowのJWT認証UIは、JWTトークンのみを入力する仕様になっており、Consumer Keyを別途送信する機能がありません

---

## 解決方法

### ✅ 方法1: OAuth 2.0認証を使用【最も簡単・推奨】

JWT認証ではなく、標準のOAuth 2.0認証を使用します。

#### ステップ1: AppFlow接続設定

1. **AppFlow Console → Salesforceに接続**

2. **OAuth グラントタイプを変更**
   - 「JSON ウェブトークン (JWT)」ではなく
   - **「認証コード付与」を選択**

3. **Salesforce環境を選択**
   - Production または Sandbox を選択
   - あなたの場合: **Sandbox**

4. **接続をクリック**
   - Salesforceログイン画面が表示されます
   - ユーザー名: `gaibu_sys_icr_ts_hanbaiten_0714@toyotasystems.com.developer`
   - パスワードを入力
   - 「許可」をクリック

5. **接続完了**
   - AppFlowが自動的にトークンを管理します

**この方法の利点:**
- 設定が簡単
- トークンの更新が自動
- エラーが発生しにくい

---

### ✅ 方法2: Client Credentials認証を使用

Consumer KeyとConsumer Secretを使用した認証方式です。

#### ステップ1: Salesforce側の設定確認

1. **接続アプリケーションの設定**
   ```
   Setup → App Manager → AWS_AppFlow_Connector → Edit
   ```

2. **Client Credentials Flowを有効化**
   - ✅ 「Enable Client Credentials Flow」をチェック
   - 「Run As」でユーザーを選択: `gaibu_sys_icr_ts_hanbaiten_0714@toyotasystems.com.developer`
   - 保存

#### ステップ2: AppFlow接続設定

1. **AppFlow Console → Salesforceに接続**

2. **OAuth グラントタイプ**
   - 「クライアント認証情報」を選択（利用可能な場合）

3. **認証情報を入力**
   ```
   Client ID: 3MVG95ol_2z.5OsOsJrbjsoq7u8vcS0KP15Q4OEw6eBq2VtCmSxTsulDZqq02emelED9fFSjBRZx5jQBMdfkz
   Client Secret: B413D497D762E9E1CC95708A28BC7AB554E75861B873F8A3E45F153A1C963B18
   Token URL: https://04401-toyota-crm--developer.sandbox.my.salesforce.com/services/oauth2/token
   ```

4. **接続をテスト**

---

### ✅ 方法3: カスタムコネクタでJWT認証を実装【高度】

Lambda関数を使用してJWT認証を実装します。

#### ステップ1: Lambda関数の作成

`lambda_appflow_jwt.py`を作成：

```python
import json
import os
import jwt
import time
import requests
from cryptography.hazmat.primitives import serialization

def lambda_handler(event, context):
    """
    AppFlow Custom Connector for Salesforce JWT Bearer Authentication
    """
    operation = event.get('operation')
    
    print(f"Operation: {operation}")
    
    try:
        if operation == 'ValidateCredentials':
            return validate_credentials()
        elif operation == 'DescribeConnectorConfiguration':
            return describe_connector_configuration()
        elif operation == 'ListConnectorEntities':
            return list_connector_entities()
        elif operation == 'DescribeConnectorEntity':
            return describe_connector_entity(event)
        elif operation == 'QueryConnectorData':
            return query_connector_data(event)
        else:
            return {
                'isSuccess': False,
                'errorMessage': f'Unsupported operation: {operation}'
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'isSuccess': False,
            'errorMessage': str(e)
        }

def get_jwt_access_token():
    """
    JWT Bearer方式でアクセストークンを取得
    """
    # 環境変数から設定を取得
    username = os.environ['SALESFORCE_USERNAME']
    consumer_key = os.environ['SALESFORCE_CONSUMER_KEY']
    private_key_pem = os.environ['SALESFORCE_PRIVATE_KEY']
    token_url = os.environ['SALESFORCE_TOKEN_URL']
    audience = os.environ['SALESFORCE_AUDIENCE']
    
    # 秘密鍵の読み込み
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None
    )
    
    # JWTペイロードの生成
    payload = {
        'iss': consumer_key,
        'sub': username,
        'aud': audience,
        'exp': int(time.time()) + 300  # 5分間有効
    }
    
    # JWTの生成
    assertion = jwt.encode(payload, private_key, algorithm='RS256')
    
    # アクセストークンの取得
    # 重要: client_idパラメータを追加
    params = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': assertion,
        'client_id': consumer_key  # ← これが重要！
    }
    
    response = requests.post(token_url, data=params)
    
    if response.status_code != 200:
        raise Exception(f"Token request failed: {response.text}")
    
    token_data = response.json()
    return token_data['access_token'], token_data['instance_url']

def validate_credentials():
    """
    認証情報の検証
    """
    try:
        access_token, instance_url = get_jwt_access_token()
        
        # 認証テスト
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{instance_url}/services/data/v60.0/sobjects",
            headers=headers
        )
        
        if response.status_code == 200:
            return {'isSuccess': True}
        else:
            return {
                'isSuccess': False,
                'errorMessage': f'Validation failed: {response.text}'
            }
    except Exception as e:
        return {
            'isSuccess': False,
            'errorMessage': f'Credential validation failed: {str(e)}'
        }

def describe_connector_configuration():
    """
    コネクタ設定情報の取得
    """
    return {
        'isSuccess': True,
        'connectorRuntimeSettings': [],
        'supportedApiVersions': ['v60.0'],
        'supportedOperators': ['EQUAL_TO', 'GREATER_THAN', 'LESS_THAN'],
        'supportedWriteOperations': ['INSERT', 'UPDATE', 'UPSERT'],
        'supportsMultipleRecords': True
    }

def list_connector_entities():
    """
    利用可能なオブジェクトのリスト取得
    """
    try:
        access_token, instance_url = get_jwt_access_token()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{instance_url}/services/data/v60.0/sobjects",
            headers=headers
        )
        response.raise_for_status()
        
        sobjects = response.json()['sobjects']
        
        entities = []
        for sobject in sobjects:
            if sobject.get('queryable'):
                entities.append({
                    'entityIdentifier': sobject['name'],
                    'label': sobject['label'],
                    'hasNestedEntities': False
                })
        
        return {
            'isSuccess': True,
            'entities': entities[:100]  # 最初の100件
        }
    except Exception as e:
        return {
            'isSuccess': False,
            'errorMessage': f'Failed to list entities: {str(e)}'
        }

def describe_connector_entity(event):
    """
    オブジェクトの詳細情報取得
    """
    entity_identifier = event.get('entityIdentifier')
    
    try:
        access_token, instance_url = get_jwt_access_token()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{instance_url}/services/data/v60.0/sobjects/{entity_identifier}/describe",
            headers=headers
        )
        response.raise_for_status()
        
        describe_result = response.json()
        
        fields = []
        for field in describe_result['fields']:
            fields.append({
                'fieldName': field['name'],
                'dataType': 'String',  # 簡略化
                'label': field['label'],
                'isRequired': not field['nillable'],
                'isPrimaryKey': field['name'] == 'Id'
            })
        
        return {
            'isSuccess': True,
            'entityDefinition': {
                'entityIdentifier': entity_identifier,
                'label': describe_result['label'],
                'fields': fields
            }
        }
    except Exception as e:
        return {
            'isSuccess': False,
            'errorMessage': f'Failed to describe entity: {str(e)}'
        }

def query_connector_data(event):
    """
    データのクエリ（読み取り）
    """
    entity_identifier = event.get('entityIdentifier')
    selected_fields = event.get('selectedFieldNames', [])
    max_results = event.get('maxResults', 100)
    
    try:
        access_token, instance_url = get_jwt_access_token()
        
        # SOQLクエリの構築
        if not selected_fields:
            selected_fields = ['Id']
        
        fields_str = ', '.join(selected_fields)
        soql = f"SELECT {fields_str} FROM {entity_identifier} LIMIT {max_results}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{instance_url}/services/data/v60.0/query",
            headers=headers,
            params={'q': soql}
        )
        response.raise_for_status()
        
        query_result = response.json()
        
        records = []
        for record in query_result.get('records', []):
            # 'attributes'フィールドを除外
            record_data = {k: v for k, v in record.items() if k != 'attributes'}
            records.append(record_data)
        
        return {
            'isSuccess': True,
            'records': records
        }
    except Exception as e:
        return {
            'isSuccess': False,
            'errorMessage': f'Failed to query data: {str(e)}'
        }
```

#### ステップ2: Lambda関数のデプロイ

```bash
# requirements.txtを作成
cat > requirements.txt << EOF
PyJWT==2.8.0
cryptography==41.0.7
requests==2.31.0
EOF

# Lambda関数をパッケージ化
mkdir package
pip install -r requirements.txt -t package/
cp lambda_appflow_jwt.py package/
cd package
zip -r ../lambda_appflow_jwt.zip .
cd ..

# Lambda関数を作成
aws lambda create-function \
  --function-name salesforce-appflow-jwt \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_appflow_jwt.lambda_handler \
  --zip-file fileb://lambda_appflow_jwt.zip \
  --timeout 60 \
  --environment Variables="{
    SALESFORCE_USERNAME=gaibu_sys_icr_ts_hanbaiten_0714@toyotasystems.com.developer,
    SALESFORCE_CONSUMER_KEY=3MVG95ol_2z.5OsOsJrbjsoq7u8vcS0KP15Q4OEw6eBq2VtCmSxTsulDZqq02emelED9fFSjBRZx5jQBMdfkz,
    SALESFORCE_TOKEN_URL=https://04401-toyota-crm--developer.sandbox.my.salesforce.com/services/oauth2/token,
    SALESFORCE_AUDIENCE=https://04401-toyota-crm--developer.sandbox.my.salesforce.com,
    SALESFORCE_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----
[秘密鍵の内容をここに貼り付け]
-----END PRIVATE KEY-----'
  }"
```

#### ステップ3: AppFlowカスタムコネクタの登録

1. **AppFlow Console → Connectors → Create custom connector**

2. **設定**
   ```
   Connector label: Salesforce JWT Bearer
   Lambda function: salesforce-appflow-jwt
   ```

3. **Register connector**

4. **接続の作成**
   - Connections → Create connection
   - カスタムコネクタ「Salesforce JWT Bearer」を選択
   - Connect

---

## 重要なポイント

### ❌ AppFlowのJWT認証UIの制限

AppFlowのJWT認証画面は、以下の理由で正しく動作しません：

1. **Consumer Keyが送信されない**
   - JWTトークンのみを送信し、`client_id`パラメータを送信しない
   - Salesforceは`client_id`パラメータを必須としている

2. **トークンの有効期限管理**
   - JWTトークンは短時間（5分程度）で期限切れになる
   - AppFlowは自動的に再生成できない

### ✅ 推奨される方法

1. **最も簡単**: OAuth 2.0認証コード付与（方法1）
2. **サーバー間通信**: Client Credentials認証（方法2）
3. **完全なカスタマイズ**: Lambda関数でJWT認証（方法3）

---

## トラブルシューティング

### Q: なぜJWTトークンだけでは動作しないのか？

**A**: Salesforce JWT Bearer認証の仕様では、以下のパラメータが必要です：

```http
POST /services/oauth2/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
&assertion=[JWTトークン]
&client_id=[Consumer Key]  ← AppFlowが送信していない
```

AppFlowのJWT認証UIは`client_id`を送信しないため、エラーが発生します。

### Q: `sf-connect-t.py`で生成したJWTトークンは使えないのか？

**A**: Pythonスクリプトでは正しく動作しますが、AppFlowでは使えません。理由：

- Pythonスクリプト: `client_id`パラメータを明示的に送信していない（JWTの`iss`クレームから推測される）
- AppFlow: UIの制限により`client_id`を送信できない

### Q: 最も簡単な解決方法は？

**A**: **OAuth 2.0認証コード付与（方法1）**を使用してください。

設定手順：
1. AppFlowでSalesforce接続を作成
2. OAuth グラントタイプ: 「認証コード付与」を選択
3. Salesforceでログインして許可
4. 完了

---

## まとめ

**AppFlowのJWT認証UIは、Salesforceの要件を満たしていないため使用できません。**

代わりに以下の方法を使用してください：

1. ✅ **OAuth 2.0認証コード付与**（最も簡単）
2. ✅ **Client Credentials認証**（サーバー間通信）
3. ✅ **Lambda関数でカスタムコネクタ**（完全なカスタマイズ）

これらの方法により、AppFlowからSalesforceへの接続が正常に動作します。
