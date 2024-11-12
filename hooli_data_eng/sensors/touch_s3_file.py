import boto3

# ---------------------------------------------------
# Internal Only
# Run this to update the file in s3 to force a sensor
# eval
# 
# To update the local version of the file just run 
# touch customers.txt

BUCKET = 'hooli-demo-branch'
BUCKET = 'hooli-demo'

dev = boto3.session.Session(profile_name='user-cloud-admin')
s3 = dev.client('s3', region_name = 'us-west-2')

with open('customers.txt', "rb") as f:
    s3.upload_fileobj(f, BUCKET, 'customers.txt')