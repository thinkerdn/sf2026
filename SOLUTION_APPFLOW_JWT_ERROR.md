# AppFlowでのJWT使用時の「invalid_client_id」エラー解決方法

## エラー内容

```
エラー: invalid_client_id
Salesforceログイン履歴: 失敗：コンシューマキーパラメーターがありません
```

## 問題の原因

`sf-connect-t.py`で生成されたJWTトークンをAppFlowで直接使用しようとしていますが、**AppFlowとJWT Bearer認証の仕組みが異なる**ため、このエラーが発生します。

### 認証方式の違い

1. **JWT Bearer認証（sf-connect-t.py）**
   - JWTトークンを生成してSalesforceに送信
   - アクセストークンを取得
   - 主にサーバー間通信で使用

2. **AppFlowの認証**
   - OAuth 2.0フローを使用
   - Consumer Key（Client ID）とConsumer Secret（Client Secret）を**直接**AppFlowに設定
   - AppFlowが自動的にトークンを取得・管理

**重要**: AppFlowにはJWTトークンではなく、**Consumer KeyとConsumer Secret**を設定する必要があります。

---

## 解決方法

### ✅ 方法1: AppFlowでClient Credentials方式を使用【推奨】

AppFlowのカスタムコネクタを使用して、Client Credentials方式でSalesforceに接続します。

#### ステップ1: Lambda関数のデプロイ

```bash
# SAM CLIでデプロイ
sam build -t template-appflow.yaml
sam deploy -t template-appflow.yaml --guided

# デプロイ時の入力:
# Parameter SalesforceClientId: 3MVG95ol_2z.5OsOsJrbjsoq7u8vcS0KP15Q4OEw6eBq2VtCmSxTsulDZqq02emelED9fFSjBRZx5jQBMdfkz
# Parameter SalesforceClientSecret: B413D497D762E9E1CC95708A28BC7AB554E75861B873F8A3E45F153A1C963B18
# Parameter SalesforceTokenUrl: https://04401-toyota-crm--developer.sandbox.my.salesforce.com/services/oauth2/token
```

#### ステップ2: AppFlowカスタムコネクタの登録

1. **AWS AppFlow Consoleを開く**
   ```
   https://console.aws.amazon.com/appflow/
   ```

2. **カスタムコネクタの作成**
   - 左メニュー「Connectors」→「Create custom connector」
   - Connector label: `Salesforce JWT Bearer`
   - Lambda function: `salesforce-appflow-connector`（デプロイしたLambda関数）
   - 「Register connector」をクリック

3. **接続プロファイルの作成**
   - 「Connections」→「Create connection」
   - カスタムコネクタ「Salesforce JWT Bearer」を選択
   - Connection name: `salesforce-jwt-connection`
   - 「Connect」をクリック

これでAppFlowがLambda関数を通じてSalesforceに接続します。

---

### ✅ 方法2: JWT Bearer方式用のカスタムコネクタを作成

JWT Bearer認証を使用するカスタムコネクタを作成します。

#### Lambda関数の作成

`lambda_appflow_jwt_connector.py`を作成：

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
    print(f"Event: {json.dumps(event)}")
    
    try:
        if operation == 'ValidateCredentials':
            return validate_credentials(event)
        elif operation == 'DescribeConnectorConfiguration':
            return describe_connector_configuration()
        elif operation == 'ListConnectorEntities':
            return list_connector_entities(event)
        elif operation == 'DescribeConnectorEntity':
            return describe_connector_entity(event)
        elif operation == 'QueryConnectorData':
            return query_connector_data(event)
        elif operation == 'WriteConnectorData':
            return write_connector_data(event)
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
    username = os.environ.get('SALESFORCE_USERNAME')
    consumer_key = os.environ.get('SALESFORCE_CONSUMER_KEY')
    private_key_content = os.environ.get('SALESFORCE_PRIVATE_KEY')
    token_url = os.environ.get('SALESFORCE_TOKEN_URL')
    audience = os.environ.get('SALESFORCE_AUDIENCE')
    
    # 秘密鍵の読み込み
    private_key = serialization.load_pem_private_key(
        private_key_content.encode('utf-8'),
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
    params = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': assertion
    }
    
    response = requests.post(token_url, data=params)
    response.raise_for_status()
    
    token_data = response.json()
    return token_data['access_token'], token_data['instance_url']

def validate_credentials(event):
    """
    認証情報の検証
    """
    try:
        access_token, instance_url = get_jwt_access_token()
        
        # 認証テスト（組織情報を取得）
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{instance_url}/services/data/v60.0/sobjects",
            headers=headers
        )
        response.raise_for_status()
        
        return {
            'isSuccess': True
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
        'connectorRuntimeSettings': [
            {
                'key': 'instanceUrl',
                'dataType': 'String',
                'isRequired': False,
                'label': 'Instance URL',
                'description': 'Salesforce Instance URL',
                'scope': 'ConnectorProfile'
            }
        ],
        'supportedApiVersions': ['v60.0'],
        'supportedOperators': ['EQUAL_TO', 'GREATER_THAN', 'LESS_THAN', 'CONTAINS'],
        'supportedWriteOperations': ['INSERT', 'UPDATE', 'UPSERT', 'DELETE'],
        'supportsMultipleRecords': True
    }

def list_connector_entities(event):
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
            'entities': entities
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
                'dataType': map_salesforce_type(field['type']),
                'label': field['label'],
                'isRequired': not field['nillable'] and not field.get('defaultedOnCreate', False),
                'isPrimaryKey': field['name'] == 'Id',
                'isCreatable': field.get('createable', False),
                'isUpdatable': field.get('updateable', False)
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
        fields_str = ', '.join(selected_fields) if selected_fields else '*'
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

def write_connector_data(event):
    """
    データの書き込み（INSERT/UPDATE/UPSERT）
    """
    entity_identifier = event.get('entityIdentifier')
    operation = event.get('operation', 'INSERT')
    records = event.get('records', [])
    
    try:
        access_token, instance_url = get_jwt_access_token()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        results = []
        
        for record in records:
            if operation == 'INSERT':
                response = requests.post(
                    f"{instance_url}/services/data/v60.0/sobjects/{entity_identifier}",
                    headers=headers,
                    json=record
                )
            elif operation == 'UPDATE':
                record_id = record.pop('Id')
                response = requests.patch(
                    f"{instance_url}/services/data/v60.0/sobjects/{entity_identifier}/{record_id}",
                    headers=headers,
                    json=record
                )
            elif operation == 'UPSERT':
                external_id_field = event.get('externalIdFieldName', 'Id')
                external_id_value = record.pop(external_id_field)
                response = requests.patch(
                    f"{instance_url}/services/data/v60.0/sobjects/{entity_identifier}/{external_id_field}/{external_id_value}",
                    headers=headers,
                    json=record
                )
            
            if response.status_code in [200, 201, 204]:
                results.append({
                    'isSuccess': True,
                    'recordId': response.json().get('id') if response.text else None
                })
            else:
                results.append({
                    'isSuccess': False,
                    'errorMessage': response.text
                })
        
        return {
            'isSuccess': True,
            'records': results
        }
    except Exception as e:
        return {
            'isSuccess': False,
            'errorMessage': f'Failed to write data: {str(e)}'
        }

def map_salesforce_type(sf_type):
    """
    SalesforceのデータタイプをAppFlowのデータタイプにマッピング
    """
    type_mapping = {
        'string': 'String',
        'textarea': 'String',
        'email': 'String',
        'phone': 'String',
        'url': 'String',
        'picklist': 'String',
        'multipicklist': 'String',
        'int': 'Integer',
        'double': 'Double',
        'currency': 'Double',
        'percent': 'Double',
        'boolean': 'Boolean',
        'date': 'Date',
        'datetime': 'Datetime',
        'time': 'Time',
        'reference': 'String',
        'id': 'String'
    }
    return type_mapping.get(sf_type.lower(), 'String')
```

#### 環境変数の設定

Lambda関数に以下の環境変数を設定：

```bash
SALESFORCE_USERNAME=gaibu_sys_icr_ts_hanbaiten_0714@toyotasystems.com.developer
SALESFORCE_CONSUMER_KEY=3MVG95ol_2z.5OsOsJrbjsoq7u8vcS0KP15Q4OEw6eBq2VtCmSxTsulDZqq02emelED9fFSjBRZx5jQBMdfkz
SALESFORCE_TOKEN_URL=https://04401-toyota-crm--developer.sandbox.my.salesforce.com/services/oauth2/token
SALESFORCE_AUDIENCE=https://04401-toyota-crm--developer.sandbox.my.salesforce.com
SALESFORCE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
[秘密鍵の内容]
-----END PRIVATE KEY-----
```

**注意**: 秘密鍵は改行を`\n`に置き換えて1行にするか、AWS Secrets Managerを使用してください。

---

### ✅ 方法3: Salesforce標準コネクタを使用【最も簡単】

AppFlowの標準Salesforceコネクタを使用します。

#### ステップ1: Salesforce接続の作成

1. **AppFlow Console → Connections → Create connection**

2. **Salesforceを選択**

3. **接続情報の入力**
   ```
   Connection name: salesforce-oauth-connection
   Environment: Sandbox
   ```

4. **OAuth認証**
   - 「Connect」をクリック
   - Salesforceログイン画面が表示される
   - ユーザー（gaibu_sys_icr_ts_hanbaiten_0714@toyotasystems.com.developer）でログイン
   - 「許可」をクリック

5. **接続の確認**
   - 接続が成功したことを確認

#### ステップ2: フローの作成

1. **Flows → Create flow**

2. **ソースの設定**
   ```
   Source: Salesforce
   Connection: salesforce-oauth-connection
   Object: User（または他のオブジェクト）
   ```

3. **デスティネーションの設定**
   - S3、Redshift等を選択

4. **フローの実行**

---

## 重要なポイント

### ❌ 間違った方法

```
AppFlowに直接JWTトークンを入力
→ AppFlowはJWTトークンを直接受け付けません
```

### ✅ 正しい方法

```
方法1: カスタムコネクタ（Lambda）でJWT認証を実装
方法2: Consumer KeyとSecretをLambda環境変数に設定
方法3: Salesforce標準コネクタでOAuth認証を使用
```

---

## トラブルシューティング

### エラー: "コンシューマキーパラメーターがありません"

**原因**: AppFlowがConsumer Keyを見つけられない

**解決方法**:
1. Lambda関数の環境変数を確認
2. カスタムコネクタが正しく登録されているか確認
3. または、Salesforce標準コネクタを使用

### エラー: "invalid_client_id"

**原因**: Consumer Keyが間違っている、または設定されていない

**解決方法**:
```bash
# Lambda関数の環境変数を更新
aws lambda update-function-configuration \
  --function-name salesforce-appflow-jwt-connector \
  --environment Variables="{SALESFORCE_USERNAME=gaibu_sys_icr_ts_hanbaiten_0714@toyotasystems.com.developer,SALESFORCE_CONSUMER_KEY=3MVG95ol_2z.5OsOsJrbjsoq7u8vcS0KP15Q4OEw6eBq2VtCmSxTsulDZqq02emelED9fFSjBRZx5jQBMdfkz,SALESFORCE_TOKEN_URL=https://04401-toyota-crm--developer.sandbox.my.salesforce.com/services/oauth2/token,SALESFORCE_AUDIENCE=https://04401-toyota-crm--developer.sandbox.my.salesforce.com}"
```

---

## まとめ

**推奨される解決方法**:

1. **最も簡単**: Salesforce標準コネクタを使用（方法3）
2. **カスタマイズが必要**: JWT Bearer用のカスタムコネクタを作成（方法2）
3. **既存のコードを活用**: Client Credentials方式のカスタムコネクタを使用（方法1）

AppFlowでは、JWTトークンを直接入力するのではなく、**認証情報（Consumer Key/Secret）をLambda関数に設定**し、Lambda関数内でトークンを取得する仕組みが必要です。
