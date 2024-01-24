from Driveup.features import utils
from tqdm import tqdm
import io
from googleapiclient.http import MediaIoBaseDownload

def get_update(name,file_id,folder_id,service,mode):
    """
    Creates metadata for updating / uploading drive file (whether it exists or not).

    If file_id is specified, it will be used to retrieve the file metadata.
    If file_id is not specified, the function will search for a duplicate file
    (file with the same name) and overwrite it.

    Args:
        name: The name of the file.
        file_id: The file ID.
        folder_id: The folder ID.
        service: The Google Drive service.
        mode: The mode (client / service).

    Returns:
        file_metadata: The file metadata.
    """
    if file_id != None:
            if mode == 'client':
                file_metadata = {'id':file_id,'name': name,'parents': [folder_id]}
            else:
                file_metadata = {'id':file_id,'name': name,'parents': folder_id}

    else:
        file_id = utils.find_duplicate(list_files(folder_id,service),name = name)
        if file_id != None:
            if mode == 'client':
                file_metadata = {'id':file_id,'name': name,'parents': [folder_id]}
            else:
                file_metadata = {'id':file_id,'name': name,'parents': folder_id}
        else:
            file_metadata = None

    return file_metadata
    
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
    subfolder = None

    if update == True:
        subfolder = get_update(subfolder_name,subfolder_id,parent_folder_id,service,mode)
        
    subfolder_metadata = {'name': subfolder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_folder_id]}

    if subfolder == None:
        subfolder = service.files().create(body=subfolder_metadata, fields='id',supportsAllDrives=True).execute()
    else:
        subfolder['mimeType'] = subfolder_metadata['mimeType']

    return subfolder['id']
    
def drive_download(id,path,service ,mode):

    # Unable to get real size of the file (without duplicating API calls)
    size = 0

    if mode == 'binary':
        request = service.files().get_media(fileId=id)

        fh = io.FileIO(path, 'wb')

        downloader = MediaIoBaseDownload(fh, request)

        with tqdm(total=size, unit='B', unit_scale=True, unit_divisor=1024, ncols=80) as pbar:
            done = False
            while not done:
                status, done = downloader.next_chunk()
                pbar.update(status.resumable_progress - pbar.n)
    else:
        request = service.files().export_media(fileId=id, mimeType=mode)

        response = request.execute()

        with open(path, 'wb') as f:
            with tqdm(total=size, unit='B', unit_scale=True, unit_divisor=1024, ncols=80) as pbar:
                f.write(response)
                pbar.update(len(response))


    print(f'Download complete: {path}')