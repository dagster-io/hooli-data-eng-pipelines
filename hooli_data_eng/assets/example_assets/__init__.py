import os


from dagster import asset, AssetSelection, define_asset_job, Definitions, graph_asset, In, Nothing, op, RetryPolicy
from dagster_aws.s3 import S3Resource




@asset(io_manager_key="model_io_manager")
def upstream_asset():
   """
   My Example Asset
   """
   return [1, 2, 3]



#@asset(io_manager_key="model_io_manager")
#def downstream_asset(upstream_asset):
#    return upstream_asset + [4]




# Define the S3 resource
#s3_resource = S3Resource(
#    region_name='us-west-1',  # Specify your region
#    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#    s3_bucket=os.getenv("AWS_S3_BUCKET_DEMO")
#)
#
#
## Simulate cleaning the 'working' folder
#@op
#def clean_working_folder(context):
#    context.log.info("Working directory cleaned.")
#
#
## Simulate cleaning the 'latest' folder
#@op(ins={"after_clean_working": In(Nothing)})
#def clean_latest_folder(context):
#    context.log.info("Latest directory cleaned.")
#
#
## Simulate creating a dated folder
#@op(ins={"after_clean_latest": In(Nothing)})
#def create_dated_folder(context):
#    folder_name = datetime.utcnow().strftime("%Y-%m-%d")
#    context.log.info(f"Dated folder created: {folder_name}")
#    return folder_name
#
#
## Simulate retrieving files from SFTP
#@op(ins={"after_create_dated": In(Nothing)})
#def retrieve_files_from_sftp(context):
#    mock_files = ['file_1.csv', 'file_2.csv', 'file_3.csv']
#    context.log.info(f"Files retrieved from SFTP: {', '.join(mock_files)}")
#    return mock_files
#
#
## Simulate copying files from SFTP to the working directory
#@op
#def copy_files_to_working(context, files):
#    for file in files:
#        context.log.info(f"Copied {file} to working directory.")
#    return files
#
## Simulate copying files from the working directory to the latest directory
#@op
#def copy_files_to_latest(context, files):
#    for file in files:
#        context.log.info(f"Copied {file} from working to latest directory.")
#
#
## Simulate copying files from the working directory to today's dated directory
#@op
#def copy_files_to_today(context, files, dated_folder):
#    for file in files:
#        context.log.info(f"Copied {file} from working to {dated_folder} directory.")
#    return len(files)  # Return the count as metadata
#
#
#@op
#def log_total_files_copied(context, total_files, dated_folder):
#    context.log.info(f"Total files copied to {dated_folder}: {total_files}")
#    return f"logged_{total_files}_files"
#
#
#@graph_asset
#def file_management_asset():
#    return create_dated_folder(after_clean_latest=clean_latest_folder(after_clean_working=clean_working_folder()))
#
#
#default_policy = RetryPolicy(max_retries=3)
#
#
##
#run_pipeline = define_asset_job(
#    name="run_pipeline",
#    selection=AssetSelection.assets(file_management_asset),
#    op_retry_policy=default_policy
#)
#
#defs = Definitions(
#    assets=[file_management_asset],
#    jobs=[run_pipeline],
#    resources={'s3': s3_resource}
#)
