def get_provider_info():
    return {
        "package-name": "driveup",
        "name": "DriveUp",
        "description": "DriveUp provider for Apache Airflow.",
        "hook-class-names": [
            "driveup.providers.airflow.hooks.DriveUpHook"
        ],
        "connection-types": [
            {
                "connection-type": "driveup",  # 
                "hook-class-name": "driveup.providers.airflow.hooks.DriveUpHook"
            }
        ],
        "versions": ["0.9.7"]
    }