import unittest
import os

from Driveup.drive import Drive

tests_dir = os.path.dirname(os.path.abspath(__file__)) # Driveup/tests/

CREDENTIALS_PATH = os.path.join(tests_dir,"__testsDataFiles","auth_testFiles","credentials.json")
CLIENT_SECRET_PATH = os.path.join(tests_dir,"__testsDataFiles","auth_testFiles","client_secrets.json")
UPLOAD_FILE_PATH = os.path.join(tests_dir,"__testsDataFiles","drive_testFiles","test_file.csv")
UPLOAD_FOLDER_PATH = os.path.join(tests_dir,"__testsDataFiles","drive_testFiles","test_folder")
DRIVE_FOLDER_ID = 'https://drive.google.com/drive/folders/1wXpG03SN0RXI7y1QAd03IDGH2eXFD_VS'

class TestDrive(unittest.TestCase):
    def test_upload(self):
        drive_obj = Drive(client_secret_path=CLIENT_SECRET_PATH,credentials_path=CREDENTIALS_PATH)
        drive_obj.upload(UPLOAD_FILE_PATH,DRIVE_FOLDER_ID)

    def test_upload_folder(self):
        drive_obj = Drive(credentials_path=CREDENTIALS_PATH,client_secret_path=CLIENT_SECRET_PATH)
        drive_obj.upload_folder(UPLOAD_FOLDER_PATH,DRIVE_FOLDER_ID)

if __name__ == "__main__":
    unittest.main()
    # Auth tests can't be tested simultaneously (API conflict)