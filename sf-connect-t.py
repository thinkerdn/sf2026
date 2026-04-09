import jwt
import time
import requests
from cryptography.hazmat.primitives import serialization

# --- 設定値 ---
username = 'gaibu_sys_icr_ts_hanbaiten_0714@toyotasystems.com.developer'
consumer_key = '3MVG95ol_2z.5OsOsJrbjsoq7uy8OsrssagOVOKF47H.DkWucMkTYAu0YkDbSMy4Jc4BVdQjIk9nPHcyUQjnF'
#consumer_key = '3MVG95ol_2z.5OsOsJrbjsoq7u8vcS0KP15Q4OEw6eBq2VtCmSxTsulDZqq02emelED9fFSjBRZx5jQBMdfkz'
key_file = 'sf-dev.key'  # 秘密鍵ファイルへのパス
token_url = "https://04401-toyota-crm--developer.sandbox.my.salesforce.com/services/oauth2/token"
# token_url = 'https://login.salesforce.com/services/oauth2/token' # 本番環境
# token_url = 'https://test.salesforce.com/services/oauth2/token' # Sandbox

# --- 1. 秘密鍵の読み込み ---
with open(key_file, 'rb') as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

# --- 2. JWTの生成 ---
payload = {
    'iss': consumer_key,
    'sub': username,
    'aud': 'https://04401-toyota-crm--developer.sandbox.my.salesforce.com', # 本番: login.salesforce.com, Sandbox: test.salesforce.com
    'exp': int(time.time()) + 60 * 60 * 24 * 365  # 1年間有効
}
assertion = jwt.encode(payload, private_key, algorithm='RS256')
print(f"exp: {int(time.time()) + 60 * 60 * 24 * 365}")
print(f"assertion: {assertion}")

# --- 3. アクセストークンの取得 ---

#Salesforce Login URL:

#https://04401-toyota-crm--developer.sandbox.my.salesforce.com/

#ユーザー名:

#gaibu_sys_icr_ts_hanbaiten_0714@toyotasystems.com.developer

#外部クライアントアプリケーション名:

#AWS_AppFlow_Connector

#顧客の詳細:

#• コンシューマー鍵:

#3MVG95ol_2z.5OsOsJrbjsoq7u8vcS0KP15Q4OEw6eBq2VtCmSxTsulDZqq02emelED9fFSjBRZx5jQBMdfkz

#• コンシューマーの秘密:

#B413D497D762E9E1CC95708A28BC7AB554E75861B873F8A3E45F153A1C963B18

#exp: 1775417188
#assertion: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzTVZHOTVvbF8yei41T3NPc0pyYmpzb3E3dTh2Y1MwS1AxNVE0T0V3NmVCcTJWdENtU3hUc3VsRFpxcTAyZW1lbEVEOWZGU2pCUlp4NWpRQk1kZmt6Iiwic3ViIjoiZ2FpYnVfc3lzX2ljcl90c19oYW5iYWl0ZW5fMDcxNEB0b3lvdGFzeXN0ZW1zLmNvbS5kZXZlbG9wZXIiLCJhdWQiOiJodHRwczovLzA0NDAxLXRveW90YS1jcm0tLWRldmVsb3Blci5zYW5kYm94Lm15LnNhbGVzZm9yY2UuY29tIiwiZXhwIjoxNzc1NDE2NDA5fQ.VZgGkVGFK6ZxsgiXQ08bx1wp58e2Br3bo_8nZZzWR_Wowp2HqQct7kXgUSQ42vda5LqeEF7YtX-pfOumwYSUnBrtIx836M_Aq9aa3DGxjUcAcI9sVZfhWFQee2IUvVERztYMRBw9imOx8c2x1KVX0CEKc__25e5KV1cjlo2l18JuVMtekQvR_rcx5yRGrnc3o8EOcAisUOVzkrntIFlTSEihtWM6cvu_jDqG204gJVI9j_2pPH9UZhBESIsMA0RfzIyCqVUZQHoxYRGSYaOgnnpsCXvpc9wzwgzlUvSoNBt8m9h8B8ghnE3S9bkBwDvrTGXns5poOdRNx8IOZdblSg
#assertion: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzTVZHOTVvbF8yei41T3NPc0pyYmpzb3E3dTh2Y1MwS1AxNVE0T0V3NmVCcTJWdENtU3hUc3VsRFpxcTAyZW1lbEVEOWZGU2pCUlp4NWpRQk1kZmt6Iiwic3ViIjoiZ2FpYnVfc3lzX2ljcl90c19oYW5iYWl0ZW5fMDcxNEB0b3lvdGFzeXN0ZW1zLmNvbS5kZXZlbG9wZXIiLCJhdWQiOiJodHRwczovLzA0NDAxLXRveW90YS1jcm0tLWRldmVsb3Blci5zYW5kYm94Lm15LnNhbGVzZm9yY2UuY29tIiwiZXhwIjoxNzc1NDE2NDA5fQ.VZgGkVGFK6ZxsgiXQ08bx1wp58e2Br3bo_8nZZzWR_Wowp2HqQct7kXgUSQ42vda5LqeEF7YtX-pfOumwYSUnBrtIx836M_Aq9aa3DGxjUcAcI9sVZfhWFQee2IUvVERztYMRBw9imOx8c2x1KVX0CEKc__25e5KV1cjlo2l18JuVMtekQvR_rcx5yRGrnc3o8EOcAisUOVzkrntIFlTSEihtWM6cvu_jDqG204gJVI9j_2pPH9UZhBESIsMA0RfzIyCqVUZQHoxYRGSYaOgnnpsCXvpc9wzwgzlUvSoNBt8m9h8B8ghnE3S9bkBwDvrTGXns5poOdRNx8IOZdblSg
#exp: 1775500427
#assertion: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzTVZHOTVvbF8yei41T3NPc0pyYmpzb3E3dXk4T3Nyc3NhZ09WT0tGNDdILkRrV3VjTWtUWUF1MFlrRGJTTXk0SmM0QlZkUWpJazluUEhjeVVRam5GIiwic3ViIjoiZ2FpYnVfc3lzX2ljcl90c19oYW5iYWl0ZW5fMDcxNEB0b3lvdGFzeXN0ZW1zLmNvbS5kZXZlbG9wZXIiLCJhdWQiOiJodHRwczovLzA0NDAxLXRveW90YS1jcm0tLWRldmVsb3Blci5zYW5kYm94Lm15LnNhbGVzZm9yY2UuY29tIiwiZXhwIjoxNzc1NDE2NDA5fQ.Jae1hIDfEkDjX-QPBf7gxXPA1DEoeExC9JTPkggxj21rPyLExrrxZRJi5NSlx_2EMSwsNDIhZoZJhKeDGqGpl9Epzbv4cQtz5hEu2pe9Kmqw1UoxXxaytSRE_8hJSGk0OLop_ud0iE7oCMPfWr_cvxLC04rrzvA_-8zXO6AskDusM2GIljWH5rgW4pLsuSutQroQIKG-1lv0Rj9yp1UaUTScv99kRmax2LgvL3VnCVp3oEjCQjHzDBZHawCSq4sEoBlVO2FD0NvSVKpzPsnp072AAOxvdkSyYfywaiRlOMJwJRTwACIuKOLiK_-4jLg2R9Ybm1CKOa8FQ-bH23PyjQ




eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzTVZHOTVvbF8yei41T3NPc0pyYmpzb3E3dXk4T3Nyc3NhZ09WT0tGNDdILkRrV3VjTWtUWUF1MFlrRGJTTXk0SmM0QlZkUWpJazluUEhjeVVRam5GIiwic3ViIjoiZ2FpYnVfc3lzX2ljcl90c19oYW5iYWl0ZW5fMDcxNEB0b3lvdGFzeXN0ZW1zLmNvbS5kZXZlbG9wZXIiLCJhdWQiOiJodHRwczovLzA0NDAxLXRveW90YS1jcm0tLWRldmVsb3Blci5zYW5kYm94Lm15LnNhbGVzZm9yY2UuY29tIiwiZXhwIjoxODA3MDAzNjA5fQ.dAFooV4pSupJmDM1oLiBjTBTZ_4mkIUc_jgae770YkivnlNFu6hqrhXMWt7xZ0Jtf2t6wDhRFWo-EhO7BuCfE_iJl8Fl4DTb2k41xJbwyKu-efHOzgK7lKzNZ80TaGvEKtSPX941WqmPUr91lV3o3LICCuz3ZPQ8Tw6vEitVKO2TloM8yXj4J-yBj7ItLefQWXhYOKKuiA9G8hbdlBK1lPm3mmpFayzaziTM6dIBedKV1u9FnvQWW5kYi9rKcdragDPhv1txauLWQPZqp0xhbiFm-BnP1G-2xGqfVHcQa7n4jwmBETxq4j2ROGhmcbMVB5vQmpy1nM-TrLpEuCCnGQ