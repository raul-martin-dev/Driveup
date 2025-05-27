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
        raise ValueError("Column index must be non-negative.")
    letters = ""
    while col_idx >= 0:
        letters = string.ascii_uppercase[col_idx % 26] + letters
        col_idx = col_idx // 26 - 1
    return letters

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
        print(f"Resizing sheet ID {sheet_id} to {rows} rows and {cols} columns.")
        requests = [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {
                            "rowCount": max(1, rows), # Sheet must have at least 1 row/col
                            "columnCount": max(1, cols)
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
            raise # Re-raise for handling in the calling function

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
                  spreadsheet_id: str, # Renamed 'id' to 'spreadsheet_id' for clarity
                  sheet_name: str = None,
                  unformat: bool = False,
                  chunk_size: int = 5000):
        """Update content of a drive sheet with a pandas dataframe.

        This method clears the target sheet, resizes it, then uploads the DataFrame in chunks.

        Args:
            df: Dataframe, or list of them, which information will be used to update drive sheets.
            spreadsheet_id: ID of the Google Spreadsheet that will be updated.
            sheet_name: Name of the sheet that will be updated. If None, first sheet is used.
            unformat: If True, clean df format (NaN to 'NULL', all to string).
            chunk_size: Number of rows to upload per chunk for large dataframes.
        """
        sheets_service = self.sheets_service
        try:
            # Get all sheet properties once to find the target or default sheet
            file_metadata = sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id, fields="sheets(properties(sheetId,title,gridProperties))"
            ).execute()
        except Exception as e:
            print(f"Error fetching spreadsheet metadata for ID {spreadsheet_id}: {e}")
            return

        all_sheet_props = file_metadata.get('sheets', [])

        if isinstance(df, list):
            if len(df) > len(all_sheet_props):
                print(f"Warning: More DataFrames ({len(df)}) provided than sheets ({len(all_sheet_props)}) in the spreadsheet. Extra DataFrames will be ignored.")

            for i, single_df in enumerate(df):
                if i < len(all_sheet_props):
                    current_sheet_props = all_sheet_props[i].get("properties", {})
                    current_sheet_name_from_props = current_sheet_props.get("title", f"Sheet{i+1}") # Fallback name
                    print(f"Recursively updating sheet: '{current_sheet_name_from_props}' with DataFrame at index {i}")
                    self.df_update(single_df, spreadsheet_id, current_sheet_name_from_props,
                                   unformat=unformat, chunk_size=chunk_size)
                else:
                    break # Stop if we run out of sheets in the spreadsheet
            return # Exit after processing list of DFs

        # --- Single DataFrame processing ---
        df_processed = df.copy() # Work on a copy
        if unformat:
            df_processed = df_processed.fillna('NULL')
            df_processed = df_processed.astype(str)
            df_processed.columns = df_processed.columns.astype(str)

        target_sheet_props = None
        if sheet_name:
            for props_item in all_sheet_props:
                if props_item.get("properties", {}).get("title") == sheet_name:
                    target_sheet_props = props_item.get("properties")
                    break
            if not target_sheet_props:
                print(f"Error: Sheet named '{sheet_name}' not found in spreadsheet {spreadsheet_id}.")
                # Option: Create the sheet if it doesn't exist
                # try:
                #     add_sheet_request = {'addSheet': {'properties': {'title': sheet_name}}}
                #     response = sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': [add_sheet_request]}).execute()
                #     new_sheet_props = response.get('replies')[0].get('addSheet').get('properties')
                #     print(f"Sheet '{sheet_name}' created with ID {new_sheet_props.get('sheetId')}.")
                #     target_sheet_props = new_sheet_props
                # except Exception as e_create:
                #     print(f"Failed to create sheet '{sheet_name}': {e_create}")
                #     return
                return # If not creating, then exit
        elif all_sheet_props:
            target_sheet_props = all_sheet_props[0].get("properties") # Default to first sheet
            sheet_name = target_sheet_props.get("title")
        else:
            print(f"Error: No sheets found in spreadsheet {spreadsheet_id} and no sheet_name provided.")
            # Option: Create a default sheet "Sheet1"
            # try:
            #     add_sheet_request = {'addSheet': {'properties': {'title': "Sheet1"}}}
            #     response = sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': [add_sheet_request]}).execute()
            #     new_sheet_props = response.get('replies')[0].get('addSheet').get('properties')
            #     print(f"Default sheet 'Sheet1' created with ID {new_sheet_props.get('sheetId')}.")
            #     target_sheet_props = new_sheet_props
            #     sheet_name = "Sheet1"
            # except Exception as e_create_default:
            #     print(f"Failed to create default sheet 'Sheet1': {e_create_default}")
            #     return
            return # If not creating, then exit

        if not target_sheet_props or 'sheetId' not in target_sheet_props:
            print(f"Error: Could not determine target sheet properties or sheetId for '{sheet_name}'.")
            return

        actual_sheet_name = target_sheet_props['title'] # Use the name from properties for safety
        sheet_id_num = target_sheet_props['sheetId']

        print(f"Processing sheet: '{actual_sheet_name}' (ID: {sheet_id_num}) in spreadsheet: {spreadsheet_id}")

        # 1. Clear all cell values in the target sheet
        print(f"Clearing all values from sheet: '{actual_sheet_name}'...")
        try:
            # Quoting sheet name is good practice for names with spaces/special chars
            clear_range = f"'{actual_sheet_name}'"
            sheets_service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=clear_range,
                body={}
            ).execute()
            print(f"Sheet '{actual_sheet_name}' cleared.")
        except Exception as e:
            print(f"Error clearing sheet '{actual_sheet_name}': {e}")
            return

        # 2. Resize the sheet to a minimal size (e.g., 1x1) to remove old grid structure
        try:
            self._resize_sheet(spreadsheet_id, sheet_id_num, rows=1, cols=1)
        except Exception as e:
            print(f"Halting due to error during initial resize of '{actual_sheet_name}': {e}")
            return

        # Prepare data for upload
        headers_list = df_processed.columns.tolist()
        data_values = df_processed.values.tolist()

        total_rows_to_write = len(data_values)
        num_cols_to_write = len(headers_list) if headers_list else (len(data_values[0]) if data_values else 0)

        if not headers_list and not data_values:
            print(f"DataFrame is empty. Sheet '{actual_sheet_name}' remains cleared and resized to 1x1.")
            # Optionally, resize to 0x0 if supported, or ensure it's truly empty via API
            # However, 1x1 is typically fine.
            return

        # 3. (Optional but recommended) Pre-resize sheet to fit all new data + headers
        # This avoids potential issues with `update` needing to expand the sheet on the fly for very large updates.
        # Google Sheets has limits (e.g., 10M cells total per spreadsheet).
        rows_needed = (1 if headers_list else 0) + total_rows_to_write
        cols_needed = num_cols_to_write
        
        if rows_needed == 0 and cols_needed == 0: # Truly empty df, after header check
            rows_needed = 1
            cols_needed = 1

        print(f"Pre-resizing sheet '{actual_sheet_name}' for {rows_needed} rows and {cols_needed} columns.")
        try:
            self._resize_sheet(spreadsheet_id, sheet_id_num, rows_needed, cols_needed)
        except Exception as e:
            print(f"Warning: Error during pre-resize for data, proceeding with writes: {e}")
            # Continue, as `update` might still work by auto-expanding.

        current_row_gsheet = 1 # Google Sheets is 1-indexed

        # 4. Write Headers
        if headers_list:
            if num_cols_to_write == 0: # Should not happen if headers_list is non-empty
                 print("Error: Headers list exists but num_cols_to_write is 0. This is a bug.")
                 return
            end_col_letter_header = col_idx_to_a1(num_cols_to_write - 1)
            header_range = f"'{actual_sheet_name}'!A{current_row_gsheet}:{end_col_letter_header}{current_row_gsheet}"
            print(f"Writing headers to {header_range}...")
            try:
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=header_range,
                    valueInputOption='USER_ENTERED',
                    body={'values': [headers_list]}
                ).execute()
                print("Headers written.")
                current_row_gsheet += 1
            except Exception as e:
                print(f"Error writing headers to '{actual_sheet_name}': {e}")
                return
        else:
            print(f"No headers to write for sheet '{actual_sheet_name}'.")

        # 5. Write Data in Chunks using update
        if data_values:
            if num_cols_to_write == 0: # If no headers, infer from first data row
                num_cols_to_write = len(data_values[0]) if data_values else 0
                if num_cols_to_write == 0:
                    print("No data columns to write.") # No data and no headers with columns
                    # If we only had headers, sheet is already sized. If no headers, 1x1.
                    return 
            
            end_col_letter_data = col_idx_to_a1(num_cols_to_write - 1)

            print(f"Writing {total_rows_to_write} data rows in chunks of {chunk_size} to '{actual_sheet_name}'...")
            for i in range(0, total_rows_to_write, chunk_size):
                chunk_data = data_values[i:i + chunk_size]
                if not chunk_data: continue

                start_row_for_chunk = current_row_gsheet
                end_row_for_chunk = current_row_gsheet + len(chunk_data) - 1
                
                chunk_range = f"'{actual_sheet_name}'!A{start_row_for_chunk}:{end_col_letter_data}{end_row_for_chunk}"
                
                print(f"  Writing chunk to {chunk_range} (DF rows {i+1} to {min(i + chunk_size, total_rows_to_write)})")
                try:
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=chunk_range,
                        valueInputOption='USER_ENTERED',
                        body={'values': chunk_data}
                    ).execute()
                    current_row_gsheet += len(chunk_data)
                    # time.sleep(0.1) # Small delay, if needed for API rate limits
                except Exception as e:
                    print(f"Error writing chunk to {chunk_range}: {e}")
                    # Implement retry or error aggregation if needed
                    return # Stop on error for now
            print(f"All data written to '{actual_sheet_name}'.")
        else:
            print(f"No data rows to write to '{actual_sheet_name}'.")

        # 6. (Optional) Final trim to exact size, if pre-resize was generous or no data written
        final_rows_written = (1 if headers_list else 0) + total_rows_to_write
        final_cols_written = num_cols_to_write
        if final_rows_written == 0 : final_rows_written = 1 # Min 1 row
        if final_cols_written == 0 : final_cols_written = 1 # Min 1 col

        # Get current grid properties to see if trim is needed
        # current_grid_props = self._get_sheet_properties(spreadsheet_id, actual_sheet_name).get('gridProperties', {})
        # current_rows = current_grid_props.get('rowCount', 0)
        # current_cols = current_grid_props.get('columnCount', 0)
        # if current_rows != final_rows_written or current_cols != final_cols_written:

        print(f"Performing final size adjustment of '{actual_sheet_name}' to {final_rows_written} rows and {final_cols_written} columns.")
        try:
            self._resize_sheet(spreadsheet_id, sheet_id_num, final_rows_written, final_cols_written)
        except Exception as e:
            print(f"Warning: Error during final trim of '{actual_sheet_name}': {e}")

        print(f"Sheet '{actual_sheet_name}' update complete.")

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
