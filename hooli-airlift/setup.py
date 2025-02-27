from setuptools import find_packages, setup

setup(
    name="hooli_airlift",
    packages=find_packages(exclude=["hooli_airlift_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "dagster-airlift",
        "boto3",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
