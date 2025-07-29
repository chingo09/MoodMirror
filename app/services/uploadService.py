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
