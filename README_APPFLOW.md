# Salesforce AppFlow Custom Connector

AWS AppFlowのカスタムコネクタとして、SalesforceにClient Credentials方式で接続するLambda関数です。

## 📁 ファイル構成

```
.
├── lambda_appflow_connector.py   # AppFlowカスタムコネクタLambda関数
├── requirements.txt               # Python依存パッケージ
├── template-appflow.yaml          # AWS SAMテンプレート（AppFlow用）
└── README_APPFLOW.md              # このファイル
```

## 🚀 機能

このカスタムコネクタは以下のAppFlow操作をサポートします：

1. **ValidateCredentials** - 認証情報の検証
2. **DescribeConnectorConfiguration** - コネクタ設定情報の取得
3. **DescribeConnectorEntity** - オブジェクト（エンティティ）の詳細情報取得
4. **ListConnectorEntities** - 利用可能なオブジェクトのリスト取得
5. **QueryConnectorData** - データの読み取り（SELECT）
6. **WriteConnectorData** - データの書き込み（INSERT/UPDATE/UPSERT）

## 📋 前提条件

- AWS CLI設定済み
- AWS SAM CLI（推奨）
- Python 3.12以上
- Salesforce接続アプリケーション（Connected App）でClient Credentials Flowが有効
- AppFlowの使用権限

## 🔧 デプロイ手順

### ステップ1: Lambda関数のデプロイ

#### SAM CLIを使用（推奨）

```bash
# ビルド
sam build -t template-appflow.yaml

# デプロイ
sam deploy -t template-appflow.yaml --guided

# デプロイ時の入力例:
# Stack Name: salesforce-appflow-connector-stack
# AWS Region: ap-northeast-1
# Parameter SalesforceClientId: [Your Consumer Key]
# Parameter SalesforceClientSecret: [Your Consumer Secret]
# Parameter SalesforceTokenUrl: [Your Token URL]
# Confirm changes before deploy: Y
# Allow SAM CLI IAM role creation: Y
# AppFlowConnectorFunction may not have authorization defined, Is this okay?: Y
# Save arguments to configuration file: Y
```

#### 手動デプロイ

```bash
# デプロイパッケージの作成
mkdir lambda_appflow_connector
pip install -r requirements.txt -t lambda_appflow_connector/
copy lambda_appflow_connector.py lambda_appflow_connector/
cd lambda_appflow_connector
powershell Compress-Archive -Path * -DestinationPath ../lambda_appflow_connector.zip
cd ..

# Lambda関数の作成
aws lambda create-function \
  --function-name salesforce-appflow-connector \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_appflow_connector.lambda_handler \
  --zip-file fileb://lambda_appflow_connector.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{SALESFORCE_CLIENT_ID=YOUR_CLIENT_ID,SALESFORCE_CLIENT_SECRET=YOUR_CLIENT_SECRET,SALESFORCE_TOKEN_URL=YOUR_TOKEN_URL}"

# AppFlowからの呼び出しを許可
aws lambda add-permission \
  --function-name salesforce-appflow-connector \
  --statement-id appflow-invoke \
  --action lambda:InvokeFunction \
  --principal appflow.amazonaws.com
```

# 既存の関数を更新
aws lambda update-function-code \
  --function-name salesforce-appflow-connector \
  --zip-file fileb://lambda_appflow_connector.zip

### ステップ2: AppFlowカスタムコネクタの登録

1. **AWS AppFlow Consoleを開く**
   ```
   https://console.aws.amazon.com/appflow/
   ```

2. **カスタムコネクタの作成**
   - 左メニューから「Connectors」を選択
   - 「Create custom connector」をクリック

3. **コネクタ情報の入力**
   ```
   Connector label: Salesforce Client Credentials
   Description: Salesforce connector using OAuth 2.0 Client Credentials flow
   ```

4. **Lambda関数の選択**
   ```
   Lambda function: salesforce-appflow-connector
   ```

5. **コネクタの登録**
   - 「Register connector」をクリック
   - 登録が完了するまで待機

### ステップ3: 接続プロファイルの作成

1. **AppFlow Consoleで接続を作成**
   - 「Connections」→「Create connection」

2. **カスタムコネクタを選択**
   - 登録したカスタムコネクタ「Salesforce Client Credentials」を選択

3. **接続情報の入力**
   ```
   Connection name: salesforce-client-credentials-connection
   ```

4. **認証情報の設定**
   - Client Credentials方式の認証情報は環境変数で設定済み
   - 「Connect」をクリック

5. **接続のテスト**
   - 接続が成功することを確認

### ステップ4: フローの作成

1. **新しいフローを作成**
   - 「Flows」→「Create flow」

2. **ソースの設定**
   ```
   Source name: Salesforce Client Credentials
   Choose connection: salesforce-client-credentials-connection
   Choose object: User (または他のアクセス可能なオブジェクト)
   ```

3. **デスティネーションの設定**
   - S3、Redshift、Snowflake等、任意のデスティネーションを選択

4. **フィールドマッピング**
   - 必要なフィールドをマッピング

5. **フローの実行**
   - 「Run flow」でテスト実行

## 🧪 ローカルテスト

### Lambda関数の単体テスト

```bash
python lambda_appflow_connector.py
```

### 各操作のテスト

```python
# Test 1: 認証情報の検証
{
  "operation": "ValidateCredentials"
}

# Test 2: コネクタ設定の取得
{
  "operation": "DescribeConnectorConfiguration"
}

# Test 3: オブジェクトリストの取得
{
  "operation": "ListConnectorEntities"
}

# Test 4: オブジェクト詳細の取得
{
  "operation": "DescribeConnectorEntity",
  "entityIdentifier": "User"
}

# Test 5: データのクエリ
{
  "operation": "QueryConnectorData",
  "entityIdentifier": "User",
  "selectedFieldNames": ["Id", "Username", "Email"],
  "maxResults": 10,
  "filterExpression": "IsActive = true"
}

# Test 6: データの書き込み（INSERT）
{
  "operation": "WriteConnectorData",
  "entityIdentifier": "Contact",
  "operation": "INSERT",
  "records": [
    {
      "FirstName": "John",
      "LastName": "Doe",
      "Email": "john.doe@example.com"
    }
  ]
}
```

## 📊 サポートされるオブジェクト

Client Credentials方式でアクセス可能な主なオブジェクト：

### ✅ アクセス可能（通常）
- User
- Profile
- PermissionSet
- Organization
- カスタムオブジェクト（__c）

### ⚠️ 権限設定が必要
- Account
- Contact
- Opportunity
- Lead
- Case
- その他の標準オブジェクト

**注意**: 標準オブジェクトへのアクセスには、Salesforce側で適切な権限設定が必要です。詳細はTROUBLESHOOTING.mdを参照してください。

## 🔍 トラブルシューティング

### エラー: "Credential validation failed"

**原因**: Client IDまたはClient Secretが間違っている

**解決方法**:
```bash
# Lambda関数の環境変数を更新
aws lambda update-function-configuration \
  --function-name salesforce-appflow-connector \
  --environment Variables="{SALESFORCE_CLIENT_ID=YOUR_CLIENT_ID,SALESFORCE_CLIENT_SECRET=YOUR_CLIENT_SECRET,SALESFORCE_TOKEN_URL=YOUR_TOKEN_URL}"
```

### エラー: "Failed to list entities"

**原因**: Token URLが間違っている、またはネットワークエラー

**解決方法**:
1. Token URLを確認（Developer Editionの場合はカスタムドメインURLを使用）
2. Lambda関数のVPC設定を確認（インターネットアクセスが必要）

### エラー: "sObject type 'Account' is not supported"

**原因**: Client Credentials方式では標準オブジェクトへのアクセスに制限がある

**解決方法**:
1. Salesforce Setup → App Manager → Connected App → Edit
2. 「Run As」ユーザーに「View All Data」権限を付与
3. または、アクセス可能なオブジェクト（User, Profile等）を使用

詳細は`TROUBLESHOOTING.md`を参照してください。

## 🌐 AppFlowフローの例

### 例1: SalesforceからS3へのデータ同期

```yaml
Flow Name: Salesforce-User-to-S3
Source: Salesforce Client Credentials (User object)
Destination: Amazon S3
Schedule: Daily at 2:00 AM
Fields:
  - Id
  - Username
  - Email
  - Profile.Name
  - IsActive
Filter: IsActive = true
```

### 例2: S3からSalesforceへのデータ書き込み

```yaml
Flow Name: S3-to-Salesforce-Contact
Source: Amazon S3
Destination: Salesforce Client Credentials (Contact object)
Trigger: On-demand
Operation: INSERT
Field Mapping:
  - FirstName → FirstName
  - LastName → LastName
  - Email → Email
  - Phone → Phone
```

## 📈 パフォーマンスの最適化

### 1. バッチサイズの調整

AppFlowのバッチサイズを調整してスループットを向上：

```python
# Lambda関数でバッチ処理を最適化
max_results = event.get('maxResults', 1000)  # デフォルトを増やす
```

### 2. フィールドの選択

必要なフィールドのみを選択してデータ転送量を削減：

```python
selected_fields = ['Id', 'Name', 'Email']  # 必要最小限のフィールド
```

### 3. フィルタの使用

WHERE句を使用してデータ量を削減：

```python
filter_expression = "LastModifiedDate > LAST_N_DAYS:7"
```

## 🔐 セキュリティのベストプラクティス

### 1. AWS Secrets Managerの使用

機密情報をSecrets Managerで管理：

```python
import boto3
import json

def get_credentials_from_secrets_manager():
    client = boto3.client('secretsmanager', region_name='ap-northeast-1')
    response = client.get_secret_value(SecretId='salesforce/client-credentials')
    secret = json.loads(response['SecretString'])
    return secret
```

### 2. VPC内でのLambda実行

セキュリティを強化するためVPC内でLambda関数を実行：

```yaml
VpcConfig:
  SecurityGroupIds:
    - sg-xxxxxxxxx
  SubnetIds:
    - subnet-xxxxxxxxx
    - subnet-yyyyyyyyy
```

### 3. IAMロールの最小権限

必要最小限の権限のみを付与：

```yaml
Policies:
  - PolicyName: MinimalPermissions
    PolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Action:
            - logs:CreateLogGroup
            - logs:CreateLogStream
            - logs:PutLogEvents
          Resource: !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*'
```

## 📝 制限事項

1. **API呼び出し制限**
   - Salesforce API制限に従う（Developer Edition: 5,000回/日）

2. **Lambda実行時間**
   - 最大60秒（タイムアウト設定可能）

3. **データサイズ**
   - Lambda関数のペイロードサイズ制限: 6MB

4. **同時実行数**
   - Lambdaの同時実行数制限に従う

## 🆚 他の接続方式との比較

| 機能 | Client Credentials | JWT Bearer | Username-Password |
|------|-------------------|------------|-------------------|
| 実装の複雑さ | 低 | 中 | 低 |
| セキュリティ | 高 | 最高 | 中 |
| 標準オブジェクトアクセス | 制限あり | フルアクセス | フルアクセス |
| ユーザーコンテキスト | なし | あり | あり |
| 推奨用途 | サーバー間通信 | エンタープライズ統合 | 開発・テスト |

## 📚 参考資料

- [AWS AppFlow Custom Connector Documentation](https://docs.aws.amazon.com/appflow/latest/userguide/custom-connector.html)
- [Salesforce OAuth 2.0 Client Credentials Flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_client_credentials_flow.htm)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

## 🤝 サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：

1. エラーメッセージの全文
2. Lambda関数のCloudWatch Logs
3. AppFlowフローの設定
4. 使用しているSalesforceオブジェクト
5. Salesforce組織のエディション

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。
