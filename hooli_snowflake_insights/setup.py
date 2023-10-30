from setuptools import find_packages, setup

setup(
    name="dagster_snowflake_insights",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "dagster-dbt",
        "dagster-snowflake",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)