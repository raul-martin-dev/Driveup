from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    README_DESCRIPTION = fh.read()

setup(
    name='driveup',
    version='0.9.12',
    author='Raúl M.R.',
    author_email="raul.martin4bc@gmail.com",
    url="https://github.com/raul-martin-dev/Driveup",
    license="MIT",
    description='Python package for uploading files and folders to Google Drive.',
    long_description=README_DESCRIPTION,
    long_description_content_type="text/markdown",
    
    packages=find_packages(include=["driveup", "driveup.*"]),

    include_package_data=True,
    package_data={
        "driveup": ["utilities/*.json"],
    },
    
    install_requires=[
        'google-api-python-client>=2.0.0',
        'pandas>=1.0.0',
        # 'google-auth-httplib2>=0.1.0',
        'google-auth-oauthlib>=0.8.0',
    ],

    python_requires='>3.7',
)