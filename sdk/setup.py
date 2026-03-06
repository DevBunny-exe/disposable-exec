from setuptools import setup, find_packages

setup(
    name="disposable-exec",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "disposable=disposable.cli:main"
        ]
    },
)
