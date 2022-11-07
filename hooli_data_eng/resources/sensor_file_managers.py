
from dagster import build_resources, resource
import boto3
from dagster._utils import file_relative_path
import os
import boto3

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
        s3 = boto3.client('s3', region_name = self._region_name)
        objects = s3.list_objects(Bucket = self._s3_bucket)
        for o in objects["Contents"]:
            if o["Key"] == filename:
                mtime = o["LastModified"].timestamp() 
                print(mtime)
                return mtime
                
        
        

@resource(config_schema = {"region_name": str, "s3_bucket": str})
def s3_fs(context):
    region_name = context.resource_config["region_name"]
    s3_bucket = context.resource_config["s3_bucket"]
    return s3FileSystem(region_name, s3_bucket)