from google_auth_oauthlib.flow import InstalledAppFlow
import json

def authorize(client_secrets_file):
    scopes = ['https://www.googleapis.com/auth/drive']
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes=scopes)
    creds = flow.run_local_server(port=0)

    return creds

def get_secret_type(path):

    with open(path,'r') as f:
        secret_dict = json.load(f)

    if 'type' in secret_dict and secret_dict['type'] == 'service_account':
        secret_type = 'service'
    else:
        secret_type = 'client'
    
    return secret_type