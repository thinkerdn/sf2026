# JWT認証エラー解決手順

## エラー内容

### エラー1: user hasn't approved this consumer
```
{"error":"invalid_grant","error_description":"user hasn't approved this consumer"}
```

### エラー2: user is not admin approved to access this app
```
{"error":"invalid_app_access","error_description":"user is not admin approved to access this app"}
```

### エラー3: invalid_client_id（現在のエラー）
```
{"error":"invalid_client_id","error_description":"client identifier invalid"}
```

これらのエラーは、Salesforce側の接続アプリケーション（Connected App）の設定が不完全であることを示しています。

## 解決手順

### 1. Salesforce接続アプリケーションの設定確認

1. **Salesforceにログイン**して、[設定] > [アプリケーションマネージャー] に移動

2. **対象の接続アプリケーションを見つけて、右側の▼をクリック > [管理]**

3. **[ポリシーを編集]** をクリック

4. **以下の設定を変更：**
   - **[許可されたユーザー]**: 「**管理者が承認したユーザーは事前承認済み**」に変更
   - **[IP 制限]**: 「**IP 制限を緩和**」を選択

5. **[保存]** をクリック

### 2. プロファイルまたは権限セットの追加 ⚠️ **重要**

**エラー "user is not admin approved to access this app" の解決には、この手順が必須です。**

接続アプリケーションの管理画面（[設定] > [アプリケーションマネージャー] > 対象アプリの▼ > [管理]）で、下にスクロールして：

#### オプションA: プロファイルを追加
1. **[プロファイル]** セクションで **[プロファイルを管理]** をクリック
2. ユーザー `conn_test@thinkerdn.net` のプロファイルを選択してチェック
   - 例: 「システム管理者」「標準ユーザー」「カスタムプロファイル」など
3. **[保存]** をクリック

#### オプションB: 権限セットを追加（推奨）
1. **[権限セット]** セクションで **[権限セットを管理]** をクリック
2. ユーザー `conn_test@thinkerdn.net` に割り当てられている権限セットを選択してチェック
3. **[保存]** をクリック

**📝 確認方法:**
- ユーザーのプロファイルを確認: [設定] > [ユーザ] > ユーザー名をクリック > 「プロファイル」欄を確認
- ユーザーの権限セットを確認: 同じページの「権限セットの割り当て」関連リストを確認

### 3. デジタル署名の確認

接続アプリケーションの編集画面で：
1. **[デジタル署名を使用]** にチェックが入っていることを確認
2. 正しい公開鍵証明書（`sf-dev.crt`）がアップロードされていることを確認

### 4. 再テスト

上記の設定を完了したら、再度スクリプトを実行：
```bash
python sf-connect.py
```

## 参考情報

- ユーザー名: `conn_test@thinkerdn.net`
- Consumer Key: `3MVG9HtWXcDGV.nEIQERv68uqfXcPAvD.uUACicp1wEcD6s9U54eKfKi3Ijz9S8iZMiaSKW4mY6mFw16FffGd`
- Token URL: `https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com/services/oauth2/token`

## トラブルシューティング

### エラー3: invalid_client_id の解決方法 ⚠️

このエラーは **Consumer Key（コンシューマ鍵）が無効** であることを示しています。

**確認手順：**

1. **Salesforceで正しいConsumer Keyを取得**
   - [設定] > [アプリケーションマネージャー] に移動
   - 対象の接続アプリケーションの▼ > **[詳細を表示]** をクリック
   - **「コンシューマ鍵」** の値をコピー（長い英数字の文字列）

2. **sf-connect.pyのconsumer_keyを更新**
   ```python
   consumer_key = '正しいコンシューマ鍵をここに貼り付け'
   ```

3. **接続アプリケーションが有効であることを確認**
   - アプリケーションマネージャーで対象アプリが「有効」になっているか確認
   - 削除されていないか確認

4. **再テスト**
   ```bash
   python sf-connect.py
   ```

**よくある原因：**
- Consumer Keyをコピーする際に、前後にスペースが入っている
- 別の接続アプリケーションのConsumer Keyを使用している
- 接続アプリケーションが削除または無効化されている
- 接続アプリケーションを再作成した際に、古いConsumer Keyを使用している

### その他のエラーが続く場合：
1. ユーザー `conn_test@thinkerdn.net` が有効であることを確認
2. ユーザーが正しいプロファイル/権限セットを持っていることを確認
3. 秘密鍵と公開鍵のペアが正しいことを確認（同じ鍵ペアから生成されているか）
4. token_urlとaudのドメインが一致していることを確認
