import unittest
import os

from Driveup.features.auth import Auth

credentials_dir = os.path.dirname(os.path.abspath(__file__)) # Driveup/tests/

CLIENT_SECRET_PATH = os.path.join(credentials_dir,"__testsDataFiles","auth_testFiles","client_secrets.json")

class TestAuth(unittest.TestCase):
    def test_authorize_secret(self):
        auth_obj = Auth()
        credentials = auth_obj.authorize(CLIENT_SECRET_PATH)


if __name__ == "__main__":
    unittest.main()
    # Auth tests can't be tested simultaneously (API conflict)


