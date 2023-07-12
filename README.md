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
DRIVE_FOLDER_ID = 'https://drive.google.com/drive/folders/1wXpG03SN0RXI7y1QAd03IDGH2eXFD_VS'

creds = authorize(SECRET_PATH)
drive_obj = Drive(creds)
drive_obj.upload(EXCEL_PATH,DRIVE_FOLDER_ID)

```
## 🔑​ Getting credentials file

In order to get access to **Google Drive's API** (required to use this package), you will need either a "service" or a "client" **secret .json file** (SECRET_PATH variable mentioned in the example of use).

You can follow the next steps to download this file:

### 1. Create a new proyect

Go to [Google Cloud's console](https://console.cloud.google.com/apis/dashboard)) and create a new proyect:

# 💳​ License
Driveup is licensed under [MIT License](LICENSE).

# 🗃️ Shields
<p align="center">
  <a href="https://pypi.org/project/driveup/">
    <img src="https://img.shields.io/pypi/v/driveup" alt="PyPI" />
  </a>
  <a href="https://pepy.tech/project/driveup">
    <img src="https://pepy.tech/badge/driveup/month" alt="downloads" />
  </a>
</p>
