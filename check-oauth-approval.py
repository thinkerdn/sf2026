#!/usr/bin/env python3
"""
Salesforce OAuth承認ヘルパースクリプト

このスクリプトは、JWT Bearer認証で必要なユーザー承認を行うための
承認URLを生成します。

使用方法:
    python check-oauth-approval.py
"""

import webbrowser

# sf-connect.pyの設定値を使用
consumer_key = '3MVG9HtWXcDGV.nEIQERv68uqfRaaJag3_LzlSUyLGPzOUqAWAVpBPKABo7QeFDRyrXIltqlaeZ.hgyDMt.QM'
redirect_uri = 'https://login.salesforce.com/services/oauth2/callback'
auth_url = 'https://orgfarm-e3d99ff5bd-dev-ed.develop.my.salesforce.com'

# 承認URLを生成
approval_url = f"{auth_url}/services/oauth2/authorize?response_type=code&client_id={consumer_key}&redirect_uri={redirect_uri}"

print("=" * 80)
print("Salesforce OAuth承認ヘルパー")
print("=" * 80)
print()
print("エラー: 'user hasn't approved this consumer' の解決方法")
print()
print("以下のURLをブラウザで開いて、ユーザー（conn_test@thinkerdn.net）で")
print("ログインし、接続アプリケーションを承認してください:")
print()
print(approval_url)
print()
print("=" * 80)
print()
print("手順:")
print("1. 上記のURLをコピーしてブラウザで開く")
print("2. ユーザー: conn_test@thinkerdn.net でログイン")
print("3. 「許可」ボタンをクリックして接続アプリケーションを承認")
print("4. 承認後、再度 'python sf-connect.py' を実行")
print()
print("=" * 80)
print()

# ユーザーに確認
response = input("ブラウザで自動的にURLを開きますか？ (y/n): ")
if response.lower() in ['y', 'yes', 'はい']:
    print("ブラウザを開いています...")
    webbrowser.open(approval_url)
    print("ブラウザで承認を完了してください。")
else:
    print("上記のURLを手動でブラウザにコピーして開いてください。")
