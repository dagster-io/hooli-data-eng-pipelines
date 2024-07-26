import os
import posixpath
from typing import Iterator, Sequence

import dlt
from dlt.sources import TDataItems, DltResource
import boto3
import duckdb
import pandas as pd
from io import StringIO


try:
    from .filesystem import FileItemDict, filesystem, readers, read_csv  # type: ignore
except ImportError:
    from filesystem import (
        FileItemDict,
        filesystem,
        readers,
        #read_csv,
    )
from pyarrow.csv import read_csv

TESTS_BUCKET_URL = posixpath.abspath("../tests/filesystem/samples/")


def stream_and_merge_csv(
    name: str,
    s3_bucket_name: str = "hooli-demo",
    s3_prefix: str = "embedded-elt/",
):
    s3 = boto3.client('s3')
    # List CSV files in the S3 bucket
    response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_prefix)
    csv_files = [item['Key'] for item in response.get('Contents', []) if item['Key'].endswith('.csv')]
    print(csv_files)
    # Read and load each CSV file into DuckDB
    for csv_file in csv_files:
        print(f"Processing {csv_file}")
        obj = s3.get_object(Bucket=s3_bucket_name, Key=csv_file)
        csv_content = obj['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_content))
    #pyarrow_content = read_csv(csv_content)
    #print(pyarrow_content)
    # print(csv_content)
    # Load CSV content into DuckDB
        conn = duckdb.connect(database=':memory:')
        conn.execute(f"CREATE TABLE IF NOT EXISTS met_data AS SELECT * FROM df")
        conn.execute(f"INSERT INTO met_data SELECT * FROM df")

@dlt.source
def s3_locations_data(s3_bucket_name: str, s3_prefix: str) -> dlt.sources.DltResource:
    """
    Reads CSV files from an S3 bucket and loads them into a Pandas DataFrame.

    Args:
        s3_bucket_name (str): The name of the S3 bucket.
        s3_prefix (str): The prefix (path) to the CSV files in the S3 bucket.

    Returns:
        pd.DataFrame: The loaded Pandas DataFrame.
    """
    @dlt.resource(primary_key="id", write_disposition="merge")
    def locations_data():
        s3 = boto3.client('s3')
        # List CSV files in the S3 bucket
        response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_prefix)
        csv_files = [item['Key'] for item in response.get('Contents', []) if item['Key'].endswith('.csv')]
        
        for csv_file in csv_files:
            obj = s3.get_object(Bucket=s3_bucket_name, Key=csv_file)
            csv_content = obj['Body'].read().decode('utf-8')
            df = pd.read_csv(StringIO(csv_content))
        yield df
    return locations_data

    # @dlt.resource(name="locations")
    # def resource():
    #     return combined_df
    # return resource

# @dlt.source
# def s3_locations_data(s3_bucket_name: str, s3_prefix: str
# ) -> Sequence[DltResource]:
#     """Demonstrates how to scan folder with csv files, load them in chunk and merge on date column with the previous load"""
#     # pipeline = dlt.pipeline(
#     #     pipeline_name="standard_filesystem_csv",
#     #     destination='duckdb',
#     #     dataset_name="locations",
#     # )
#     return(
#         dlt.resource(
#             "locations",
#             stream_and_merge_csv(
#                 "locations",
#                 s3_bucket_name="hooli-demo",
#                 s3_prefix="embedded-elt/",
#             ),        
#             write_disposition="replace",
#             ),
#         dlt.resource(
#             "name",
#             stream_and_merge_csv(
#                 "some_other_name",
#                 s3_bucket_name="hooli-demo",
#                 s3_prefix="embedded-elt/",
#             ),        
#             write_disposition="replace",
#             ),
#     )
  


if __name__ == "__main__":
    stream_and_merge_csv()