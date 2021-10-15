from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="hooli_data_science",
        version="1.3.5",
        author="Hooli",
        author_email="hello@hooli.com",
        description="Hooli Data Science team Dagster pipelines.",
        url="https://github.com/dagster-io/hooli-data-science-pipelines",
        classifiers=[
            "Programming Language :: Python :: 3.10",
        ],
        packages=find_packages(exclude=["hooli_data_science_pipelines_tests"]),
        include_package_data=True,
        install_requires=[
            "dagit",
            "dagster",
            "dagster_aws",
            "dagster_cloud",
            "dagster_dbt",
            "dagster_pyspark",
            "dbt",
            "fsspec",
            "pandas",
            "pyarrow",
            "pyspark",
            "requests",
            "s3fs",
            "snowflake-sqlalchemy",
            "sqlalchemy",
        ],
        extras_require={
            "test": ["black", "mypy", "pylint", "pytest"],
        },
        package_data={"hooli_data_science": ["hooli_data_science_dbt/*"]},
    )
