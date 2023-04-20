import unittest
import os

from Driveup.features.auth import Auth

credentials_dir = os.path.dirname(os.path.abspath(__file__)) # Driveup/tests/

CREDENTIALS_PATH = os.path.join(credentials_dir,"__testsDataFiles","auth_testFiles","credentials.json")
CLIENT_SECRET_PATH = os.path.join(credentials_dir,"__testsDataFiles","auth_testFiles","client_secrets.json")

class TestAuth(unittest.TestCase):
    def test_authorize_secret(self):
        auth_obj = Auth()
        gauth,credentials_path = auth_obj.authorize(CLIENT_SECRET_PATH,None)

        self.assertEqual(credentials_path,None)

    def test_authorize_credentials_save(self):
        auth_obj = Auth()
        gauth,credentials_path = auth_obj.authorize(CLIENT_SECRET_PATH,None,save_credentials=True)

        self.assertEqual(credentials_path,CREDENTIALS_PATH)

    def test_authorize_credentials(self):
        auth_obj = Auth()
        gauth,credentials_path = auth_obj.authorize(None,CREDENTIALS_PATH)

        self.assertEqual(credentials_path,CREDENTIALS_PATH)

if __name__ == "__main__":
    unittest.main()
    # Auth tests can't be tested simultaneously (API conflict)


