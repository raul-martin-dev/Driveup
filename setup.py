from setuptools import setup, find_packages

setup(
    name='driveup',
    version='0.2.0',
    author='Raúl M.R.',
    description='Python package for uploading files and folders to Google Drive',
    long_description='Python package for uploading files and folders to Google Drive',
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'pydrive',
    ],
)