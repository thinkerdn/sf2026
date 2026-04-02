"""
AWS Lambda関数: Salesforce AppFlow Custom Connector (Secrets Manager版)
AppFlowのカスタムコネクタとしてSalesforceにClient Credentials方式で接続
認証情報はAWS Secrets Managerから取得
"""

import json
import os
import boto3
import requests
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# Secrets Manager設定
SECRET_NAME = os.environ.get('SECRET_NAME', 'salesforce/client-credentials')
REGION_NAME = os.environ.get('AWS_REGION', 'ap-northeast-1')

# Secrets Managerクライアント（グローバル変数でキャッシュ）
secrets_client = None
cached_secret = None

def get_secrets_manager_client():
    """
    Secrets Managerクライアントを取得（キャッシュ）
    """
    global secrets_client
    if secrets_client is None:
        secrets_client = boto3.client('secretsmanager', region_name=REGION_NAME)
    return secrets_client

def get_salesforce_credentials():
    """
    AWS Secrets ManagerからSalesforce認証情報を取得
    
    Secretの形式:
    {
        "client_id": "3MVG9...",
        "client_secret": "245C545D...",
        "token_url": "https://orgfarm-xxx.salesforce.com/services/oauth2/token"
    }
    """
    global cached_secret
    
    # キャッシュがあれば返す（Lambda実行環境の再利用時に高速化）
    if cached_secret is not None:
        return cached_secret
    
    try:
        client = get_secrets_manager_client()
        
        # Secretを取得
        response = client.get_secret_value(SecretId=SECRET_NAME)
        
        # Secretの値を解析
        if 'SecretString' in response:
            secret_data = json.loads(response['SecretString'])
        else:
            # バイナリシークレットの場合（通常は使用しない）
            import base64
            secret_data = json.loads(base64.b64decode(response['SecretBinary']))
        
        # 必須フィールドの検証
        required_fields = ['client_id', 'client_secret', 'token_url']
        for field in required_fields:
            if field not in secret_data:
                raise ValueError(f"Missing required field in secret: {field}")
        
        # キャッシュに保存
        cached_secret = secret_data
        
        print(f"Successfully retrieved credentials from Secrets Manager: {SECRET_NAME}")
        return secret_data
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            raise Exception(f"Secret not found: {SECRET_NAME}")
        elif error_code == 'InvalidRequestException':
            raise Exception(f"Invalid request to Secrets Manager: {str(e)}")
        elif error_code == 'InvalidParameterException':
            raise Exception(f"Invalid parameter: {str(e)}")
        elif error_code == 'DecryptionFailure':
            raise Exception(f"Cannot decrypt secret: {str(e)}")
        elif error_code == 'InternalServiceError':
            raise Exception(f"Secrets Manager internal error: {str(e)}")
        else:
            raise Exception(f"Failed to retrieve secret: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON in secret: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error retrieving credentials: {str(e)}")

def get_salesforce_access_token():
    """
    Client Credentials方式でSalesforceのアクセストークンを取得
    """
    try:
        # Secrets Managerから認証情報を取得
        credentials = get_salesforce_credentials()
        
        params = {
            'grant_type': 'client_credentials',
            'client_id': credentials['client_id'],
            'client_secret': credentials['client_secret']
        }
        
        response = requests.post(credentials['token_url'], data=params)
        response.raise_for_status()
        
        token_data = response.json()
        return {
            'access_token': token_data['access_token'],
            'instance_url': token_data['instance_url'],
            'token_type': token_data.get('token_type', 'Bearer'),
            'issued_at': token_data.get('issued_at'),
            'signature': token_data.get('signature')
        }
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get access token: {str(e)}")

def validate_credentials(event):
    """
    AppFlow用: 認証情報の検証
    """
    try:
        token_info = get_salesforce_access_token()
        return {
            'isSuccess': True,
            'message': 'Credentials validated successfully'
        }
    except Exception as e:
        return {
            'isSuccess': False,
            'message': f'Credential validation failed: {str(e)}'
        }

def describe_connector_configuration(event):
    """
    AppFlow用: コネクタの設定情報を返す
    """
    return {
        'isSuccess': True,
        'connectorOwner': 'Custom',
        'connectorName': 'Salesforce-Client-Credentials-SM',
        'connectorVersion': '1.0',
        'connectorModes': ['SOURCE', 'DESTINATION'],
        'supportedApiVersions': ['v1'],
        'authenticationConfig': {
            'isBasicAuthSupported': False,
            'isApiKeyAuthSupported': False,
            'isOAuth2Supported': False,
            'isCustomAuthSupported': True,
            'customAuthConfig': [
                {
                    'authenticationType': 'OAUTH2',
                    'authParameters': [
                        {
                            'key': 'client_id',
                            'required': True,
                            'label': 'Client ID',
                            'description': 'Salesforce Consumer Key',
                            'isSensitiveField': False
                        },
                        {
                            'key': 'client_secret',
                            'required': True,
                            'label': 'Client Secret',
                            'description': 'Salesforce Consumer Secret',
                            'isSensitiveField': True
                        }
                    ]
                }
            ]
        },
        'connectorConfiguration': {
            'isPrivateLinkEnabled': False,
            'isPrivateLinkEndpointUrlRequired': False,
            'supportedAuthenticationTypes': ['OAUTH2'],
            'supportedWriteOperations': ['INSERT', 'UPDATE', 'UPSERT'],
            'supportedSchedulingFrequencies': ['BYMINUTE', 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY', 'ONCE']
        }
    }

def describe_connector_entity(event):
    """
    AppFlow用: エンティティ（オブジェクト）の詳細情報を返す
    """
    entity_identifier = event.get('entityIdentifier', 'User')
    
    try:
        token_info = get_salesforce_access_token()
        
        # Salesforce Describe APIを呼び出し
        describe_url = f"{token_info['instance_url']}/services/data/v66.0/sobjects/{entity_identifier}/describe"
        headers = {
            'Authorization': f"Bearer {token_info['access_token']}",
            'Content-Type': 'application/json'
        }
        
        response = requests.get(describe_url, headers=headers)
        response.raise_for_status()
        
        describe_data = response.json()
        
        # フィールド情報を変換
        fields = []
        for field in describe_data.get('fields', []):
            fields.append({
                'fieldName': field['name'],
                'dataType': map_salesforce_type_to_appflow(field['type']),
                'label': field.get('label', field['name']),
                'description': field.get('inlineHelpText', ''),
                'isRequired': not field.get('nillable', True),
                'isReadOnly': not field.get('updateable', False),
                'isPrimaryKey': field.get('idLookup', False)
            })
        
        return {
            'isSuccess': True,
            'entityDefinition': {
                'entityIdentifier': entity_identifier,
                'label': describe_data.get('label', entity_identifier),
                'hasNestedEntities': False,
                'fields': fields
            }
        }
    except Exception as e:
        return {
            'isSuccess': False,
            'message': f'Failed to describe entity: {str(e)}'
        }

def list_connector_entities(event):
    """
    AppFlow用: 利用可能なエンティティ（オブジェクト）のリストを返す
    """
    try:
        token_info = get_salesforce_access_token()
        
        # Salesforce Global Describe APIを呼び出し
        describe_url = f"{token_info['instance_url']}/services/data/v66.0/sobjects"
        headers = {
            'Authorization': f"Bearer {token_info['access_token']}",
            'Content-Type': 'application/json'
        }
        
        response = requests.get(describe_url, headers=headers)
        response.raise_for_status()
        
        sobjects_data = response.json()
        
        # エンティティリストを作成
        entities = []
        for sobject in sobjects_data.get('sobjects', []):
            # Client Credentialsでアクセス可能なオブジェクトのみをフィルタ
            if sobject.get('queryable', False):
                entities.append({
                    'entityIdentifier': sobject['name'],
                    'label': sobject.get('label', sobject['name']),
                    'hasNestedEntities': False
                })
        
        return {
            'isSuccess': True,
            'entities': entities[:100]  # 最初の100件を返す
        }
    except Exception as e:
        return {
            'isSuccess': False,
            'message': f'Failed to list entities: {str(e)}'
        }

def query_connector_data(event):
    """
    AppFlow用: データのクエリを実行
    """
    try:
        token_info = get_salesforce_access_token()
        
        # イベントからパラメータを取得
        entity_identifier = event.get('entityIdentifier', 'User')
        selected_fields = event.get('selectedFieldNames', ['Id'])
        max_results = event.get('maxResults', 100)
        filter_expression = event.get('filterExpression', '')
        
        # SOQLクエリを構築
        fields_str = ', '.join(selected_fields)
        soql = f"SELECT {fields_str} FROM {entity_identifier}"
        
        if filter_expression:
            soql += f" WHERE {filter_expression}"
        
        soql += f" LIMIT {max_results}"
        
        # クエリを実行
        query_url = f"{token_info['instance_url']}/services/data/v66.0/query"
        headers = {
            'Authorization': f"Bearer {token_info['access_token']}",
            'Content-Type': 'application/json'
        }
        params = {'q': soql}
        
        response = requests.get(query_url, headers=headers, params=params)
        
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = json.dumps(error_json)
            except:
                pass
            return {
                'isSuccess': False,
                'message': f'Query failed: {error_detail}'
            }
        
        query_result = response.json()
        
        # レコードを変換
        records = []
        for record in query_result.get('records', []):
            # attributes フィールドを除外
            record_data = {k: v for k, v in record.items() if k != 'attributes'}
            records.append(record_data)
        
        return {
            'isSuccess': True,
            'records': records,
            'nextToken': query_result.get('nextRecordsUrl', None)
        }
    except Exception as e:
        return {
            'isSuccess': False,
            'message': f'Failed to query data: {str(e)}'
        }

def write_connector_data(event):
    """
    AppFlow用: データの書き込み（INSERT/UPDATE/UPSERT）
    """
    try:
        token_info = get_salesforce_access_token()
        
        # イベントからパラメータを取得
        entity_identifier = event.get('entityIdentifier')
        operation = event.get('operation', 'INSERT')  # INSERT, UPDATE, UPSERT
        records = event.get('records', [])
        
        if not entity_identifier or not records:
            return {
                'isSuccess': False,
                'message': 'entityIdentifier and records are required'
            }
        
        headers = {
            'Authorization': f"Bearer {token_info['access_token']}",
            'Content-Type': 'application/json'
        }
        
        results = []
        
        for record in records:
            try:
                if operation == 'INSERT':
                    # レコードを作成
                    url = f"{token_info['instance_url']}/services/data/v66.0/sobjects/{entity_identifier}"
                    response = requests.post(url, headers=headers, json=record)
                    
                elif operation == 'UPDATE':
                    # レコードを更新
                    record_id = record.get('Id')
                    if not record_id:
                        results.append({
                            'isSuccess': False,
                            'message': 'Id is required for UPDATE operation'
                        })
                        continue
                    
                    # Idを除外
                    update_data = {k: v for k, v in record.items() if k != 'Id'}
                    url = f"{token_info['instance_url']}/services/data/v66.0/sobjects/{entity_identifier}/{record_id}"
                    response = requests.patch(url, headers=headers, json=update_data)
                    
                elif operation == 'UPSERT':
                    # 外部IDでUpsert
                    external_id_field = event.get('externalIdFieldName', 'Id')
                    external_id_value = record.get(external_id_field)
                    
                    if not external_id_value:
                        results.append({
                            'isSuccess': False,
                            'message': f'{external_id_field} is required for UPSERT operation'
                        })
                        continue
                    
                    url = f"{token_info['instance_url']}/services/data/v66.0/sobjects/{entity_identifier}/{external_id_field}/{external_id_value}"
                    response = requests.patch(url, headers=headers, json=record)
                
                if response.status_code in [200, 201, 204]:
                    result_data = response.json() if response.text else {}
                    results.append({
                        'isSuccess': True,
                        'recordId': result_data.get('id', external_id_value if operation == 'UPSERT' else None)
                    })
                else:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = json.dumps(error_json)
                    except:
                        pass
                    results.append({
                        'isSuccess': False,
                        'message': f'Operation failed: {error_detail}'
                    })
                    
            except Exception as e:
                results.append({
                    'isSuccess': False,
                    'message': str(e)
                })
        
        return {
            'isSuccess': True,
            'results': results
        }
    except Exception as e:
        return {
            'isSuccess': False,
            'message': f'Failed to write data: {str(e)}'
        }

def map_salesforce_type_to_appflow(sf_type):
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
        'id': 'String',
        'reference': 'String',
        'int': 'Integer',
        'double': 'Double',
        'currency': 'Double',
        'percent': 'Double',
        'boolean': 'Boolean',
        'date': 'Date',
        'datetime': 'Datetime',
        'time': 'Time'
    }
    return type_mapping.get(sf_type.lower(), 'String')

def lambda_handler(event, context):
    """
    AppFlow Custom Connector Lambda Handler (Secrets Manager版)
    
    AppFlowから呼び出される際のイベント構造:
    {
        "operation": "ValidateCredentials" | "DescribeConnectorConfiguration" | 
                     "DescribeConnectorEntity" | "ListConnectorEntities" | 
                     "QueryConnectorData" | "WriteConnectorData",
        ... その他のパラメータ
    }
    """
    
    print(f"Event: {json.dumps(event)}")
    print(f"Using Secrets Manager: {SECRET_NAME} in region {REGION_NAME}")
    
    try:
        operation = event.get('operation')
        
        # operationがNoneまたは空の場合、デフォルトでDescribeConnectorConfigurationを返す
        if not operation or operation == 'None':
            print("Operation is None or empty, returning DescribeConnectorConfiguration")
            result = describe_connector_configuration(event)
            
        elif operation == 'ValidateCredentials':
            result = validate_credentials(event)
            
        elif operation == 'DescribeConnectorConfiguration':
            result = describe_connector_configuration(event)
            
        elif operation == 'DescribeConnectorEntity':
            result = describe_connector_entity(event)
            
        elif operation == 'ListConnectorEntities':
            result = list_connector_entities(event)
            
        elif operation == 'QueryConnectorData':
            result = query_connector_data(event)
            
        elif operation == 'WriteConnectorData':
            result = write_connector_data(event)
            
        else:
            # 不明なoperationの場合もDescribeConnectorConfigurationを返す
            print(f"Unknown operation: {operation}, returning DescribeConnectorConfiguration")
            result = describe_connector_configuration(event)
        
        print(f"Result: {json.dumps(result)}")
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'isSuccess': False,
            'connectorOwner': 'Custom',
            'connectorName': 'Salesforce-Client-Credentials-SM',
            'connectorVersion': '1.0',
            'message': f'Internal error: {str(e)}'
        }

# ローカルテスト用
if __name__ == '__main__':
    # ローカルテスト時は環境変数を設定
    # export SECRET_NAME=salesforce/client-credentials
    # export AWS_REGION=ap-northeast-1
    
    print("="*70)
    print("Test 1: Validate Credentials")
    print("="*70)
    result1 = lambda_handler({'operation': 'ValidateCredentials'}, None)
    print(json.dumps(result1, indent=2))
    
    print("\n" + "="*70)
    print("Test 2: Describe Connector Configuration")
    print("="*70)
    result2 = lambda_handler({'operation': 'DescribeConnectorConfiguration'}, None)
    print(json.dumps(result2, indent=2))
    
    print("\n" + "="*70)
    print("Test 3: List Connector Entities")
    print("="*70)
    result3 = lambda_handler({'operation': 'ListConnectorEntities'}, None)
    print(json.dumps(result3, indent=2)[:500] + "...")
    
    print("\n" + "="*70)
    print("Test 4: Describe Connector Entity (User)")
    print("="*70)
    result4 = lambda_handler({
        'operation': 'DescribeConnectorEntity',
        'entityIdentifier': 'User'
    }, None)
    print(json.dumps(result4, indent=2)[:1000] + "...")
    
    print("\n" + "="*70)
    print("Test 5: Query Connector Data (User)")
    print("="*70)
    result5 = lambda_handler({
        'operation': 'QueryConnectorData',
        'entityIdentifier': 'User',
        'selectedFieldNames': ['Id', 'Username', 'Email'],
        'maxResults': 5
    }, None)
    print(json.dumps(result5, indent=2))
