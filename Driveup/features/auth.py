from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.service_account import Credentials

class Auth:
    def authorize(self,client_secrets_file,service=False):
        scopes = ['https://www.googleapis.com/auth/drive']
        if service == True:
            creds = Credentials.from_service_account_file(client_secrets_file, scopes=scopes)
            creds_type = 'service'
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes=scopes)
            creds = flow.run_local_server(port=0)
            creds_type = 'client'

        return creds,creds_type