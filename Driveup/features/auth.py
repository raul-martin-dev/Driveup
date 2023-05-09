from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.service_account import Credentials
import json

def authorize(secrets_file):
    scopes = ['https://www.googleapis.com/auth/drive']
    creds_type = get_secret_type(secrets_file)
    if creds_type == 'client':
        flow = InstalledAppFlow.from_client_secrets_file(secrets_file, scopes=scopes)
        secret = flow.run_local_server(port=0)
    elif creds_type == 'service':
        secret = Credentials.from_service_account_file(secrets_file,scopes=scopes)
    else:
        # ERROR: invalid JSON file (needs control)
        pass
    
    creds_body = {
        'creds': secret,
        'type': creds_type
    }

    return creds_body

def get_secret_type(path):
    with open(path,'r') as f:
        secret_dict = json.load(f)

    if 'type' in secret_dict and secret_dict['type'] == 'service_account':
        secret_type = 'service'
    else:
        secret_type = 'client'
    
    return secret_type