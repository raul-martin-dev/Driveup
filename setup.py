from setuptools import setup, find_packages

# ...

with open("README.md", "r") as fh:
    README_DESCRIPTION = fh.read()

# ...

setup(
    long_description=README_DESCRIPTION,
    long_description_content_type="text/markdown",
    name='driveup',
    version='0.8.0',
    author='Raúl M.R.',
    author_email="raul.martin4bc@gmail.com",
    url="https://github.com/raul-martin-dev/Driveup",
    license="MIT",
    description='Python package for uploading files and folders to Google Drive.',
    packages=find_packages(include=["Driveup","Driveup.features"]),
    install_requires=[
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
    ],
)