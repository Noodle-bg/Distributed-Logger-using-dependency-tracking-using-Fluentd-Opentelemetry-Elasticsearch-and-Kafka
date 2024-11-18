from setuptools import setup, find_packages

setup(
    name="distributed_logger",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'flask',
        'requests',
        'fluent-logger',  # Add this new dependency
        'networkx'
    ]
)