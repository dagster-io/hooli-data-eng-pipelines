from setuptools import find_packages, setup

setup(
    name="dagster_batch_enrichment",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-duckdb",
        "pandas",
        "responses"
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
