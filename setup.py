from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="hooli_data_eng",
        version="1.3.5",
        author="Hooli",
        author_email="hello@hooli.com",
        description="Hooli Data Science team Dagster pipelines.",
        url="https://github.com/dagster-io/hooli-data-eng-pipelines",
        classifiers=[
            "Programming Language :: Python :: 3.10",
        ],
        packages=find_packages(exclude=["hooli_data_eng_pipelines_tests"]),
        include_package_data=True,
        install_requires=[
            "dagit",
            "dagster",
            "dagster_aws",
            "dagster_cloud",
            "dagster_dbt",
            "dagster_pandas",
            "dagster_fivetran",
            "dbt",
            "fsspec",
            "pandas",
            "pyarrow",
            "requests",
            "s3fs",
            "snowflake-sqlalchemy",
            "sqlalchemy",
        ],
        extras_require={
            "test": ["black", "mypy", "pylint", "pytest"],
        },
        package_data={"hooli_data_eng": ["hooli_data_eng_dbt/*"]},
    )
