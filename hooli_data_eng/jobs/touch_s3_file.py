import boto3

dev = boto3.session.Session(profile_name='user-cloud-admin')
s3 = dev.client('s3', region_name = 'us-west-2')

with open('customers.txt', "rb") as f:
    s3.upload_fileobj(f, 'hooli-demo-branch', 'customers.txt')