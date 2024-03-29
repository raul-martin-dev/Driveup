import os
import re

def get_filename(path):
    name = os.path.basename(path)
    name = os.path.splitext(name)[0]

    return name
    
def get_file_extension(path):
    name = os.path.basename(path)
    extension = os.path.splitext(name)[-1]
    extension = extension.lower()
    extension = extension.replace(".", "")

    return extension
    
# Transforms drive folder's URL to id. Returns ID if entry is not URL
def url_to_id(folder_id):
    # regex = r"(https?://)?(www\.)?(drive.google\.com/)?drive/folders/(\w+)"
    # match = re.search(regex, folder_id)
    # if match:
    #     return match.group(4) # (\w+) -> Alphanumeric id
    # else:
    #     return folder_id
    return folder_id[-33:]
       
def convert(file_metadata,extension):
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
        
    if extension in ['docx','rtf']:
        file_metadata['mimeType'] = 'application/vnd.google-apps.document'
    elif extension in ['md','odf']:
        file_metadata['mimeType'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        file_metadata['name'] = file_metadata['name'] + '.' + extension
    elif extension == 'slk':
        file_metadata['mimeType'] = 'application/vnd.google-apps.spreadsheet'
    elif extension == 'prn':
        file_metadata['mimeType'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        file_metadata['name'] = file_metadata['name'] + '.' + extension
    elif extension in permited_general_extensions :
        file_metadata['mimeType'] = 'application/vnd.google-apps.' + extension
    else:
        file_metadata['name'] = file_metadata['name'] + '.' + extension

        
    return file_metadata

def get_export_type(file_metadata,extension):
    
    mime_type = file_metadata.get('mimeType')

    export_type = None

    if mime_type == 'application/vnd.google-apps.document':

        # When extension is not specified in path, it is created by default from file's mimeType
        if extension == '':
            extension = 'docx'

        if extension in ['docx','md']:
            export_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif extension in ['odt','odf','fodt','fodf']:
            export_type = 'application/vnd.oasis.opendocument.text'
        elif extension == 'rtf':
            export_type = 'application/rtf'
        elif extension == 'pdf':
            export_type = 'application/pdf'
        elif extension == 'txt':
            export_type = 'text/plain'
        elif extension == 'zip':
            export_type = 'application/zip'
        elif extension == 'epub':
            export_type = 'application/epub+zip'
        else:
            export_type = "error" # Needs error control

    elif mime_type == 'application/vnd.google-apps.spreadsheet':

        # When extension is not specified in path, it is created by default from file's mimeType
        if extension == '':
            extension = 'xlsx'
        
        if extension in ['xlsx','xls','slk','prn']:
            export_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif extension in ['ods','odf','fods','fodf']:
            export_type = 'application/x-vnd.oasis.opendocument.spreadsheet'
        elif extension == 'pdf':
            export_type = 'application/pdf'
        elif extension == 'zip':
            export_type = 'application/zip'
        elif extension == 'csv':
            export_type = 'text/csv'
        elif extension == 'tsv':
            export_type = 'text/tab-separated-values'
        else:
            export_type = "error" # Needs error control

    elif mime_type == 'application/vnd.google-apps.presentation':

        # When extension is not specified in path, it is created by default from file's mimeType
        if extension == '':
            extension = 'pptx'
        
        if extension in ['pptx','ppt']:
            export_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        elif extension in ['odp','odf','fodp','fodf']:
            export_type = 'application/vnd.oasis.opendocument.presentation'
        elif extension == 'pdf':
            export_type = 'application/pdf'
        elif extension == 'txt':
            export_type = 'text/plain'
        elif extension == 'jpg':
            export_type = 'image/jpeg'
        elif extension == 'png':
            export_type = 'image/png'
        elif extension == 'svg':
            export_type = 'image/svg+xml'
        else:
            export_type = "error" # Needs error control

    elif mime_type == 'application/vnd.google-apps.drawing':

        # When extension is not specified in path, it is created by default from file's mimeType
        if extension == '':
            extension = 'pdf'
        
        if extension == 'pdf':
            export_type = 'application/pdf'
        elif extension == 'jpg':
            export_type = 'image/jpeg'
        elif extension == 'png':
            export_type = 'image/png'
        elif extension == 'svg':
            export_type = 'image/svg+xml'
        else:
            export_type = "error" # Needs error control

    elif mime_type == 'application/vnd.google-apps.script':

        # When extension is not specified in path, it is created by default from file's mimeType
        if extension == '':
            extension = 'json'
        
        if extension == 'json':
            export_type = 'application/vnd.google-apps.script+json'

    elif mime_type == 'application/vnd.google-apps.folder':

        export_type = "folder-error"

    else:
        export_type = 'binary'

    return extension,export_type


        
        
        