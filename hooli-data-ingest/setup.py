from setuptools import find_packages, setup

setup(
    name="hooli_data_ingest",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-cloud[insights]",
        "dagster-embedded-elt",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)