from setuptools import setup, find_packages

# ...

with open("README.md", "r") as fh:
    README_DESCRIPTION = fh.read()

# ...

setup(
    long_description=README_DESCRIPTION,
    long_description_content_type="text/markdown",
    name='driveup',
    version='0.2.1',
    author='Raúl M.R.',
    author_email="raul.martin4bc@gmail.com",
    license="MIT",
    description='Python package for uploading files and folders to Google Drive',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'pydrive',
    ],
)