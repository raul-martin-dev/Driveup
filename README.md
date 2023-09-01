<p align="center"><img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/Driveup.png" alt="logo" width="80%" /></p>

<p align="center">
 <i>Driveup logo</i>
</p>


----------------------

<p align="justify">
Driveup is a python package to upload files and folders to Google Drive.
</p>

# 💬​ Contribution & Questions
| Contribution & Questions Type     | Platforms                               |
| ------------------------------- | --------------------------------------- |
| 🐞​​ **Bug Reports**              | [GitHub Issue Tracker]                  |
| 📦​ **Feature Requests & Ideas** | [GitHub Discussions]                    |
| 🛠️​ **Usage Questions & Discusions**          | [GitHub Discussions] |

# 💼​ Features
- Simplify google drive api usage
- Simplify google authorization flow (working both on service and client account in the same way)
- Upload files and folders to google drive via python
- Update google sheets content with pandas dataframes
- Update drive files content in flexible ways
- Download drive files

# ​💾​ Install DriveUp

To start using DriveUp use the next command:

```markdown
pip install driveup
```

Note: you might have to add this command as a “code” line in order to use Driveup on a Python notebook.

## 🔧​ Example of use

In this basic example, you can check how to use the package in order to upload an excel file to an specific folder in google drive.

```python
from Driveup.drive import Drive
from Driveup.features.auth import authorize

EXCEL_PATH = 'C:\\Data\\Path\\sample_excel_file.xlsx'
SECRET_PATH = 'C:\\Data\\Path\\Secret\\service_account_key.json'
DRIVE_FOLDER_ID = '1wXpG03SN0RXI7y1QAd03IDGH2eXFD_VS'

creds = authorize(SECRET_PATH)
drive_obj = Drive(creds)
drive_obj.upload(EXCEL_PATH,DRIVE_FOLDER_ID)

```
## 🔑​ Getting credentials file

In order to get access to **Google Drive's API** (required to use this package), you will need either a "service" or a "client" **secret .json file** (SECRET_PATH variable mentioned in the example of use).

You can follow the next steps to download this file:

### 1. Create a new proyect

Go to [Google Cloud's console](https://console.cloud.google.com/apis/dashboard) and create a new proyect:

<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/1.png" width="40%" />
</p>

<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/2.png" width="40%" />
</p>
<br>
<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/3.png" width="40%" />
</p>

### 2. Enable APIs

Add Drive's and Sheet's API for the new created project:

<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/4.png" width="60%" />
</p>
<br>
<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/5.png" width="60%" />
</p>

<br>

Search for both Drive and Sheets and click 'enable' button on both.

<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/6.png" width="40%" />
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/7.png" width="40%" />
</p>

### 3. Create credentials

Create a service/client account with access to this new created app and all its permissions:

<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/8.png" width="70%" />
</p>
<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/9.png" width="40%" />
</p>

Set default settings and choose a name for the account:

<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/10.png" width="60%" />
</p>

### 4. Download secret

Edit the new created account, go to 'KEYS' tab and create one. Download the secret key .json file.

<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/11.png" width="40%" />
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/12.png" width="40%" />
</p>

#### * Special consideration

Note that if you are using a service account, you must share the drive folder in wich you will be uploading files with the service account mail direction for it to be able to find that folder. You can copy this direction from the 'service accounts' tab at the console dashboard:

<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/13.png" width="90%" />
</p>
<p align="center">
 <img src="https://github.com/raul-martin-dev/Driveup/blob/master/static/img/secret_tutorial/14.png" width="80%" />
</p>
 
# 💳​ License
Driveup is licensed under [MIT License](LICENSE).

# 🗃️ Shields

<p align="center">
  <a href="https://pypi.org/project/driveup/">
    <img src="https://img.shields.io/pypi/v/driveup" alt="PyPI" />
  </a>
  <a href="https://pepy.tech/project/driveup">
    <img src="https://static.pepy.tech/badge/driveup" alt="downloads" />
  </a>
</p>
