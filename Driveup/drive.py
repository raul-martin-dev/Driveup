from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pandas as pd
import io
from googleapiclient.http import MediaIoBaseDownload

from Driveup.features import utils,service

from typing import overload,Union,List

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
                folder_id = utils.url_to_id(folder_id)

            if file_title == None:
                file_title = utils.get_filename(file_path)

            drive_service = self.drive_service

            file_metadata = None

            media = MediaFileUpload(file_path, resumable=True)

            # possible refactor
            if update == True:
                file_metadata = service.get_update(file_title,file_id,folder_id,drive_service,self.mode)
                    
            if file_metadata == None: # Doesn't exist in the folder already or update=False (duplicating file)
                if self.mode == 'client':
                    file_metadata = {'name': file_title,'parents': [folder_id]}
                else:
                    file_metadata = {'name': file_title,'parents': folder_id}

                if convert == True:
                    file_metadata = utils.convert(file_metadata,utils.get_file_extension(file_path))

                gfile = drive_service.files().create(body=file_metadata, media_body=media, fields='id',supportsAllDrives=True).execute()

                if self.mode == 'service':
                    old_parents = gfile.get('parents')
                    file_id = gfile.get('id')

                    drive_service.files().update(fileId=file_id,removeParents=old_parents,addParents=folder_id,supportsAllDrives=True).execute()

            else: # File already exists: update
                file_id = file_metadata['id']
                gfile = self.update(file_path,file_id)
                
    def update(self,file_path: str,file_id: str):
        
        drive_service = self.drive_service
        media = MediaFileUpload(file_path, resumable=True)
        void_metadata = {}

        gfile = drive_service.files().update(fileId=file_id, body=void_metadata, media_body=media,supportsAllDrives=True).execute()

        return gfile
    
    def df_update(self,df:Union[pd.DataFrame, List[pd.DataFrame]],id:str,sheet_name:str = None,unformat:bool = False):


        sheets_service = self.sheets_service

        sheets = sheets_service.spreadsheets().get(spreadsheetId=id).execute().get('sheets', '')
        # sheet_id = sheets[0].get("properties", {}).get("sheetId", 0)

        if isinstance(df, list): 
            for single_df,sheet in zip(df,sheets):
                sheet_name = sheet.get("properties", {}).get("title", "Sheet1")
                self.df_update(single_df,id,sheet_name)       
        else:
            if unformat == True:
                df = df.fillna('NULL')
                df = df.astype(str)

            if sheet_name == None:
                sheet_name = sheets[0].get("properties", {}).get("title", "Sheet1")

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
            sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=id, body=requests).execute()

    def upload_folder(self,local_folder_path,folder_id,update=True,subfolder=True,subfolder_name=None,subfolder_id=None,recursive=True,convert=False,url=True):

        if url == True:
            folder_id = utils.url_to_id(folder_id)

        files_list = os.listdir(local_folder_path)

        if subfolder == True:

            if subfolder_name == None:
                subfolder_name = utils.get_filename(local_folder_path)

            folder_id = service.create_subfolder(subfolder_name,subfolder_id,folder_id,update,self.drive_service,self.mode)

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

    def download(self,id,path):

        # Download the file
        request = self.drive_service.files().get_media(fileId=id)
        fh = io.FileIO(path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f'Download progress: {status.progress() * 100:.2f}%')
        print(f'Download complete: {path}')
