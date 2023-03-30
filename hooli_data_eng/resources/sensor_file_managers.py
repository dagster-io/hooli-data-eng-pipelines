# ---------------------------------------------------
# This file contains a set of resources used
# by the jobs/watch_s3.py sensor
# Creating a new resource is as easy
# as implementing a class and then a function
# that invokes the class
# These resources accept configuration, passed
# in the sensor definition


from dagster import ConfigurableResource
import boto3
import os


class FileSystem(ConfigurableResource):
    def get_mtime(self, filename):
        raise NotImplementedError()


# The LocalFileSystem class allows for local
# testing with the same sensor code


class LocalFileSystem(FileSystem):
    base_dir: str

    def get_mtime(self, filename):
        path = self.base_dir + "/" + filename
        return os.path.getmtime(path)


# The s3FileSystem class is used on branch and
# production deployments
# TODO: Implement AWS profiles as config


class s3FileSystem(FileSystem):
    region_name: str
    s3_bucket: str

    def get_mtime(self, filename):
        s3 = boto3.client("s3", region_name=self.region_name)
        objects = s3.list_objects(Bucket=self.s3_bucket)
        for o in objects["Contents"]:
            if o["Key"] == filename:
                mtime = o["LastModified"].timestamp()
                print(mtime)
                return mtime
