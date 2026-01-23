from airflow.hooks.base import BaseHook
from driveup.drive import Drive
from driveup.features.auth import authorize


class DriveUpHook(BaseHook):
    conn_name_attr = 'driveup_conn_id'
    default_conn_name = 'driveup_default'
    conn_type = 'driveup'
    hook_name = 'DriveUp'

    def __init__(self, driveup_conn_id: str = default_conn_name):
        super().__init__()
        self.driveup_conn_id = driveup_conn_id

    def get_conn(self):
        """
        Retrieves the connection from Airflow and validates the JSON extra field.
        """
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
        return Drive(credentials=credentials)
    
    @staticmethod
    def get_ui_field_behaviour():
        """
        Customizes the Airflow Web UI Connection Form.
        Hides Host, Schema, Login, Port. Shows Password (optional) and Extra.
        """
        return {
            "hidden_fields": ["host", "schema", "login", "port"],
            "relabeling": {
                "extra": "DriveUp JSON Config",
            },
            "placeholders": {
                "extra": '{"client_id": "...", "client_secret": "..."}',
            },
        }