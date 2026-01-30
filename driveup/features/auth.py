from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.service_account import Credentials
import json

def authorize(secrets):
    """
    Authorize the user to access the Google Drive API.

    Args:
        secrets (str or dict): The path to the JSON file containing the user's OAuth credentials or a dictionary with the credentials.

    Returns:
        dict: A dictionary containing the credentials and the type of the secret.

    This function first identifies the type of the secret, which can be either 'client' or 'service'.
    If the secret is a 'client' secret, it uses the InstalledAppFlow class to create a flow that
    runs a local server for user authorization. If the secret is a 'service' account, it creates
    a credentials object using the Credentials class. If the secret type is neither 'client' nor
    'service', an error message is returned.

    More Details:
    - The 'scopes' variable is a list of required authorization scopes, e.g., ['https://www.googleapis.com/auth/drive'].
    - The 'creds_type' variable determines the type of the secret ('client' or 'service').
    - If 'creds_type' is 'client', the function initiates user authorization using InstalledAppFlow.
    - If 'creds_type' is 'service', it creates a credentials object.
    - If 'creds_type' is neither 'client' nor 'service', the function returns an error message.

    Example Usage:
    ```
    credentials_info = authorize("path/to/secrets.json")
    or
    credentials_info = authorize({"type": "service_account", ...})
    ```
    """

    scopes = ['https://www.googleapis.com/auth/drive']

    secret_info, creds_type = get_secret(secrets)

    if creds_type == 'client':
        flow = InstalledAppFlow.from_client_config(secret_info, scopes=scopes)
        secret = flow.run_local_server(port=0)
    elif creds_type == 'service':
        secret = Credentials.from_service_account_info(secret_info, scopes=scopes)
    else:
        print('\033[0;31mERROR: Invalid secret dictionary. Please check the dictionary and try again.\033[0m')
        raise Exception('Invalid secret dictionary.')

    creds_body = {
        'creds': secret,
        'type': creds_type
    }

    return creds_body

def get_secret(secret):
    """
    Get secret dictionary and type from a file path or a dictionary.
    
    Retrieves information from the secret to determine whether it is a service or
    a client file, and returns the secret dictionary and its type.

    Args:
        secret (str or dict): Secret local file path or a dictionary containing the secret.
    
    Returns:
        tuple: A tuple containing the secret dictionary and the secret type ('service' or 'client').
    """
    if isinstance(secret, str):
        with open(secret, 'r') as f:
            secret_dict = json.load(f)
    elif isinstance(secret, dict):
        secret_dict = secret
    else:
        raise ValueError("\033[0;31mERROR: Secret must be a file path or a dictionary.\033[0m")

    if 'type' in secret_dict and secret_dict['type'] == 'service_account':
        secret_type = 'service'
    else:
        secret_type = 'client'
    
    return secret_dict, secret_type
