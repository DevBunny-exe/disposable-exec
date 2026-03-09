from setuptools import find_packages, setup

setup(
    name="disposable-exec",
    version="0.1.2",
    description="Hosted sandbox execution API and client for short-lived AI-generated Python code",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn>=0.29.0",
        "requests>=2.31.0",
        "redis>=5.0.1",
    ],
    entry_points={
        "console_scripts": [
            "disposable=disposable_exec.cli:main",
        ],
    },
)