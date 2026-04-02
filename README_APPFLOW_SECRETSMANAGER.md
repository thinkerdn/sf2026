# Salesforce AppFlow Custom Connector (Secrets Manager版)

AWS Secrets Managerから認証情報を取得してSalesforceにClient Credentials方式で接続するAppFlowカスタムコネクタです。

## 概要

このLambda関数は、AWS AppFlowのカスタムコネクタとして動作し、Salesforce REST APIにアクセスします。認証情報はAWS Secrets Managerに安全に保存され、環境変数にハードコードする必要がありません。

## アーキテクチャ

```
AppFlow → Lambda関数 → Secrets Manager → Salesforce API
                ↓
         認証情報取得
```

## 主な機能

- ✅ **Secrets Manager統合**: 認証情報を安全に管理
- ✅ **Client Credentials認証**: サーバー間通信に最適
- ✅ **キャッシング**: Lambda実行環境の再利用時に高速化
- ✅ **エラーハンドリング**: 詳細なエラーメッセージ
- ✅ **AppFlow完全対応**: 全操作をサポート

## 前提条件

1. **AWS CLI**: バージョン2.x以上
2. **SAM CLI**: AWS Serverless Application Model CLI
3. **Python**: 3.11以上
4. **Salesforce接続アプリ**: Client Credentials方式が有効

## セットアップ手順

### 1. Secrets Managerにシークレットを作成

```bash
# AWS CLIでシークレットを作成
aws secretsmanager create-secret \
  --name salesforce/client-credentials \
  --description "Salesforce Client Credentials for AppFlow" \
  --secret-string '{
    "client_id": "3MVG9HtWXcDGV.nEIQERv68uqfeoto.hXr79io4W6pyO4DFXgnRRXmDFegJ70U0G7tj54wr5NsFAcenrr83wp",
    "client_secret": "245C545D423DB3D770CE104B02B9DE6D81BBF41F802413FEE84B724B88359C70",
    "token_url": "https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com/services/oauth2/token"
  }' \
  --region ap-northeast-1
```

**シークレットの形式:**
```json
{
  "client_id": "Salesforceのコンシューマ鍵",
  "client_secret": "Salesforceのコンシューマの秘密",
  "token_url": "https://your-instance.salesforce.com/services/oauth2/token"
}
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt -t .
```

### 3. Lambda関数のデプロイ

#### SAM CLIを使用（推奨）

```bash
# ビルド
sam build -t template-appflow-secretsmanager.yaml

# デプロイ（初回）
sam deploy -t template-appflow-secretsmanager.yaml \
  --guided \
  --stack-name salesforce-appflow-connector-sm \
  --capabilities CAPABILITY_IAM

# デプロイ（2回目以降）
sam deploy -t template-appflow-secretsmanager.yaml
```

#### AWS CLIを使用

```bash
# デプロイパッケージを作成
zip -r lambda_appflow_connector_sm.zip \
  lambda_appflow_connector_secretsmanager.py \
  requests/ \
  urllib3/ \
  certifi/ \
  charset_normalizer/ \
  idna/

# Lambda関数を作成
aws lambda create-function \
  --function-name salesforce-appflow-connector-sm \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-appflow-role \
  --handler lambda_appflow_connector_secretsmanager.lambda_handler \
  --zip-file fileb://lambda_appflow_connector_sm.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{SECRET_NAME=salesforce/client-credentials,AWS_REGION=ap-northeast-1}" \
  --region ap-northeast-1

# Lambda関数を更新
aws lambda update-function-code \
  --function-name salesforce-appflow-connector-sm \
  --zip-file fileb://lambda_appflow_connector_sm.zip \
  --region ap-northeast-1
```

### 4. IAMロールの設定

Lambda関数には以下の権限が必要です：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:ap-northeast-1:YOUR_ACCOUNT_ID:secret:salesforce/client-credentials*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:ap-northeast-1:YOUR_ACCOUNT_ID:log-group:/aws/lambda/salesforce-appflow-connector-sm:*"
    }
  ]
}
```

### 5. AppFlowでカスタムコネクタを登録

1. **AWS AppFlow Console**を開く
2. **Connectors** → **Create custom connector**をクリック
3. 以下の情報を入力：
   - **Connector label**: Salesforce Client Credentials (SM)
   - **Lambda function**: salesforce-appflow-connector-sm
4. **Register connector**をクリック

### 6. 接続プロファイルの作成

1. **Connections** → **Create connection**をクリック
2. **Connector**: Salesforce Client Credentials (SM)を選択
3. **Connection name**: 任意の名前を入力
4. **Client ID**: Salesforceのコンシューマ鍵（表示のみ、Secrets Managerから取得）
5. **Client Secret**: Salesforceのコンシューマの秘密（表示のみ、Secrets Managerから取得）
6. **Connect**をクリック

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------------|
| `SECRET_NAME` | Secrets Managerのシークレット名 | `salesforce/client-credentials` |
| `AWS_REGION` | AWSリージョン | `ap-northeast-1` |

## Secrets Managerの管理

### シークレットの更新

```bash
# シークレットを更新
aws secretsmanager update-secret \
  --secret-id salesforce/client-credentials \
  --secret-string '{
    "client_id": "NEW_CLIENT_ID",
    "client_secret": "NEW_CLIENT_SECRET",
    "token_url": "https://your-instance.salesforce.com/services/oauth2/token"
  }' \
  --region ap-northeast-1
```

### シークレットの取得（確認用）

```bash
# シークレットの値を取得
aws secretsmanager get-secret-value \
  --secret-id salesforce/client-credentials \
  --region ap-northeast-1 \
  --query SecretString \
  --output text | jq .
```

### シークレットのローテーション設定

```bash
# 自動ローテーションを有効化（オプション）
aws secretsmanager rotate-secret \
  --secret-id salesforce/client-credentials \
  --rotation-lambda-arn arn:aws:lambda:ap-northeast-1:YOUR_ACCOUNT_ID:function:SecretsManagerRotation \
  --rotation-rules AutomaticallyAfterDays=30 \
  --region ap-northeast-1
```

## ローカルテスト

### 環境変数を設定

```bash
# Linux/Mac
export SECRET_NAME=salesforce/client-credentials
export AWS_REGION=ap-northeast-1

# Windows (PowerShell)
$env:SECRET_NAME="salesforce/client-credentials"
$env:AWS_REGION="ap-northeast-1"

# Windows (CMD)
set SECRET_NAME=salesforce/client-credentials
set AWS_REGION=ap-northeast-1
```

### テスト実行

```bash
python lambda_appflow_connector_secretsmanager.py
```

## トラブルシューティング

### エラー: Secret not found

**原因**: Secrets Managerにシークレットが存在しない

**解決策**:
```bash
# シークレットが存在するか確認
aws secretsmanager describe-secret \
  --secret-id salesforce/client-credentials \
  --region ap-northeast-1
```

### エラー: Access Denied

**原因**: Lambda関数にSecrets Managerへのアクセス権限がない

**解決策**:
1. Lambda関数のIAMロールを確認
2. `secretsmanager:GetSecretValue`権限を追加

### エラー: Invalid JSON in secret

**原因**: Secrets Managerのシークレットが正しいJSON形式でない

**解決策**:
```bash
# シークレットの値を確認
aws secretsmanager get-secret-value \
  --secret-id salesforce/client-credentials \
  --region ap-northeast-1 \
  --query SecretString \
  --output text | jq .

# 正しい形式で更新
aws secretsmanager update-secret \
  --secret-id salesforce/client-credentials \
  --secret-string '{"client_id":"...","client_secret":"...","token_url":"..."}' \
  --region ap-northeast-1
```

### エラー: Failed to get access token

**原因**: Salesforceの認証情報が正しくない

**解決策**:
1. Secrets Managerのシークレット値を確認
2. Salesforce接続アプリの設定を確認
3. Client Credentials方式が有効になっているか確認

## セキュリティのベストプラクティス

1. **最小権限の原則**: Lambda関数には必要最小限の権限のみを付与
2. **シークレットの暗号化**: Secrets Managerは自動的にKMSで暗号化
3. **アクセスログ**: CloudTrailでSecrets Managerへのアクセスを監視
4. **定期的なローテーション**: 認証情報を定期的に更新
5. **VPC内での実行**: 必要に応じてLambda関数をVPC内で実行

## コスト

### Secrets Manager
- シークレット保存: $0.40/月/シークレット
- API呼び出し: $0.05/10,000回

### Lambda
- 実行時間: $0.0000166667/GB秒
- リクエスト: $0.20/100万リクエスト

### AppFlow
- フロー実行: データ量に応じて課金

**推定月額コスト** (1日100回実行の場合):
- Secrets Manager: $0.40
- Lambda: $0.50
- 合計: 約$1/月

## パフォーマンス最適化

1. **キャッシング**: Lambda実行環境の再利用時にシークレットをキャッシュ
2. **メモリ設定**: 256MBで十分（必要に応じて調整）
3. **タイムアウト**: 30秒（通常は5秒以内に完了）
4. **同時実行数**: デフォルトで十分（必要に応じて予約済み同時実行数を設定）

## 監視とログ

### CloudWatch Logs

```bash
# ログを確認
aws logs tail /aws/lambda/salesforce-appflow-connector-sm --follow
```

### CloudWatch Metrics

- **Invocations**: 呼び出し回数
- **Duration**: 実行時間
- **Errors**: エラー数
- **Throttles**: スロットリング数

### アラーム設定

```bash
# エラー率のアラームを作成
aws cloudwatch put-metric-alarm \
  --alarm-name salesforce-appflow-connector-sm-errors \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=salesforce-appflow-connector-sm
```

## 関連ドキュメント

- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [AWS AppFlow](https://docs.aws.amazon.com/appflow/)
- [Salesforce REST API](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/)
- [OAuth 2.0 Client Credentials](https://oauth.net/2/grant-types/client-credentials/)

## ライセンス

MIT License

## サポート

問題が発生した場合は、以下を確認してください：
1. CloudWatch Logsでエラーメッセージを確認
2. Secrets Managerのシークレット値を確認
3. IAMロールの権限を確認
4. Salesforce接続アプリの設定を確認
