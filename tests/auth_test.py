import unittest
import os

from Driveup.features import auth

tests_dir = os.path.dirname(os.path.abspath(__file__)) # Driveup/tests/

CLIENT_SECRET_PATH = os.path.join(tests_dir,"__testsDataFiles","auth_testFiles","client_secrets.json")
SERVICE_SECRET_PATH = os.path.join(tests_dir,"__testsDataFiles","auth_testFiles","service_account_key.json")

class TestAuth(unittest.TestCase):
    def test_authorize_secret_service(self):
        credentials = auth.authorize(SERVICE_SECRET_PATH)
        # credentials = get_secret_type(CLIENT_SECRET_PATH)
        
        self.assertEqual(credentials["type"], 'service')

    def test_authorize_secret_client(self):
        credentials = auth.authorize(CLIENT_SECRET_PATH)
        # credentials = get_secret_type(CLIENT_SECRET_PATH)
        
        self.assertEqual(credentials["type"], 'client')


if __name__ == "__main__":
    unittest.main()
    # Auth tests can't be tested simultaneously (API conflict)



