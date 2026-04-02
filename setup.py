from pathlib import Path

from setuptools import find_packages, setup

README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")

setup(
    name="disposable-exec",
    version="0.1.3",
    description="Python SDK and hosted execution client for short-lived remote Python sandbox runs",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
    ],
    python_requires=">=3.10",
)
