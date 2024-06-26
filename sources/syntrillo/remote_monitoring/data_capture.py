# Path: ./sources/syntrillo/remote_monitoring/data_capture.py


class RemoteDataCapture:
    """
    Data stored in our PHI database
    - summary statistics : watch data
    - some sparse raw data : BPM and pillbox data

    Data capture:
    - Could run automatically on a schedule to capture (only new) data from the remote monitoring system for all patients
    - Could be run manually to capture data for a specific patient

    """
    def __init__(self) -> None:
        pass

    def capture_data_for_all_patients(self):
        """
        Capture data for all patients
        """
        pass

    def capture_data_for_patient(self, patient_id):
        """
        Capture data for a specific patient
        """
        pass






