from setuptools import setup, find_packages

setup(
    name='driveup',
    version='0.1.0',
    author='Raúl M.R.',
    description='Python package for uploading files and folders to Google Drive',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'pydrive',
    ],
)