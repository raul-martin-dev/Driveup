from typing import overload,Union,List
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import re

class Drive:
    def __init__(self,creds):
        self.mode = creds['type']
        self.drive_service = build('drive', 'v3', credentials=creds['creds'])
        self.sheets_service = build('sheets', 'v4', credentials=creds['creds'])
    
    @overload
    def upload(self,file_path:list,folder_id:Union[str, List[str]],file_title:str=None,file_id:Union[str, List[str]]=None,update=True,convert=False,url=True):
        ...
    @overload
    def upload(self,file_path:str,folder_id:Union[str, List[str]],file_title:str=None,file_id:Union[str, List[str]]=None,update=True,convert=False,url=True):
        ...
    
    def upload(self,file_path: Union[str, List[str]],folder_id:Union[str, List[str]],file_title:str=None,file_id: Union[str, List[str]]=None,update=True,convert=False,url=True):

        if isinstance(file_path, list): # if multipath

            if isinstance(folder_id, list): # needs a warning saying that will ignore file ids 
                for file,folder in zip(file_path,folder_id): # needs a warning controlling if sizes of both lists are the same
                    self.upload(file,folder_id=folder,file_title=file_title,file_id=file_id,update=update,convert=convert,url=url)
            else:
                if file_id == None: 
                    for file in file_path:
                        self.upload(file,folder_id=folder_id,file_title=file_title,file_id=file_id,update=update,convert=convert,url=url)
                else: # needs a warning controlling if sizes of both lists are the same
                    for file,id in zip(file_path,file_id):
                        self.upload(file,folder_id=folder_id,file_title=file_title,file_id=id,update=update,convert=convert,url=url)

        else: # if single file path
            
            if isinstance(file_id, list): # needs a warning saying that file_id as 'list' is not intended for a single path
                # print ('warning')
                file_id = file_id[0]
            
            if isinstance(folder_id, list): # needs a warning saying that folder_id as 'list' is not intended for a single path
                # print ('warning')
                folder_id = folder_id[0]
                
            if url == True:
                folder_id = self.url_to_id(folder_id)

            if file_title == None:
                file_title = self.get_filename(file_path)

            drive_service = self.drive_service

            file_metadata = None

            media = MediaFileUpload(file_path, resumable=True)

            # possible refactor
            if update == True:
                file_metadata = self.get_update(file_title,file_id,folder_id,drive_service)
                    
            if file_metadata == None: # Doesn't exist in the folder already or update=False (duplicating file)
                if self.mode == 'client':
                    file_metadata = {'name': file_title,'parents': [folder_id]}
                else:
                    file_metadata = {'name': file_title,'parents': folder_id}

                if convert == True:
                    file_metadata = self.convert(file_metadata,self.get_file_extension(file_path))

                gfile = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

                if self.mode == 'service':
                    old_parents = gfile.get('parents')
                    file_id = gfile.get('id')

                    drive_service.files().update(fileId=file_id,removeParents=old_parents,addParents=folder_id).execute()

            else: # File already exists: update
                file_id = file_metadata['id']
                gfile = self.update(file_path,file_id)
                

    def update(self,file_path: str,file_id: str):
        
        drive_service = self.drive_service
        media = MediaFileUpload(file_path, resumable=True)
        void_metadata = {}

        gfile = drive_service.files().update(fileId=file_id, body=void_metadata, media_body=media).execute()

        return gfile
    
    def df_update(self,df,id,sheet_name = None):

        sheets_service = self.sheets_service

        if sheet_name == None:
            sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=id).execute()
            sheets = sheet_metadata.get('sheets', '')
            sheet_name = sheets[0].get("properties", {}).get("title", "Sheet1")
            # sheet_id = sheets[0].get("properties", {}).get("sheetId", 0)

        values = [df.columns.tolist()] + df.values.tolist()

        value_range = {
            'range': sheet_name,  # Specify the range where you want to update the values
            'values': values
        }
        
        # Build the request body   
        requests = {
            "valueInputOption": 'USER_ENTERED',
            "data": [value_range]
        }

        # clear mask
        sheets_service.spreadsheets().values().clear(spreadsheetId=id,range=sheet_name, body={}).execute()

        # Update the values in the spreadsheet
        # sheets_service.spreadsheets().values().update(spreadsheetId=id, range=sheet_name, valueInputOption='USER_ENTERED', body=request_body).execute()
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=id, body=requests).execute()

    
    # returns metadata for the file (whether it exists or not)
    def get_update(self,name,file_id,folder_id,service):
        if file_id != None: # use specified id
                if self.mode == 'client':
                    file_metadata = {'id':file_id,'name': name,'parents': [folder_id]} # Change name: doesn't work
                else:
                    file_metadata = {'id':file_id,'name': name,'parents': folder_id} # Change name: doesn't work

        else: # obtain id for duplicated file (file with same name) and overwrite
            file_id = self.find_duplicate(self.list_files(folder_id,service),name = name)
            if file_id != None: # duplicate found
                if self.mode == 'client':
                    file_metadata = {'id':file_id,'name': name,'parents': [folder_id]}
                else:
                    file_metadata = {'id':file_id,'name': name,'parents': folder_id}
            else: # duplicate not found
                file_metadata = None

        return file_metadata
            
    def get_filename(self,path):
        name = os.path.basename(path)
        name = os.path.splitext(name)[0]

        return name
    
    def get_file_extension(self,path):
        name = os.path.basename(path)
        extension = os.path.splitext(name)[1]
        extension = extension.lower()
        extension = extension.replace(".", "")

        return extension
    
    def list_files(self,folder_id,service):
        results = service.files().list(q=f"'{folder_id}' in parents and trashed = false", fields="nextPageToken, files(id, name)").execute()  
        files = results.get('files', [])
        
        return files

    def find_duplicate(self,list,name = None,file_id = None):
        if name == None and file_id == None:
            # needs to control error
            pass

        elif name != None: # name mode

            for file in list:
                if file['name'] == name:
                    file_id = file['id']
            
            return file_id
        
        elif file_id != None: # id mode

            condition = False
            for file in list:
                if file['id'] == file_id:
                    condition = True
            
            return condition
            
    def upload_folder(self,local_folder_path,folder_id,update=True,subfolder=True,subfolder_name=None,subfolder_id=None,recursive=True,convert=False,url=True):

        if url == True:
            folder_id = self.url_to_id(folder_id)

        files_list = os.listdir(local_folder_path)

        if subfolder == True:

            if subfolder_name == None:
                subfolder_name = self.get_filename(local_folder_path)

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
            else:
                self.upload(file_path,folder_id,update=update)
            

    def create_subfolder(self,subfolder_name,subfolder_id,parent_folder_id,update):

        drive_service = self.drive_service

        subfolder = None

        if update == True:
            subfolder = self.get_update(subfolder_name,subfolder_id,parent_folder_id,drive_service)
        
        subfolder_metadata = {'name': subfolder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_folder_id]}

        if subfolder == None:
            subfolder = drive_service.files().create(body=subfolder_metadata, fields='id').execute()
        else:
            subfolder['mimeType'] = subfolder_metadata['mimeType']

        return subfolder['id']
    
    # Transforms drive folder's URL to id. Returns ID if entry is not URL
    def url_to_id(self,folder_id):
        regex = r"(https?://)?(www\.)?(drive.google\.com/)?drive/folders/(\w+)"
        match = re.search(regex, folder_id)
        if match:
            return match.group(4) # (\w+) -> Alphanumeric id
        else:
            return folder_id
       
    def convert(self,file_metadata,extension=None):
        permited_general_extensions = ['txt',
                                       'doc',
                                       'odt',
                                       'docm',
                                       'csv',
                                       'xlsx',
                                       'xls',
                                       'xlsm',
                                       'fods',
                                       'pptx']
        
        if extension == 'docx':
            file_metadata['mimeType'] = 'application/vnd.google-apps.document'
        elif extension == 'rtf':
            file_metadata['mimeType'] = 'application/vnd.google-apps.document'
        elif extension == 'md':
            file_metadata['mimeType'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif extension == 'odf':
            file_metadata['mimeType'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif extension == 'slk':
            file_metadata['mimeType'] = 'application/vnd.google-apps.spreadsheet'
        elif extension == 'prn':
            file_metadata['mimeType'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif extension in permited_general_extensions :
            file_metadata['mimeType'] = 'application/vnd.google-apps.' + extension
        else:
            file_metadata = file_metadata

        
        return file_metadata
    
