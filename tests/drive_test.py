import unittest
import os
import pandas as pd

from Driveup.drive import Drive
from Driveup.features.auth import authorize


tests_dir = os.path.dirname(os.path.abspath(__file__)) # Driveup/tests/

CREDENTIALS_PATH = os.path.join(tests_dir,"__testsDataFiles","auth_testFiles","credentials.json")
CLIENT_SECRET_PATH = os.path.join(tests_dir,"__testsDataFiles","auth_testFiles","client_secrets.json")
SERVICE_SECRET_PATH = os.path.join(tests_dir,"__testsDataFiles","auth_testFiles","service_account_key.json")
UPLOAD_FILE_PATH_1 = os.path.join(tests_dir,"__testsDataFiles","drive_testFiles","test_file.csv")
UPLOAD_FILE_PATH_2 = os.path.join(tests_dir,"__testsDataFiles","drive_testFiles","test_file_test.csv")
UPLOAD_FOLDER_PATH = os.path.join(tests_dir,"__testsDataFiles","drive_testFiles","test_folder")
DRIVE_FOLDER_ID = 'https://drive.google.com/drive/folders/1wXpG03SN0RXI7y1QAd03IDGH2eXFD_VS'

class TestDrive(unittest.TestCase):
    def test_upload(self):
        creds = authorize(SERVICE_SECRET_PATH)

        drive_obj = Drive(creds)

        drive_obj.upload(UPLOAD_FILE_PATH_2,DRIVE_FOLDER_ID)

    def test_upload_list(self):
        creds = authorize(SERVICE_SECRET_PATH)

        drive_obj = Drive(creds)

        files = [UPLOAD_FILE_PATH_1,UPLOAD_FILE_PATH_2]

        drive_obj.upload(files,DRIVE_FOLDER_ID)
    
    def test_upload_list_ids(self):
        creds = authorize(SERVICE_SECRET_PATH)

        drive_obj = Drive(creds)

        ids = ['1LKUzha5IqtfQi3t8fnqK09pWfonfLKc3','1BJs_eDUR0XDR82N3sxzRz4wqrueJFGQX']

        files = [UPLOAD_FILE_PATH_1,UPLOAD_FILE_PATH_2]
        # files = [UPLOAD_FILE_PATH_1]
        # files = UPLOAD_FILE_PATH_1

        drive_obj.upload(files,'1R8caV6WVxSqKDC41EhmZB5ARBcp1F-7d',file_id=ids)

    def test_upload_list_folders(self):
        creds = authorize(SERVICE_SECRET_PATH)

        drive_obj = Drive(creds)

        # ids = ['1LKUzha5IqtfQi3t8fnqK09pWfonfLKc3','1BJs_eDUR0XDR82N3sxzRz4wqrueJFGQX']
        files = [UPLOAD_FILE_PATH_1,UPLOAD_FILE_PATH_2]
        folders = [DRIVE_FOLDER_ID,'1R8caV6WVxSqKDC41EhmZB5ARBcp1F-7d']

        # drive_obj.upload(files,DRIVE_FOLDER_ID,file_id=ids)
        drive_obj.upload(files,folders)
        # drive_obj.upload(files,folders,file_id=ids)
        # drive_obj.upload(UPLOAD_FILE_PATH_1,folders)

    def test_upload_existing(self):
        drive_obj = Drive(client_secret_path=CLIENT_SECRET_PATH)
        drive_obj.upload(UPLOAD_FILE_PATH_1,DRIVE_FOLDER_ID)


    def test_upload_folder(self):

        creds = authorize(CLIENT_SECRET_PATH)

        drive_obj = Drive(creds)

        drive_obj.upload_folder(UPLOAD_FOLDER_PATH,DRIVE_FOLDER_ID)
    
    def test_upload_folder_no_convert(self):

        creds = authorize(CLIENT_SECRET_PATH)

        drive_obj = Drive(creds)

        drive_obj.upload_folder(UPLOAD_FOLDER_PATH,DRIVE_FOLDER_ID)

    def test_upload_service(self):
        creds = authorize(SERVICE_SECRET_PATH)

        drive_obj = Drive(creds)

        drive_obj.upload(UPLOAD_FILE_PATH_1,DRIVE_FOLDER_ID,convert=True)

    def test_upload_folder_service(self):

        creds = authorize(SERVICE_SECRET_PATH)

        drive_obj = Drive(creds)

        drive_obj.upload_folder(UPLOAD_FOLDER_PATH,DRIVE_FOLDER_ID,convert=True)

    def test_update(self):

        creds = authorize(SERVICE_SECRET_PATH)

        drive_obj = Drive(creds)

        drive_obj.update(UPLOAD_FILE_PATH_1,'19EImCTn8Ou2zEZ8zWrDUKzyqnqKztJLf')

    def test_df_update(self):

        creds = authorize(SERVICE_SECRET_PATH)

        drive_obj = Drive(creds)

        df = pd.DataFrame({
                'test column key': ['test1', 'test2', 'test3', 'test4', 'test5'],
                'test column value': [1,2,3,4,5]
            })

        drive_obj.df_update(df,'171WCxM-NCcRvComPLXzAITkERhHi0t7XzdLtDM7twoA','hoja')

        
        
if __name__ == "__main__":
    unittest.main()
    # Auth tests can't be tested simultaneously (API conflict)