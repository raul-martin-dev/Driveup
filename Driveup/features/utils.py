import os
import re

def get_filename(path):
    name = os.path.basename(path)
    name = os.path.splitext(name)[0]

    return name
    
def get_file_extension(path):
    name = os.path.basename(path)
    extension = os.path.splitext(name)[1]
    extension = extension.lower()
    extension = extension.replace(".", "")

    return extension

def find_duplicate(list,name = None,file_id = None):
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
    
# Transforms drive folder's URL to id. Returns ID if entry is not URL
def url_to_id(folder_id):
    regex = r"(https?://)?(www\.)?(drive.google\.com/)?drive/folders/(\w+)"
    match = re.search(regex, folder_id)
    if match:
        return match.group(4) # (\w+) -> Alphanumeric id
    else:
        return folder_id
       
def convert(file_metadata,extension=None):
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
        
        
        