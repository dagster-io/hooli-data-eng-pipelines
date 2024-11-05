from setuptools import find_packages, setup

setup(
    name="hooli_bi",
    packages=find_packages(exclude=["hooli_bi_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
