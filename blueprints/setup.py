from setuptools import find_packages, setup

setup(
    name="custom-blueprints",
    packages=find_packages(exclude=["custom-blueprints"]),
    install_requires=[
        "dagster",
        "dagster-blueprints",
        "dagster-webserver",
        "dagster-dbt",
    ],
    extras_require={"dev": ["pytest"]},
)