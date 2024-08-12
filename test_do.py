import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DigitalOcean Spaces credentials from .env
DO_ACCESS_KEY_ID = os.getenv('DO_ACCESS_KEY_ID')
DO_SECRET_ACCESS_KEY = os.getenv('DO_SECRET_ACCESS_KEY')
DO_SPACES_NAME = os.getenv('DO_SPACES_NAME')
DO_REGION = 'fra1'  # Change this if your region is different
DO_ENDPOINT_URL = f'https://{DO_REGION}.digitaloceanspaces.com'

# Initialize Boto3 session
session = boto3.session.Session()
s3_client = session.client('s3',
                           region_name=DO_REGION,
                           endpoint_url=DO_ENDPOINT_URL,
                           aws_access_key_id=DO_ACCESS_KEY_ID,
                           aws_secret_access_key=DO_SECRET_ACCESS_KEY)

# Test file path and name
file_name = "test_file.txt"
file_content = b"This is a test file for DigitalOcean Spaces."

# Create a test file
with open(file_name, 'wb') as f:
    f.write(file_content)

def upload_file_to_do_spaces(file_name, bucket_name):
    try:
        # Check if the bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' exists. Uploading file...")

        # Upload the file
        s3_client.upload_file(file_name, bucket_name, file_name)
        print(f"File '{file_name}' uploaded successfully.")
        # Generate the file URL
        file_url = f"https://{bucket_name}.{DO_REGION}.digitaloceanspaces.com/{file_name}"
        print(f"File URL: {file_url}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Bucket '{bucket_name}' does not exist.")
        else:
            print(f"Failed to upload file: {e}")
        return False
    except FileNotFoundError:
        print("The file was not found.")
        return False
    except NoCredentialsError:
        print("Credentials not available.")
        return False

# Run the upload function
upload_success = upload_file_to_do_spaces(file_name, DO_SPACES_NAME)

# Clean up by deleting the local test file
if upload_success:
    os.remove(file_name)
