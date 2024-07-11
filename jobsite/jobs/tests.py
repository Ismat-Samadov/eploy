from google.cloud import storage
from google.oauth2 import service_account
from decouple import config
import json

def test_gcs_connection():
    credentials_info = {
        "type": config('GCS_TYPE'),
        "project_id": config('GCS_PROJECT_ID'),
        "private_key_id": config('GCS_PRIVATE_KEY_ID'),
        "private_key": config('GCS_PRIVATE_KEY').replace('\\n', '\n'),
        "client_email": config('GCS_CLIENT_EMAIL'),
        "client_id": config('GCS_CLIENT_ID'),
        "auth_uri": config('GCS_AUTH_URI'),
        "token_uri": config('GCS_TOKEN_URI'),
        "auth_provider_x509_cert_url": config('GCS_AUTH_PROVIDER_CERT_URL'),
        "client_x509_cert_url": config('GCS_CLIENT_CERT_URL')
    }
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    client = storage.Client(credentials=credentials, project=config('GCS_PROJECT_ID'))

    try:
        bucket = client.get_bucket(config('GS_BUCKET_NAME'))
        print(f"Successfully connected to bucket: {bucket.name}")
    except Exception as e:
        print(f"Error connecting to bucket: {e}")

if __name__ == "__main__":
    test_gcs_connection()
