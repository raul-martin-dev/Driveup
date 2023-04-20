from pydrive.auth import GoogleAuth
import os

class Auth:
    def authorize(self,secret,credentials_path,save_credentials=False):
        if credentials_path == None:
            secret_path = 'credentials.json'
            if secret != None:
                GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = secret
                secret_path = os.path.dirname(secret) + '\\' + secret_path
            gauth = GoogleAuth()
            gauth.LocalWebserverAuth()
            if save_credentials == True:
                gauth.SaveCredentialsFile(secret_path)
                credentials_path = secret_path
        else:
            gauth = GoogleAuth()
            gauth.LoadCredentialsFile(credentials_path)

        return gauth,credentials_path