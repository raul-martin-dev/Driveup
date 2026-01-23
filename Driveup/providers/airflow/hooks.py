from airflow.hooks.base import BaseHook
from Driveup.drive import Drive
from Driveup.features.auth import authorize


class DriveUpHook(BaseHook):
    conn_name_attr = 'driveup_conn_id'
    default_conn_name = 'driveup_default'
    conn_type = 'driveup'
    hook_name = 'DriveUp'

    def __init__(self, driveup_conn_id: str = default_conn_name):
        super().__init__()
        self.driveup_conn_id = driveup_conn_id

    def get_conn(self):
        conn = self.get_connection(self.driveup_conn_id)
        
        if not conn.extra:
            raise ValueError("'Extra' field is required in the connection configuration.")
        
        try:
            config_dict = conn.extra_dejson
        except Exception:
            raise ValueError("Extra field is not a valid JSON.")
            
        return config_dict
    
    @property
    def drive(self) -> Drive:
        config = self.get_conn()
        credentials = authorize(config)
        drive_instance = Drive(credentials=credentials)
        return drive_instance