import dlt

from github_from_openapi import github_from_openapi_source


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="github_from_openapi_pipeline",
        destination='duckdb',
        dataset_name="github_from_openapi_data",
        progress="log",
        export_schema_path="schemas/export"
    )
    source = github_from_openapi_source()
    info = pipeline.run(source)
    print(info)
