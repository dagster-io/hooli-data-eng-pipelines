
from dagster import build_resources, resource
import boto3
from dagster._utils import file_relative_path
import os

class LocalFileSystem():
    def __init__(self, base_dir):
        self._base_dir = base_dir

    def get_mtime(self, filename):
        path = self._base_dir + "/" + filename
        return os.path.getmtime(path)
            

@resource(config_schema = {"base_dir": str})
def local_fs(context):
    base_dir = context.resource_config["base_dir"]
    return LocalFileSystem(base_dir)

class s3FileSystem():
    def __init__(self, region_name, s3_bucket):
        self._region_name = region_name 
        self._s3_bucket = s3_bucket

    def get_mtime(self, filename):
        dev = boto3.session.Session(profile_name='user-cloud-admin')
        s3 = dev.client('s3', region_name = self._region_name)
        objects = s3.list_objects(Bucket = self._s3_bucket)
        for o in objects["Contents"]:
            if o["Key"] == filename:
                return o["LastModified"]
        
        

@resource(config_schema = {"region_name": str, "s3_bucket": str})
def s3_fs(context):
    region_name = context.resource_config["region_name"]
    s3_bucket = context.resource_config["s3_bucket"]
    return s3FileSystem(region_name, s3_bucket)


def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    #return "LOCAL"
    return "BRANCH"

sensor_resources = {
    "LOCAL": {"fs": local_fs.configured({
        "base_dir": file_relative_path(__file__, ".")
    })},
    "PROD": {"fs": s3_fs.configured({
        "region_name": "us-west-2",
        "s3_bucket": "hooli-demo"
    })},
    "BRANCH": {"fs": s3_fs.configured({
        "region_name": "us-west-2",
        "s3_bucket": "hooli-demo-branch"
    })}
}



# test it out
with build_resources(
        sensor_resources[get_env()]
    ) as resources:
        mtime = resources.fs.get_mtime("customers.txt")

        
            
        
        