from Driveup.features import utils

def get_update(name,file_id,folder_id,service,mode):
    """
    Gets metadata for the file (whether it exists or not).

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
    
