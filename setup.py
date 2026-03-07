from setuptools import setup, find_packages

setup(
    name="disposable-exec",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "requests",
        "fastapi",
        "uvicorn"
    ],
    entry_points={
        "console_scripts": [
            "disposable=disposable_exec.cli:main",
        ],
    },
)