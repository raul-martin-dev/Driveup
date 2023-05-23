from Driveup.features import utils

# returns metadata for the file (whether it exists or not)
def get_update(name,file_id,folder_id,service,mode):
    if file_id != None: # use specified id
            if mode == 'client':
                file_metadata = {'id':file_id,'name': name,'parents': [folder_id]} # Change name: doesn't work
            else:
                file_metadata = {'id':file_id,'name': name,'parents': folder_id} # Change name: doesn't work

    else: # obtain id for duplicated file (file with same name) and overwrite
        file_id = utils.find_duplicate(list_files(folder_id,service),name = name)
        if file_id != None: # duplicate found
            if mode == 'client':
                file_metadata = {'id':file_id,'name': name,'parents': [folder_id]}
            else:
                file_metadata = {'id':file_id,'name': name,'parents': folder_id}
        else: # duplicate not found
            file_metadata = None

    return file_metadata
    
def list_files(folder_id,service):
    results = service.files().list(q=f"'{folder_id}' in parents and trashed = false", fields="nextPageToken, files(id, name)",supportsAllDrives=True).execute()  
    files = results.get('files', [])
        
    return files
            
def create_subfolder(subfolder_name,subfolder_id,parent_folder_id,update,service,mode):

    subfolder = None

    if update == True:
        subfolder = get_update(subfolder_name,subfolder_id,parent_folder_id,service,mode)
        
    subfolder_metadata = {'name': subfolder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_folder_id]}

    if subfolder == None:
        subfolder = service.files().create(body=subfolder_metadata, fields='id',supportsAllDrives=True).execute()
    else:
        subfolder['mimeType'] = subfolder_metadata['mimeType']

    return subfolder['id']
    
