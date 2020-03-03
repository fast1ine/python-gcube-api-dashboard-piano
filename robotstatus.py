### 상태 저장용 구조체
class RobotStatus():
    def __init__(self, connection_number, discovery_group=None):
        self.controller_status = ControllerStatus(connection_number, discovery_group)
        self.processed_status = ProcessedStatus(connection_number)
class ControllerStatus():
    def __init__(self, connection_number, discovery_group):
        ### discovery group, connection status
        self.discovery_group = discovery_group
        self.connection_number = connection_number
        ### stepper status
        self.stepper_mode = [None]*connection_number
        self.stepper_pause = [None]*connection_number
        self.stepper_speed = [None]*connection_number
        self.stepper_step = [None]*connection_number
        self.stepper_speed_schedule = [[]]*connection_number
        self.stepper_step_schedule = [[]]*connection_number
        self.stepper_schedule_sync_on = [None]*connection_number
        self.stepper_schedule_point_start = [[]]*connection_number
        self.stepper_schedule_point_end = [[]]*connection_number
        self.stepper_schedule_point_repeat = [[]]*connection_number
class ProcessedStatus():
    def __init__(self, connection_number):
        ### connection status
        self.connected_number = 0
        self.MAC_address = [None]*2
        ### stepper status
        self.stepper_agg_set = None
        self.stepper_schedule_set = [None]*connection_number
        self.stepper_point_set = [None]*connection_number
        self.stepper_played_pause = [None]*connection_number
        self.stepper_played_schedule_idx = [None]*connection_number
        self.stepper_played_point_idx = [None]*connection_number
        self.stepper_played_repeat_idx = [None]*connection_number