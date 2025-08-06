import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def upload_to_s3(file_path, s3_key):
    bucket = os.getenv("S3_BUCKET_NAME")
    try:
        s3.upload_file(file_path, bucket, s3_key)
        url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"
        return url
    except Exception as e:
        print("S3 Upload Error:", e)
        return None

def delete_from_s3(s3_url):
    bucket = os.getenv("S3_BUCKET_NAME")
    try:
        # Correct base URL
        url = f"https://{bucket}.s3.amazonaws.com/"
        
        if not s3_url.startswith(url):
            raise ValueError("Invalid S3 URL format")
        
        # Extract the object key from the URL
        s3_key = s3_url.replace(url, "")
        
        # Delete the object
        s3.delete_object(Bucket=bucket, Key=s3_key)
        return True
    except Exception as e:
        print("S3 Delete Error:", e)
        return False
