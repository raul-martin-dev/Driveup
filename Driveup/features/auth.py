from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.service_account import Credentials
import json

def authorize(secrets_file):
    """
    Authorize the user to access the Google Drive API.

    Args:
        secrets_file (str): The path to the JSON file containing the user's OAuth credentials.

    Returns:
        dict: A dictionary containing the credentials and the type of the secret file.

    This function first identifies the type of the secret file, which can be either 'client' or 'service'.
    If the file is a 'client' secret file, it uses the InstalledAppFlow class to create a flow that
    runs a local server for user authorization. If the file is a 'service' account file, it creates
    a credentials object using the Credentials class. If the secret file type is neither 'client' nor
    'service', an error message is returned.

    More Details:
    - The 'scopes' variable is a list of required authorization scopes, e.g., ['https://www.googleapis.com/auth/drive'].
    - The 'creds_type' variable determines the type of the secret file ('client' or 'service').
    - If 'creds_type' is 'client', the function initiates user authorization using InstalledAppFlow.
    - If 'creds_type' is 'service', it creates a credentials object.
    - If 'creds_type' is neither 'client' nor 'service', the function returns an error message.

    Example Usage:
    ```
    credentials_info = authorize("path/to/secrets.json")
    ```
    """

    scopes = ['https://www.googleapis.com/auth/drive']
    creds_type = get_secret_type(secrets_file)
    if creds_type == 'client':
        flow = InstalledAppFlow.from_client_secrets_file(secrets_file, scopes=scopes)
        secret = flow.run_local_server(port=0)
    elif creds_type == 'service':
        secret = Credentials.from_service_account_file(secrets_file,scopes=scopes)
    else:
        print('\033[0;31mERROR: Invalid secret JSON file. Please check the file and try again.\033[0m')
        raise Exception('Invalid secret JSON file.')
    
    creds_body = {
        'creds': secret,
        'type': creds_type
    }

    return creds_body

def get_secret_type(path):
    """Get file type from secret path
    
    Retrieves information from the secret path to determine whether is a service or
    a client file.

    Args:
        path: Secret local file path.
    
    Returns:
        secret_type: Secret local file type (service / client)
    """
    with open(path,'r') as f:
        secret_dict = json.load(f)

    if 'type' in secret_dict and secret_dict['type'] == 'service_account':
        secret_type = 'service'
    else:
        secret_type = 'client'
    
    return secret_type