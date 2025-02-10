from setuptools import find_packages, setup

setup(
    name="retail_pipeline",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagit",
        "minio",
        "pandas",
        "python-dotenv",
    ],
)
