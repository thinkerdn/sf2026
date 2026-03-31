# Salesforce Client Credentials Lambda Function

AWS Lambda関数を使用してSalesforceにClient Credentials方式で接続するプロジェクトです。

## 📁 ファイル構成

```
.
├── lambda_sf_client_credentials.py  # Lambda関数のメインコード
├── requirements.txt                 # Python依存パッケージ
├── template.yaml                    # AWS SAMテンプレート
└── README_LAMBDA.md                 # このファイル
```

## 🚀 機能

このLambda関数は以下の機能を提供します：

1. **トークン取得** (`action: get_token`)
   - Salesforceのアクセストークンを取得

2. **APIバージョン取得** (`action: get_versions`)
   - Salesforce REST APIのバージョン情報を取得

3. **SOQLクエリ実行** (`action: query`)
   - SalesforceにSOQLクエリを実行してデータを取得

## 📋 前提条件

- Python 3.12以上
- AWS CLI設定済み
- AWS SAM CLI（デプロイ用）
- Salesforce接続アプリケーション（Connected App）でClient Credentials Flowが有効

## 🔧 ローカルテスト

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. ローカル実行

```bash
python lambda_sf_client_credentials.py
```

## 📦 AWS Lambdaへのデプロイ

### 方法1: AWS SAM CLIを使用（推奨）

#### 1. SAM CLIのインストール

```bash
# Windows (Chocolatey)
choco install aws-sam-cli

# macOS (Homebrew)
brew install aws-sam-cli

# Linux
pip install aws-sam-cli
```

#### 2. ビルド

```bash
sam build
```

#### 3. デプロイ

```bash
# 初回デプロイ（ガイド付き）
sam deploy --guided

# 2回目以降
sam deploy
```

デプロイ時に以下の情報を入力：
- Stack Name: `salesforce-client-credentials-stack`
- AWS Region: `ap-northeast-1` (東京リージョン)
- Parameter SalesforceClientId: `[あなたのConsumer Key]`
- Parameter SalesforceClientSecret: `[あなたのConsumer Secret]`
- Parameter SalesforceTokenUrl: `[あなたのToken URL]`

### 方法2: 手動デプロイ

#### 1. デプロイパッケージの作成

```bash
# Windowsの場合
mkdir package
pip install -r requirements.txt -t package/
copy lambda_sf_client_credentials.py package/
cd package
powershell Compress-Archive -Path * -DestinationPath ../lambda_function.zip
cd ..
```

```bash
# Linux/macOSの場合
mkdir package
pip install -r requirements.txt -t package/
cp lambda_sf_client_credentials.py package/
cd package
zip -r ../lambda_function.zip .
cd ..
```

#### 2. AWS CLIでデプロイ

```bash
# Lambda関数の作成
aws lambda create-function \
  --function-name salesforce-client-credentials \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_sf_client_credentials.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{SALESFORCE_CLIENT_ID=YOUR_CLIENT_ID,SALESFORCE_CLIENT_SECRET=YOUR_CLIENT_SECRET,SALESFORCE_TOKEN_URL=YOUR_TOKEN_URL}"

# 既存の関数を更新
aws lambda update-function-code \
  --function-name salesforce-client-credentials \
  --zip-file fileb://lambda_function.zip
```

## 🧪 Lambda関数のテスト

### AWS Consoleでテスト

1. AWS Lambda Consoleを開く
2. 関数 `salesforce-client-credentials` を選択
3. 「テスト」タブを選択
4. 以下のテストイベントを作成

#### テストイベント1: トークン取得

```json
{
  "action": "get_token"
}
```

#### テストイベント2: APIバージョン取得

```json
{
  "action": "get_versions"
}
```

#### テストイベント3: SOQLクエリ実行

```json
{
  "action": "query",
  "soql": "SELECT Id, Name FROM Account LIMIT 5"
}
```

### AWS CLIでテスト

```bash
# トークン取得
aws lambda invoke \
  --function-name salesforce-client-credentials \
  --payload '{"action":"get_token"}' \
  response.json

# APIバージョン取得
aws lambda invoke \
  --function-name salesforce-client-credentials \
  --payload '{"action":"get_versions"}' \
  response.json

# SOQLクエリ実行
aws lambda invoke \
  --function-name salesforce-client-credentials \
  --payload '{"action":"query","soql":"SELECT Id, Name FROM Account LIMIT 5"}' \
  response.json

# 結果の確認
cat response.json
```

## 🔐 環境変数

Lambda関数は以下の環境変数を使用します：

| 環境変数名 | 説明 | 例 |
|-----------|------|-----|
| `SALESFORCE_CLIENT_ID` | Salesforce Consumer Key | `3MVG9Ht...` |
| `SALESFORCE_CLIENT_SECRET` | Salesforce Consumer Secret | `245C545D...` |
| `SALESFORCE_TOKEN_URL` | Salesforce Token Endpoint | `https://orgfarm-xxx.develop.my.salesforce.com/services/oauth2/token` |

## 📊 レスポンス形式

### 成功時

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "statusCode": 200,
    "timestamp": "2026-03-31T02:04:36.123456",
    "action": "get_token",
    "message": "Access token retrieved successfully",
    "data": {
      "access_token": "00Dfj00000JddeT!AQEA...",
      "instance_url": "https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com",
      "token_type": "Bearer",
      "issued_at": "1774922010572"
    }
  }
}
```

### エラー時

```json
{
  "statusCode": 500,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "error": "Internal server error",
    "message": "Failed to get access token: ...",
    "timestamp": "2026-03-31T02:04:36.123456"
  }
}
```

## 🌐 API Gateway統合

SAMテンプレートにはAPI Gatewayの設定も含まれています。デプロイ後、以下のエンドポイントが利用可能になります：

- `GET /token` - アクセストークン取得
- `GET /versions` - APIバージョン取得
- `POST /query` - SOQLクエリ実行

### API Gatewayの使用例

```bash
# API URLの取得
API_URL=$(aws cloudformation describe-stacks \
  --stack-name salesforce-client-credentials-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`SalesforceApiUrl`].OutputValue' \
  --output text)

# トークン取得
curl "${API_URL}/token"

# APIバージョン取得
curl "${API_URL}/versions"

# SOQLクエリ実行
curl -X POST "${API_URL}/query" \
  -H "Content-Type: application/json" \
  -d '{"action":"query","soql":"SELECT Id, Name FROM Account LIMIT 5"}'
```

## 🔍 トラブルシューティング

### エラー: "no client credentials user enabled"

**原因**: Salesforce側でClient Credentials Flowが有効になっていない

**解決方法**:
1. Salesforce Setup → App Manager
2. 接続アプリケーションを編集
3. 「Enable Client Credentials Flow」をチェック
4. Client Credentials用のユーザーを設定

### エラー: "invalid_client"

**原因**: Client IDまたはClient Secretが間違っている

**解決方法**:
1. Salesforceの接続アプリケーションでConsumer KeyとConsumer Secretを確認
2. Lambda関数の環境変数を更新

### エラー: "request not supported on this domain"

**原因**: Token URLが間違っている

**解決方法**:
1. Developer Edition環境の場合、カスタムドメインURLを使用
2. 正しいURL: `https://[your-domain].develop.my.salesforce.com/services/oauth2/token`

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 サポート

問題が発生した場合は、GitHubのIssuesで報告してください。
