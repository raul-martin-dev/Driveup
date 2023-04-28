from google_auth_oauthlib.flow import InstalledAppFlow

def authorize(self,client_secrets_file):
    scopes = ['https://www.googleapis.com/auth/drive']
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes=scopes)
    creds = flow.run_local_server(port=0)

    return creds