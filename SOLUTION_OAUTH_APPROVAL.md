# Salesforce OAuth承認エラーの解決方法

## エラー内容
```
Response Status: 400
Response Body: {"error":"invalid_grant","error_description":"user hasn't approved this consumer"}
```

## 原因
JWT Bearer認証フローでは、ユーザーが接続アプリケーション（Consumer/外部クライアントアプリケーション）を承認する必要があります。このエラーは承認が完了していないことを示しています。

---

## 解決方法（推奨順）

### ✅ 方法1: 管理者による事前承認設定【最も確実】

この方法では、管理者が設定することでユーザーの手動承認を不要にします。

#### ステップ1: 接続アプリケーションの編集

1. **Salesforce Setupにログイン**（管理者アカウント）
   - URL: `https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com/lightning/setup/SetupOneHome/home`

2. **App Managerを開く**
   - Quick Find で「App Manager」を検索
   - または Setup → Apps → App Manager

3. **接続アプリケーションを探す**
   - Consumer Key: `3MVG9HtWXcDGV.nEIQERv68uqfRaaJag3_LzlSUyLGPzOUqAWAVpBPKABo7QeFDRyrXIltqlaeZ.hgyDMt.QM`
   - このConsumer Keyを持つアプリケーションを見つける

4. **編集（Edit）をクリック**

#### ステップ2: OAuth設定の確認と変更

1. **OAuth Settingsセクションを確認**
   - ✅ 「Enable OAuth Settings」がチェックされている
   - ✅ 「Callback URL」が設定されている
     - 例: `https://login.salesforce.com/services/oauth2/callback`
   - ✅ 「Selected OAuth Scopes」に以下が含まれている:
     - `Access and manage your data (api)`
     - `Perform requests on your behalf at any time (refresh_token, offline_access)`
     - `Full access (full)` ※必要に応じて

2. **事前承認を有効化**
   - ✅ 「Admin approved users are pre-authorized」にチェックを入れる
   - これが最も重要な設定です！

3. **保存（Save）**

#### ステップ3: ユーザーへのアクセス権限付与

1. **接続アプリケーションの詳細ページに戻る**
   - Setup → App Manager → [Your Connected App] → View

2. **「Manage」ボタンをクリック**

3. **プロファイルまたは権限セットを割り当て**
   
   **オプションA: プロファイルで割り当て**
   - 「Manage Profiles」をクリック
   - ユーザー `conn_test@thinkerdn.net` のプロファイルを選択
     - 例: System Administrator, Standard User など
   - 保存

   **オプションB: 権限セットで割り当て（推奨）**
   - 「Manage Permission Sets」をクリック
   - 適切な権限セットを選択
   - 保存

#### ステップ4: OAuth Policiesの確認

1. **接続アプリケーションの管理画面**
   - Setup → App Manager → [Your Connected App] → Manage

2. **「Edit Policies」をクリック**

3. **以下の設定を確認**
   - **Permitted Users**: 
     - 「Admin approved users are pre-authorized」を選択
   - **IP Relaxation**: 
     - 「Relax IP restrictions」を選択（開発環境の場合）
   - **Refresh Token Policy**:
     - 「Refresh token is valid until revoked」を選択

4. **保存**

#### ステップ5: テスト

```bash
python sf-connect.py
```

これで承認なしで動作するはずです！

---

### ✅ 方法2: ユーザーによる手動承認

管理者設定ができない場合、ユーザーが手動で承認します。

#### ステップ1: 承認URLを開く

以下のURLをブラウザで開きます：

```
https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com/services/oauth2/authorize?response_type=code&client_id=3MVG9HtWXcDGV.nEIQERv68uqfRaaJag3_LzlSUyLGPzOUqAWAVpBPKABo7QeFDRyrXIltqlaeZ.hgyDMt.QM&redirect_uri=https://login.salesforce.com/services/oauth2/callback&scope=api%20refresh_token%20full
```

または、ヘルパースクリプトを使用：
```bash
python check-oauth-approval.py
```

#### ステップ2: ログインと承認

1. **ユーザーでログイン**
   - Username: `conn_test@thinkerdn.net`
   - Password: （ユーザーのパスワード）

2. **承認画面が表示される**
   - アプリケーション名が表示されます
   - 要求される権限が表示されます

3. **「許可（Allow）」ボタンをクリック**

4. **リダイレクト後のURLを確認**
   - エラーが表示されず、正常にリダイレクトされることを確認
   - URLに `code=` パラメータが含まれていればOK

#### ステップ3: テスト

```bash
python sf-connect.py
```

---

### ⚠️ トラブルシューティング

#### 問題1: 承認画面が表示されない

**原因**: Callback URLが正しく設定されていない

**解決方法**:
1. Setup → App Manager → [Your Connected App] → Edit
2. Callback URL を確認:
   ```
   https://login.salesforce.com/services/oauth2/callback
   ```
3. 複数のCallback URLを設定する場合は改行で区切る

#### 問題2: 承認後もエラーが続く

**原因**: 承認が正しく保存されていない、またはセッションの問題

**解決方法**:
1. ブラウザのキャッシュとCookieをクリア
2. 再度承認URLを開いてログイン
3. または、管理者による事前承認設定（方法1）を使用

#### 問題3: "redirect_uri_mismatch" エラー

**原因**: 承認URLのredirect_uriと接続アプリケーションの設定が一致していない

**解決方法**:
1. 接続アプリケーションのCallback URLを確認
2. 承認URLの `redirect_uri` パラメータを一致させる
3. 両方とも完全に同じURLである必要があります

#### 問題4: "invalid_client_id" エラー

**原因**: Consumer Keyが間違っている

**解決方法**:
1. Setup → App Manager → [Your Connected App] → View
2. Consumer Key を確認
3. `sf-connect.py` の `consumer_key` を更新

---

## 確認チェックリスト

承認が正しく設定されているか確認：

- [ ] 接続アプリケーションで「Enable OAuth Settings」がチェックされている
- [ ] 「Admin approved users are pre-authorized」がチェックされている
- [ ] ユーザーのプロファイルまたは権限セットが割り当てられている
- [ ] OAuth Scopesに必要な権限（api, refresh_token等）が含まれている
- [ ] Callback URLが正しく設定されている
- [ ] ユーザー名（`conn_test@thinkerdn.net`）が正しい
- [ ] Consumer Keyが正しい
- [ ] 秘密鍵ファイル（`sf-dev.key`）が正しい
- [ ] Token URLとAudience URLが一致している

---

## 設定確認用のSOQLクエリ

承認後、以下のSOQLで接続アプリケーションの承認状況を確認できます：

```sql
SELECT Id, UserId, User.Username, SalesforceOAuthTokenId, CreatedDate 
FROM UserOAuthToken 
WHERE User.Username = 'conn_test@thinkerdn.net'
```

このクエリは、Developer Consoleまたは Workbenchで実行できます。

---

## 参考情報

### Salesforce公式ドキュメント

- [OAuth 2.0 JWT Bearer Flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm)
- [Connected Apps](https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm)
- [Pre-Authorize Connected Apps](https://help.salesforce.com/s/articleView?id=sf.connected_app_manage_oauth.htm)

### 関連ファイル

- `sf-connect.py` - JWT Bearer認証スクリプト
- `check-oauth-approval.py` - OAuth承認ヘルパースクリプト
- `TROUBLESHOOTING.md` - 総合トラブルシューティングガイド

---

## まとめ

**最も確実な解決方法**: 管理者による事前承認設定（方法1）

この設定により：
- ユーザーの手動承認が不要になる
- 自動化されたプロセスで使用可能
- セキュリティを維持しながら運用が簡単

設定後は `python sf-connect.py` が正常に動作します。
