from google.cloud import storage
from google.oauth2 import service_account
import os

# Load credentials from the environment variable or directly from file
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "jobs-428816-193e530395ee.json")
credentials = service_account.Credentials.from_service_account_file(credentials_path)

# Initialize the client
client = storage.Client(credentials=credentials, project='jobs-428816')

# Test accessing the bucket
bucket_name = 'jobs_aze'
try:
    bucket = client.get_bucket(bucket_name)
    print(f"Successfully accessed the bucket: {bucket.name}")
except Exception as e:
    print(f"Error accessing the bucket: {e}")
