from Driveup.features import utils
from tqdm import tqdm
import io
from googleapiclient.http import MediaIoBaseDownload

# def find_duplicate(list,name = None,file_id = None):
#     if name == None and file_id == None:
#         # needs to control error
#         pass
#     elif name != None: # name mode

#         for file in list:
#             if file['name'] == name:
#                 file_id = file['id']
            
#         return file_id
       
#     elif file_id != None: # id mode

#         condition = False
#         for file in list:
#             if file['id'] == file_id:
#                 condition = True
            
#         return condition

def find_duplicate(file_metadata,service):

    files_list = list_files(file_metadata['parents'],service)

    files_by_id = {file['id']: file for file in files_list}
    files_by_name = {file['name']: file for file in files_list}

    target_file = file_metadata.get('id',False)
    target_file = files_by_id.get(file_metadata['id']) if target_file else target_file

    # Search first by id if it exists
    if target_file:
        file_metadata.update(target_file)
        return True,file_metadata
    # Search then by name
    else:
        target_file = files_by_name.get(file_metadata['name'])
        if target_file:
            file_metadata.update(target_file)
            return True,file_metadata
        else:
            return False,file_metadata


# def get_update(name,file_id,folder_id,service,mode):
#     """
#     Creates metadata for updating / uploading drive file (whether it exists or not).

#     If file_id is specified, it will be used to retrieve the file metadata.
#     If file_id is not specified, the function will search for a duplicate file
#     (file with the same name) and overwrite it.

#     Args:
#         name: The name of the file.
#         file_id: The file ID.
#         folder_id: The folder ID.
#         service: The Google Drive service.
#         mode: The mode (client / service).

#     Returns:
#         file_metadata: The file metadata.
#     """
#     if file_id != None:
#             if mode == 'client':
#                 file_metadata = {'id':file_id,'name': name,'parents': [folder_id]}
#             else:
#                 file_metadata = {'id':file_id,'name': name,'parents': folder_id}

#     else:
#         file_id = utils.find_duplicate(list_files(folder_id,service),name = name)
#         if file_id != None:
#             if mode == 'client':
#                 file_metadata = {'id':file_id,'name': name,'parents': [folder_id]}
#             else:
#                 file_metadata = {'id':file_id,'name': name,'parents': folder_id}
#         else:
#             file_metadata = None

#     return file_metadata
    
def list_files(folder_id,service):
    """
    Lists all files in the specified folder.

    Args:
        folder_id: The ID of the folder.
        service: The Google Drive service.

    Returns:
        files: A list of files.
    """
    results = service.files().list(q=f"'{folder_id}' in parents and trashed = false", fields="nextPageToken, files(id, name)",supportsAllDrives=True).execute()  
    files = results.get('files', [])
        
    return files

def files_counter_drive(folder_id,service,count = None):
    count = 0 if count == None else count

    files_list = list_files(folder_id,service)

    for file in files_list:
        file_metadata = get_full_metadata(file['id'],service)

        if file_metadata['mimeType'] == 'application/vnd.google-apps.folder':
            count += files_counter_drive(file_metadata['id'], service, count)
        else:
            count += 1
    
    return count

def get_full_metadata(file_id,service):
    """
    Retrieves complete metadata of a drive file by it's id.

    Metadata of a drive file contains fields like: 'kind', 'name' or 'mimeType'

    Args:
        file_id: The drive file ID.
        service: The Google Drive service.

    Returns:
        file_metadata: The file metadata.
    """
    file_metadata = service.files().get(fileId=file_id,supportsAllDrives=True).execute()
    
    return file_metadata
            
def create_subfolder(subfolder_name,subfolder_id,parent_folder_id,update,service,mode):
    """
    Creates a subfolder in the specified folder.

    If update is True, the function will try to update an existing subfolder
    with the same name. If the subfolder does not exist, it will be created.

    Args:
        subfolder_name: The name of the subfolder.
        subfolder_id: The ID of the subfolder.
        parent_folder_id: The ID of the parent folder.
        update: A boolean value indicating whether to update an existing subfolder.
        service: The Google Drive service.
        mode: The mode (client / service).

    Returns:
        subfolder_id: The ID of the subfolder.
    """
    # Fill metadata for file creation
    subfolder_metadata = {}
    subfolder_metadata['name'] = subfolder_name
    if subfolder_id != None:
        subfolder_metadata['id'] = subfolder_id
    subfolder_metadata['parents'] = parent_folder_id
    subfolder_metadata['mimeType'] = 'application/vnd.google-apps.folder'

    # subfolder = None

    # if update == True:
    #     subfolder = get_update(subfolder_name,subfolder_id,parent_folder_id,service,mode)
        
    # subfolder_metadata = {'name': subfolder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_folder_id]}

    if update == True:
        duplicate_check, subfolder_metadata = find_duplicate(subfolder_metadata,service)
    else:
        duplicate_check = False
        subfolder_metadata.pop('id',None)

    if duplicate_check == False:
        subfolder_metadata['parents'] = [subfolder_metadata['parents']]
        subfolder_new_metadata = service.files().create(body=subfolder_metadata, fields='id',supportsAllDrives=True).execute()
        subfolder_metadata.update(subfolder_new_metadata)
        if mode == 'service':
            old_parents = subfolder_metadata.get('parents')
            file_id = subfolder_metadata.get('id')

            subfolder_metadata = service.files().update(fileId=file_id,removeParents=old_parents,addParents=old_parents,supportsAllDrives=True).execute()
    print(subfolder_metadata)
    return subfolder_metadata['id']

    # if subfolder == None:
    #     subfolder = service.files().create(body=subfolder_metadata, fields='id',supportsAllDrives=True).execute()
    # else:
    #     subfolder['mimeType'] = subfolder_metadata['mimeType']

    # return subfolder['id']
    
def drive_download(id,path,service ,mode):

    # Unable to get real size of the file (without duplicating API calls)
    size = 0

    pbar = tqdm(total = 100)

    if mode == 'binary':
        pbar.update(10)
        request = service.files().get_media(fileId=id)
        pbar.update(20)
        fh = io.FileIO(path, 'wb')

        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
        pbar.update(70)

    else:
        pbar.update(10)
        request = service.files().export_media(fileId=id, mimeType=mode)
        pbar.update(20)
        response = request.execute()
        pbar.update(10)

        with open(path, 'wb') as f:
            f.write(response)
        pbar.update(60)