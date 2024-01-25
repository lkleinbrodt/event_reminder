import boto3
from config import Config

import json

def create_s3_client() -> boto3.client:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    )
    return s3

class S3:
    
    def __init__(self):
        self.s3 = create_s3_client()
        self.bucket = Config.S3_BUCKET
        
    def load_csv(self, path):
        s3_object = self.s3.get_object(Bucket=self.bucket, Key=path)
        contents = s3_object["Body"].read()
        df = pd.read_csv(BytesIO(contents))
        return df
    
    def download_file(self, s3_path, local_path):
        self.s3.download_file(Bucket = self.bucket, Key = s3_path, Filename=local_path)
        return True

    def upload_file(self, local_path, s3_path):
        self.s3.upload_file(Filename=local_path, Bucket=self.bucket, Key=s3_path)
        return True
    
    def get_all_objects(self, prefix='', **base_kwargs):
        continuation_token = None
        while True:
            list_kwargs = dict(MaxKeys=1000, **base_kwargs)
            list_kwargs['Bucket'] = self.bucket
            list_kwargs['Prefix'] = prefix
            if continuation_token:
                list_kwargs["ContinuationToken"] = continuation_token
            response = self.s3.list_objects_v2(**list_kwargs)
            yield from response.get("Contents", [])
            if not response.get("IsTruncated"):  # At the end of the list?
                break
            continuation_token = response.get("NextContinuationToken")
            
    def load_json(self, path):
        obj = self.s3.get_object(Bucket = self.bucket, Key = path)
        return json.loads(obj["Body"].read())

    def save_json(self, obj, path):
        self.s3.put_object(
            Body=json.dumps(obj),
            Bucket=self.bucket,
            Key=path
        )
        return True
        