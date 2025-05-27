from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pandas as pd
# import io
# from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm
import string

from Driveup.features import utils,service

from typing import overload,Union,List, Optional

def col_idx_to_a1(col_idx: int) -> str:
    """Converts a 0-indexed column number into an A1 notation letter (e.g., 0 -> A, 26 -> AA)."""
    if col_idx < 0:
        # This case should ideally be prevented by ensuring num_cols >= 1 before calling
        raise ValueError("Column index must be non-negative for A1 notation.")
    letters = ""
    # Handle 0-indexed to 1-indexed for typical algorithm
    idx = col_idx
    while idx >= 0:
        letters = string.ascii_uppercase[idx % 26] + letters
        idx = idx // 26 - 1
    return letters if letters else "A" # Should not be empty if col_idx >=0

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

    def _get_sheet_properties(self, spreadsheet_id: str, sheet_name: str) -> Optional[dict]:
        """Helper to get sheet properties (including sheetId) from sheetName."""
        try:
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id, fields="sheets(properties(sheetId,title,gridProperties))"
            ).execute()
            for sheet in spreadsheet.get('sheets', []):
                props = sheet.get('properties', {})
                if props.get('title') == sheet_name:
                    return props
            return None
        except Exception as e:
            print(f"Error getting sheet properties for '{sheet_name}': {e}")
            return None

    def _resize_sheet(self, spreadsheet_id: str, sheet_id: int, rows: int, cols: int):
        """Resizes the given sheet to specified rows and columns."""
        effective_rows = max(1, rows)
        effective_cols = max(1, cols)
        print(f"Resizing sheet ID {sheet_id} to {effective_rows} rows and {effective_cols} columns.")
        requests = [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {
                            "rowCount": effective_rows,
                            "columnCount": effective_cols
                        }
                    },
                    "fields": "gridProperties(rowCount,columnCount)"
                }
            }
        ]
        try:
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests}
            ).execute()
            print(f"Sheet ID {sheet_id} resized successfully.")
        except Exception as e:
            print(f"Error resizing sheet ID {sheet_id}: {e}")
            raise e


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
    
    def df_update(self,
                  df: Union[pd.DataFrame, List[pd.DataFrame]],
                  spreadsheet_id: str,
                  sheet_name: str = None,
                  unformat: bool = False,
                  chunk_size: int = 2000,
                  reset_sheet_structure: bool = True):
        """Update content of a drive sheet with a pandas dataframe.

        Args:
            df: DataFrame or list of DataFrames.
            spreadsheet_id: ID of the Google Spreadsheet.
            sheet_name: Name of the sheet. Defaults to the first sheet.
            unformat: If True, fill NaN with 'NULL' and convert all to string.
            chunk_size: Rows per chunk for large DataFrames.
            reset_sheet_structure: If True, the sheet's structure (dimensions and formats)
                                   will be completely reset to fit the new DataFrame, some
                                   calculated columns or aditional formats could be lost.
                                   If False (default), existing formats and dimensions are
                                   preserved, and the sheet is only expanded if necessary.
        """
        sheets_service = self.sheets_service

        # Handle list of DataFrames by recursively calling this method
        if isinstance(df, list):
            # Get all sheet names once for list processing
            try:
                file_metadata_for_list = sheets_service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id, fields="sheets(properties(title))"
                ).execute()
                available_sheets = file_metadata_for_list.get('sheets', [])
            except Exception as e:
                print(f"Error fetching sheet list for multi-DF update: {e}")
                return

            if len(df) > len(available_sheets):
                print(f"Warning: {len(df)} DFs provided, but only {len(available_sheets)} sheets exist. Extra DFs ignored.")

            for i, single_df in enumerate(df):
                if i < len(available_sheets):
                    current_sheet_title = available_sheets[i].get("properties", {}).get("title")
                    if not current_sheet_title:
                        print(f"Warning: Could not get title for sheet at index {i}. Skipping.")
                        continue
                    print(f"Recursively updating sheet: '{current_sheet_title}' with DataFrame at index {i}")
                    self.df_update(single_df, spreadsheet_id, current_sheet_title,
                                   unformat=unformat, chunk_size=chunk_size,
                                   reset_sheet_structure=reset_sheet_structure) # Pass flag
                else:
                    break
            return

        # --- Single DataFrame processing ---
        df_to_process = df.copy()
        if unformat:
            df_to_process = df_to_process.fillna('NULL')
            df_to_process = df_to_process.astype(str)
            if not df_to_process.columns.empty:
                 df_to_process.columns = df_to_process.columns.astype(str)

        # Determine target sheet name and get its properties (including sheetId and current dimensions)
        if not sheet_name: # If no sheet_name, try to get the first one
            try:
                first_sheet_meta = sheets_service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id, fields="sheets(properties(title))" # Only need title for first sheet
                ).execute().get('sheets', [])
                if first_sheet_meta:
                    sheet_name = first_sheet_meta[0].get("properties", {}).get("title")
                else:
                    print(f"Error: Spreadsheet {spreadsheet_id} has no sheets. Cannot determine default sheet.")
                    return
            except Exception as e:
                print(f"Error getting default sheet name: {e}")
                return
        
        target_sheet_props = self._get_sheet_properties(spreadsheet_id, sheet_name)
        if not target_sheet_props:
            print(f"Error: Sheet named '{sheet_name}' not found or properties inaccessible in {spreadsheet_id}.")
            return
        
        sheet_id_num = target_sheet_props['sheetId']
        current_sheet_rows = target_sheet_props.get('gridProperties', {}).get('rowCount', 1)
        current_sheet_cols = target_sheet_props.get('gridProperties', {}).get('columnCount', 1)

        print(f"Processing sheet: '{sheet_name}' (ID: {sheet_id_num}) in spreadsheet: {spreadsheet_id}")

        # Prepare DataFrame data
        headers_list = df_to_process.columns.tolist() if not df_to_process.columns.empty else []
        data_values = df_to_process.values.tolist()
        has_headers = bool(headers_list)
        
        df_num_data_rows = len(data_values)
        df_num_cols = len(headers_list) if has_headers else (len(data_values[0]) if df_num_data_rows > 0 and data_values[0] else 0)
        df_total_rows = (1 if has_headers else 0) + df_num_data_rows

        # Effective dimensions the DataFrame requires (at least 1x1 for sheet operations)
        df_effective_rows = max(1, df_total_rows)
        df_effective_cols = max(1, df_num_cols)

        # 1. Handle Sheet Structure (Resizing)
        if reset_sheet_structure:
            print(f"  Mode: Resetting sheet structure for '{sheet_name}'.")
            try:
                # print(f"    Initial resize to 1x1 to clear old structure...")
                # self._resize_sheet(spreadsheet_id, sheet_id_num, rows=1, cols=1)
                print(f"    Resizing sheet to fit new DataFrame: {df_effective_rows}x{df_effective_cols}.")
                self._resize_sheet(spreadsheet_id, sheet_id_num, df_effective_rows, df_effective_cols)
            except Exception as e:
                print(f"Halting due to error during sheet structure reset of '{sheet_name}': {e}")
                return
        else: # Default: Preserve structure, expand if necessary
            print(f"  Mode: Preserving existing sheet structure for '{sheet_name}'.")
            target_rows_for_sheet = max(current_sheet_rows, df_effective_rows)
            target_cols_for_sheet = max(current_sheet_cols, df_effective_cols)

            if target_rows_for_sheet > current_sheet_rows or target_cols_for_sheet > current_sheet_cols:
                print(f"    Expanding sheet from {current_sheet_rows}x{current_sheet_cols} to {target_rows_for_sheet}x{target_cols_for_sheet}.")
                try:
                    self._resize_sheet(spreadsheet_id, sheet_id_num, target_rows_for_sheet, target_cols_for_sheet)
                except Exception as e:
                    print(f"Halting due to error during sheet expansion of '{sheet_name}': {e}")
                    return
            else:
                print(f"    Sheet is already large enough. No expansion needed.")

        # 2. Clear values from the sheet
        # Original method cleared the whole sheet. This is simple and preserves formats on cells.
        print(f"  Clearing values from entire sheet '{sheet_name}' (preserves cell formats)...")
        try:
            sheets_service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id, range=f"'{sheet_name}'", body={}
            ).execute()
            print(f"  Values cleared from '{sheet_name}'.")
        except Exception as e:
            print(f"Error clearing values from sheet '{sheet_name}': {e}")
            return
        
        # If DataFrame is empty, we're done after clearing and potential resize.
        if df_total_rows == 0:
            print(f"DataFrame is empty. Sheet '{sheet_name}' has been prepared and values cleared.")
            print(f"Sheet '{sheet_name}' update complete (empty).")
            return

        # 3. Upload data (headers and values)
        all_values_to_upload = []
        if has_headers:
            all_values_to_upload.append(headers_list)
        all_values_to_upload.extend(data_values)

        # Use 'USER_ENTERED' to allow existing cell formats to apply to new data
        value_input_option = 'USER_ENTERED'
        
        # Determine end column letter for the actual DataFrame content
        # df_num_cols is 0 if df is empty or has no columns
        end_col_letter_df = col_idx_to_a1(df_num_cols - 1) if df_num_cols > 0 else "A"

        if df_total_rows <= chunk_size: # Small enough for a single update call
            upload_range = f"'{sheet_name}'!A1:{end_col_letter_df}{df_total_rows}"
            print(f"  Uploading {df_total_rows} rows in a single operation to {upload_range}...")
            try:
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=upload_range, # Write to A1 extending to DF's actual size
                    valueInputOption=value_input_option,
                    body={'values': all_values_to_upload}
                ).execute()
                print("  Data written successfully.")
            except Exception as e:
                print(f"Error writing data in single operation to {upload_range}: {e}")
                return
        else: # Chunking required
            print(f"  Uploading {df_total_rows} rows in chunks of {chunk_size}...")
            current_gdrive_row = 1 # 1-indexed for Sheets A1 notation

            # Write headers first
            if has_headers:
                header_range = f"'{sheet_name}'!A{current_gdrive_row}:{end_col_letter_df}{current_gdrive_row}"
                print(f"    Writing headers to {header_range}...")
                try:
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=header_range,
                        valueInputOption=value_input_option,
                        body={'values': [headers_list]}
                    ).execute()
                    current_gdrive_row += 1
                except Exception as e:
                    print(f"Error writing headers to {header_range}: {e}")
                    return
            
            # Write data values in chunks
            print(f"    Writing {df_num_data_rows} data rows in chunks...")
            for i in range(0, df_num_data_rows, chunk_size):
                chunk = data_values[i:i + chunk_size]
                if not chunk: continue

                start_row_for_chunk_in_sheet = current_gdrive_row
                end_row_for_chunk_in_sheet = current_gdrive_row + len(chunk) - 1
                chunk_range = f"'{sheet_name}'!A{start_row_for_chunk_in_sheet}:{end_col_letter_df}{end_row_for_chunk_in_sheet}"
                
                print(f"      Writing chunk to {chunk_range} (DF data rows {i+1} to {min(i+chunk_size, df_num_data_rows)})")
                try:
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=chunk_range,
                        valueInputOption=value_input_option,
                        body={'values': chunk}
                    ).execute()
                    current_gdrive_row += len(chunk)
                except Exception as e:
                    print(f"Error writing data chunk to {chunk_range}: {e}")
                    return
            print("  All data chunks written successfully.")

        print(f"Sheet '{sheet_name}' update complete.")

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
