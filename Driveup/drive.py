from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pandas as pd
# import io
# from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm


from Driveup.features import utils,service

from typing import overload,Union,List

class Drive:
    """Contains DriveUp main methods and have full access to both drive and sheets API.
    """
    def __init__(self,creds):
        """Constructor for Drive.

        Use credentials from authorization flow to create the object and it's services based on them.

        Args:
          creds: Dictionary containing credentials generated with auth lib and it's corresponding type. 
          Value generated with the authorize method from the auth module in features
        """
        self.mode = creds['type']
        self.drive_service = build('drive', 'v3', credentials=creds['creds'])
        self.sheets_service = build('sheets', 'v4', credentials=creds['creds'])

    @overload
    def upload(self,file_path:list,folder_id:Union[str, List[str]],file_title:str=None,file_id:Union[str, List[str]]=None,update:bool=True,convert:bool=False,url:bool=True):
        ...
    @overload
    def upload(self,file_path:str,folder_id:Union[str, List[str]],file_title:str=None,file_id:Union[str, List[str]]=None,update:bool=True,convert:bool=False,url:bool=True):
        ...
    
    def upload(self,file_path: Union[str, List[str]],folder_id:Union[str, List[str]],file_title:str=None,file_id: Union[str, List[str]]=None,update:bool=True,convert:bool=False,url:bool=True):
        """Upload a file or a list of files to a specified drive folder(s) by ID.

        Iterates through the folder's files searching for one with the same name as the local 
        file (unless other name is specified as file_title). If the file doesn'exist in the folder, 
        it creates one with that name and local content; else, it updates the content with the 
        local information (unless update option is disabled).

        Args:
            file_path: Path or list of paths of the local file(s) wich content will be uploaded.
            folder_id: ID of the drive folder(s) in wich the file(s) will be uploaded.
            file_title: Name that will be shown in drive for the uploaded file. (If set to None, local file name will be used instead)
            file_id: Pointing ID to overwrite the content of an specified, previously created, drive file within the folder.
            update: If set to True, the method will be overwrite (update) the content of an existing file with the same name in drive. Otherwise, it will create another with the same name.
            convert: If set to True, the method will convert all files (if conversion is available) to it's corresponding google mimeType in Drive.
            url: If set to True, the method will accept URL type input as folder_id and automatically convert it to ID type.
            
        """

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

            pbar = tqdm(total=100, unit='B')

            pbar.update(10)

            drive_service = self.drive_service

            file_metadata = {}
            file_metadata['name'] = file_title
            file_metadata['parents'] = folder_id if self.mode == 'service' else [folder_id]
            if file_id != None:
                file_metadata['id'] = file_id

            file_extension = utils.get_file_extension(file_path)

            if convert == True:
                file_metadata = utils.convert(file_metadata,file_extension)
            else:
                file_metadata['name'] += f'.{file_extension}' if file_extension != "" else file_metadata['name']

            duplicate_check, file_metadata = service.find_duplicate(file_metadata,drive_service)

            pbar.update(40)

            if duplicate_check and update == True:
                file_id = file_metadata['id']
                gfile = self.update(file_path,file_id)
            else:
                if update == False:
                    del file_metadata['id'] 
                media = MediaFileUpload(file_path, resumable=True)
                gfile = drive_service.files().create(body=file_metadata, media_body=media, fields='id',supportsAllDrives=True).execute()

                if self.mode == 'service':
                    old_parents = gfile.get('parents')
                    file_id = gfile.get('id')

                    drive_service.files().update(fileId=file_id,removeParents=old_parents,addParents=folder_id,supportsAllDrives=True).execute()

            pbar.update(50)

                
    def update(self,file_path: str,file_id: str):
        """Update content of a drive file with a local file.

        Updates content of a drive file specified by its id with local information on the specified file path.

        Args:
            file_path: Path of the local file wich content will be overwriting (updating) the drive file content.
            file_id: ID of the drive file that will be updated.      
            
        """
        
        drive_service = self.drive_service
        media = MediaFileUpload(file_path, resumable=True)
        void_metadata = {}

        gfile = drive_service.files().update(fileId=file_id, body=void_metadata, media_body=media,supportsAllDrives=True).execute()

        return gfile
    
    def df_update(self,df:Union[pd.DataFrame, List[pd.DataFrame]],id:str,sheet_name:str = None,unformat:bool = False):
        """Update content of a drive sheet with a pandas dataframe.

        Updates content of a drive sheet specified by its id with local information of a specified dataframe or a list of them.

        Args:
            df: Dataframe, or list of them, wich information will be used to update drive sheets. If a list of dataframes are specified, by default, they will be updating each sheet of the file in the same order of the list.
            id: ID of the drive sheet that will be updated.  
            sheet_name: Name of the sheet that will be updated. If set to None, first sheet of the file will be updated (unless the method is updating in list mode).  
            unformat: If set to True, original df will be cleaned of format as string and filled NaN values with 'NULL'. Enabling this option could avoid 'Not JSON serializable' error when uploading certains dataframes.   
            
        """

        sheets_service = self.sheets_service

        sheets = sheets_service.spreadsheets().get(spreadsheetId=id).execute().get('sheets', '')
        # sheet_id = sheets[0].get("properties", {}).get("sheetId", 0)

        if isinstance(df, list): 
            for single_df,sheet in zip(df,sheets):
                sheet_name = sheet.get("properties", {}).get("title", "Sheet1")
                self.df_update(single_df,id,sheet_name,unformat=unformat)       
        else:
            if unformat == True:
                df = df.fillna('NULL')
                df = df.astype(str)
                df.columns = df.columns.astype(str)

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

    def upload_folder(self,local_folder_path :str,folder_id :str,update : bool =True,subfolder : bool=False,subfolder_name:str=None,recursive: bool=True,convert: bool=False,url: bool=True,total_files_to_upload_count=None,pbar=None):
        """Upload entire local folder to a specified drive folder by ID.

        Takes all the content of a local folder and uploads it with the same structure to 
        Drive. If files or folders exists already and are strucutured in the same way as 
        local and named the same, it's contents will be updated with the local information, 
        otherwise, they will be created in it's corresponding place of the structure.

        Args:
            local_folder_path: Path of the local folder wich contents will be uploaded.
            folder_id: ID of the drive folder in wich the local folder's content will be uploaded.
            update: If set to True, the method will be overwrite (update) the content of an existing files and folders with the same name in drive. Otherwise, it will create others with the same name.
            subfolder: If set to True, the method will respect the subfolder structure of the local subfolder and replicate it on drive creating the subfolders and uploading the files in it's places. Otherwise, it will upload all files on the local folder and it's subfolders to the same Drive folder not creating subfolders (this could cause conflict with files with the same name in different subfolders as it will overwrite them).
            subfolder_name: Name of all the subfolders created by the method. If set to None, names will be created normally following the names assigned locally.
            recursive: If set to True, it iterates through the local folder uploading subfolders content too. Otherwise, it only will upload content of the specified folder and ignore subfolders.
            convert: If set to True, the method will convert all files in the folder (if conversion is available) to it's corresponding google mimeType in Drive.
            url: If set to True, the method will accept URL type input as folder_id and automatically convert it to ID type.
            
        """

        if  total_files_to_upload_count == None and pbar == None:
            print('\n> Calculating estimated files number...')
            total_files_to_upload_count = sum(len(filenames) for _, _, filenames in os.walk(local_folder_path))
            print(f'Started uploading folder with {total_files_to_upload_count} files\n')
            pbar = tqdm(total = total_files_to_upload_count,desc='Total upload progress: ')

        if url == True:
            folder_id = utils.url_to_id(folder_id)

        files_list = os.listdir(local_folder_path)

        if subfolder == True:

            if subfolder_name == None:
                subfolder_name = utils.get_filename(local_folder_path)

            folder_id = service.create_subfolder(subfolder_name,None,folder_id,update,self.drive_service,self.mode)

        for file in files_list:
            file_path = str(local_folder_path)+ '/' + file
            if recursive == True:
                if os.path.isfile(file_path):
                    # uploaded_files_counter += 1
                    # print(f"\n\nUploading folder's files : {uploaded_files_counter}/{total_files_to_upload_count}")
                    try:
                        self.upload(file_path,folder_id,convert=convert,url=False) # url=False -> not checking everytime
                    except Exception as e:
                        print(f"Error uploading file: {file_path}\nERROR: {e}")
                    pbar.update(1)

                elif os.path.isdir(file_path):
                    subfolder_name = utils.get_filename(file_path)
                    subfolder_id = service.create_subfolder(subfolder_name,None,folder_id,update,self.drive_service,self.mode)
                    self.upload_folder(file_path,subfolder_id,update=update,subfolder=False,convert=convert,total_files_to_upload_count=total_files_to_upload_count,pbar=pbar)
                else:
                    # not file nor dir
                    print('\nError uploading file: ' + file_path + '\n(Not file or directory)')
            else:
                self.upload(file_path,folder_id,update=update)

    def download(self,id:str,path:str):
        """Downloads file.

        Downloads the specified drive file content to a local file path. The method checks the file's 
        MIME type to determine how to download it. If the file is a binary file, the method uses the 
        get_media method to download the file directly to the local file path. If the file is a text file, 
        the method uses the export_media method to convert the file to a text format and then download it 
        to the local file path. The exported file will have the extension specified in the path if the 
        conversion is available.

        Args:
            id: Drive file wich content will be downloaded (specified by it's ID)
            path: Local path file in wich the content will be downloaded (name of the file with extension must be included)  
        """
        extension = utils.get_file_extension(path)

        file_metadata = service.get_full_metadata(id,self.drive_service) 
        
        new_extension,export_type = utils.get_export_type(file_metadata,extension)

        # When extension is not specified in path, it is created by default from file's mimeType
        if extension == '':
            path = path + '.' + new_extension

        if export_type == 'error':
            print("\nError downloading file: " + path + "\n." + extension + " extension it's not an available type of convertion for the specified file")

        elif export_type == 'folder-error':
            print("\nError downloading file: " + path + "\n. File id detected as a folder. Download method is not intended for downloading drive folders, use 'download_folder()' instead")
            
        else:
            try:
                service.drive_download(id,path,self.drive_service,mode=export_type)

            except Exception as e:
                print(f"Error downloading file: {path}\nERROR: {e}")
    
    def download_folder(self, local_folder_path :str,folder_id :str,subfolder = False, recursive :bool = True, url :bool = True, files_counter = None, downloaded_files_counter = 0,pbar = None):

        if url == True:
            folder_id = utils.url_to_id(folder_id)

        if subfolder == True:

            folder_metadata = service.get_full_metadata(folder_id,self.drive_service)

            local_folder_path = local_folder_path + '\\' + folder_metadata['name']
            os.makedirs(local_folder_path, exist_ok=True)

        files_list = service.list_files(folder_id,service=self.drive_service)

        if files_counter == None and pbar == None:
            # print('\n> Calculating estimated files number...')
            # recursive_counter = service.files_counter_drive(folder_id,self.drive_service)
            # print(f'Started downloading folder with {recursive_counter} files\n')
            # pbar = tqdm(total = recursive_counter,desc='Total download progress: ')
            pbar = tqdm(total=0,desc='Total download progress: ')

        files_counter = files_counter + (len(files_list)) if files_counter != None else len(files_list)

        pbar.total = files_counter
 
        for file in files_list:
            file_metadata = service.get_full_metadata(file['id'],self.drive_service)
            drive_folder = (file_metadata['mimeType'] == 'application/vnd.google-apps.folder')

            if drive_folder:

                files_counter-=1

                if recursive == True:
                    subfolder_name = local_folder_path + "\\" + file_metadata['name']
                    os.makedirs(subfolder_name, exist_ok=True)
                else:
                    subfolder_name = local_folder_path

                subfolder_file_count,downloaded_subfiles_counter = self.download_folder(subfolder_name,file['id'],recursive=recursive,url=url,files_counter=files_counter,downloaded_files_counter=downloaded_files_counter,pbar=pbar)
                files_counter = subfolder_file_count
                downloaded_files_counter = downloaded_subfiles_counter

            else:
                downloaded_files_counter +=1
                # print(f"Downloading folder's files : {downloaded_files_counter}/{files_counter}")
                file_path = local_folder_path + '\\' + file_metadata['name']
                self.download(file['id'],file_path)
                pbar.update(1)

        return files_counter,downloaded_files_counter
    
    def df_download(self,id:str,sheet_name:str=None,unformat:bool = False):
        """Download content of a drive sheet to a pandas dataframe.

        Downloads content of a drive sheet specified by its id to a pandas dataframe.

        Args:
            id: ID of the drive sheet that will be downloaded.  
            sheet_name: Name of the specific sheet that will be downloaded. If set to None, first sheet of the file will be downloaded.  
            
        """

        if sheet_name == None:
            sheet_metadata = self.sheets_service.spreadsheets().values().get(spreadsheetId=id, range='A1:Z').execute()
        else:
            sheet_metadata = self.sheets_service.spreadsheets().values().get(spreadsheetId=id, range=sheet_name, valueRenderOption='UNFORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        values = sheet_metadata.get('values', [])

        headers = values[0]
        rows = values[1:]

        max_cols = max(len(row) for row in rows)
        max_dimensions = max(len(headers),max_cols)

        headers += [None] * (max_dimensions - len(headers))

        for row in rows:
            row += [None] * (max_dimensions - len(row))

        df = pd.DataFrame(rows,columns=headers)

        if unformat == True:
            df = df.fillna('NULL')
            df = df.astype(str)
            df.columns = df.columns.astype(str)


        return df
