class DuplicatePatientError(Exception):
    def __init__(self, healthlink_id: str):
        self.healthlink_id = healthlink_id
