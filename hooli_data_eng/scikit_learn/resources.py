import dagster as dg
from dagster_aws.s3 import ConfigurablePickledObjectS3IOManager, S3Resource

resource_def = {
    "LOCAL": {
        "model_io_manager": dg.FilesystemIOManager(),
    },
    "BRANCH": {
        "model_io_manager": ConfigurablePickledObjectS3IOManager(
            s3_bucket="hooli-demo-branch",
            s3_resource=S3Resource(region_name="us-west-2"),
        ),
    },
    "PROD": {
        "model_io_manager": ConfigurablePickledObjectS3IOManager(
            s3_bucket="hooli-demo-branch",
            s3_resource=S3Resource(region_name="us-west-2"),
        ),
    },
}
