from setuptools import setup, find_packages

# ...

with open("README.md", "r", encoding="utf-8") as fh:
    README_DESCRIPTION = fh.read()

# ...

setup(
    name='driveup',
    version='0.2.0',
    author='Raúl M.R.',
    description='Python package for uploading files and folders to Google Drive',
    long_description=README_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'pydrive',
    ],
)