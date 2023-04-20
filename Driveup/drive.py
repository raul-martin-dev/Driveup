from pydrive.drive import GoogleDrive
from .features.auth import Auth
import os
import re

class Drive:
    def __init__(self,client_secret_path=None,credentials_path=None):
        self.client_secret_path = client_secret_path
        self.gauth,self.credentials_path = Auth().authorize(client_secret_path,credentials_path)
        self.drive = GoogleDrive(self.gauth)
    
    def upload(self,file_path,folder_id,file_title=None,file_id=None,update=True,convert=False,url=True):
        if url == True:
            folder_id = self.url_to_id(folder_id)

        if file_title == None:
            file_title = self.get_filename(file_path)

        gfile = None

        if update == True:
            gfile = self.update(file_title,file_id,folder_id)
                
        if gfile == None: # Doesn't exist in the folder already or update=False
            gfile = self.drive.CreateFile({'title': file_title,'parents': [{'id': folder_id}]})

        # Read file and set it as the content of this instance.
        gfile.SetContentFile(str(file_path))

        if convert == True:
            supported_types = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                'application/vnd.ms-excel',
                                'application/vnd.openxmlformats-officedocument.presentationml.presentation']
            if gfile['mimeType'] in supported_types:
                gfile.Upload(param={'convert':convert}) # Upload the file with conversion. 
            else:
                gfile.Upload()   
        else:
            gfile.Upload() # Upload the file without conversion.

    def update(self,name,file_id,folder_id):
        if file_id != None: # use specified id
                file = self.drive.CreateFile({'id':file_id,'title': name,'parents': [{'id': folder_id}]}) # Change name: doesn't work
        else: # obtain id for duplicated file (file with same name) and overwrite
            file_id = self.find_duplicate(self.list_files(folder_id),name)
            if file_id != None: # duplicate found
                file = self.drive.CreateFile({'id':file_id,'title': name,'parents': [{'id': folder_id}]})
            else: # duplicate not found
                file = None

        return file
            
    def get_filename(self,path):
        name = os.path.basename(path)
        name = os.path.splitext(name)[0]

        return name
    
    def list_files(self,folder_id):
        file_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        return file_list

    def find_duplicate(self,list,name):
        file_id = None
        for file in list:
            if file['title'] == name:
                file_id = file['id']
        
        return file_id
    
    def upload_folder(self,local_folder_path,folder_id,update=True,subfolder=True,subfolder_name=None,subfolder_id=None,recursive=True,convert=False,url=True):

        if url == True:
            folder_id = self.url_to_id(folder_id)

        files_list = os.listdir(local_folder_path)

        if subfolder_name == None:
            subfolder_name = self.get_filename(local_folder_path)

        if subfolder == True:
            folder_id = self.create_subfolder(subfolder_name,subfolder_id,folder_id,update)

        for file in files_list:
            file_path = str(local_folder_path)+ '/' + file
            if recursive == True:
                if os.path.isfile(file_path):
                    self.upload(file_path,folder_id,update=update,convert=convert,url=False) # url=False -> not checking everytime
                elif os.path.isdir(file_path):
                    self.upload_folder(file_path,folder_id,update=update,subfolder=subfolder,convert=convert)
                else:
                    # not file nor dir
                    print('\nError uploading file: ' + file_path + '\n(Not file or directory)')
                    pass
            else:
                self.upload(file_path,folder_id,update=update)
            

    def create_subfolder(self,subfolder_name,subfolder_id,parent_folder_id,update):
        subfolder = None

        if update == True:
            subfolder = self.update(subfolder_name,subfolder_id,parent_folder_id)
        
        subfolder_metadata = {'title': subfolder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [{'id': parent_folder_id}]}

        if subfolder == None:
            subfolder = self.drive.CreateFile(subfolder_metadata)
        else:
            subfolder['mimeType'] = subfolder_metadata['mimeType']
            
        subfolder.Upload()

        return subfolder['id']
    
    # Transforms drive folder's URL to id. Returns ID if entry is not URL
    def url_to_id(self,folder_id):
        regex = r"(https?://)?(www\.)?(drive.google\.com/)?drive/folders/(\w+)"
        match = re.search(regex, folder_id)
        if match:
            return match.group(4) # (\w+) -> Alphanumeric id
        else:
            return folder_id