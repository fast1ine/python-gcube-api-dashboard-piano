import serial
from utils import Utils

class MotorProtocol():
    def __init__(self, connection_number):
        self.connection_number = connection_number


    def _generic_stepper_hexlist(self, hexlist, cube_ID, discovery_group, pause) -> list:
        """generic protocol (discovery_group, cube ID, connection number, pause)"""
        ### set discovery group ID (1 to 8)
        if discovery_group == None:
            hexlist[2] = 0xFF
        else:
            hexlist[2] = discovery_group
        ### set cube ID (1 to 8 -> 0 to 7)
        if str(cube_ID).lower() == 'all':
            hexlist[3] = 0xFF
        else:
            hexlist[3] = int(cube_ID - 1) 
        ### set connection number
        hexlist[4] = self.connection_number*16 
        if pause:
            ### pause protocol
            hexlist[12] = 1 
        else:
            ### resume protocol
            hexlist[12] = 2 
        return hexlist


    def _RPM_to_hexlist(self, speed, n) -> list:
        """convert RPM to SPS in unsigned 16 hex list with n bytes"""
        unsigned_speed = Utils().unsigned16(round(Utils().RPM_to_SPS(speed)))
        return Utils().int_to_hexlist(unsigned_speed, n)


    def truncate_speed(self, speed) -> int or float:
        """truncate speed between -30 to 30 RPM"""
        if speed < -30: 
            speed = -30
            print("Warning. Maximum speed is +-30 RPM.")
        elif -3 < speed and speed < 3:
            distance = [abs(speed+3), abs(speed), abs(speed-3)]
            if speed != 0: 
                print("Warning. Minimum speed is +-3 RPM.")
            speed = [-3, 0, 3][distance.index(min(distance))]
        elif speed > 30:
            speed = 30
            print("Warning. Maximum speed is +-30 RPM.")
        return speed


    def make_dummy(self, in_bytes) -> bytes:
        ## make OP code into 0
        in_bytes_list = list(in_bytes)
        in_bytes_list[6] = 0
        return serial.to_bytes(in_bytes_list)


    def SetContinuousSteps_bytes(self, cube_ID, speed, discovery_group=None, pause=False) -> bytes or list:
        ### FF FF FF 00 10 00 CC 00 0F 01 00 00 02 11 11
        SetContinuousSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCC, 0x00, 0x0F, 0x02, 0x00, 0x00, 0x02, 0x00, 0x00]
        
        ### generic process (discovery group & cube ID & robot number & pause protocol)
        SetContinuousSteps_hexlist = self._generic_stepper_hexlist(SetContinuousSteps_hexlist, cube_ID, discovery_group, pause)
        ### Set mode multirole 
        #SetContinuousSteps_hexlist[9] 
        ### convert & set speed
        SetContinuousSteps_hexlist[13:15] = self._RPM_to_hexlist(speed, 2) 

        return serial.to_bytes(SetContinuousSteps_hexlist)


    def SetSingleSteps_bytes(self, cube_ID, speed, step, discovery_group=None, pause=False) -> bytes or list:
        ### FF FF FF 00 10 00 C1 00 13 02 01 00 02 00 00 00 00 00 00 ~
        SetSingleSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC1, 0x00, 0x13, 0x02, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        
        ### generic process (discovery group & cube ID & robot number & pause protocol)
        SetSingleSteps_hexlist = self._generic_stepper_hexlist(SetSingleSteps_hexlist, cube_ID, discovery_group, pause) 
        ### set method (1: RelativeSingleSteps, 2: AbsoluteSingleSteps)
        #SetSingleSteps_hexlist[10] = method 
        ### convert & set speed
        SetSingleSteps_hexlist[13:15] = self._RPM_to_hexlist(speed, 2) 
        ### set start phase
        #SetSingleSteps_hexlist[15:17] = [0, 0] 
        ### set step value (0 to 65535, [2000 = 1 cycle])
        SetSingleSteps_hexlist[17:19] = Utils().int_to_hexlist(step, 2) 
        
        return serial.to_bytes(SetSingleSteps_hexlist)


    def SetScheduledSteps_bytes(self, cube_ID, speed_seq_list, step_seq_list, discovery_group=None, pause=False, \
            step_type=0, servo_angle_list=None, servo_angle_timeout_list=None) -> bytes or list:
        ### FF FF FF 00 10 00 CA 00 0F 02 03 00 02 00 00 ~
        SetScheduledSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCA, 0x00, 0x0F, 0x02, 0x03, 0x00, 0x02, 0x00, 0x00]
        
        ### generic process (discovery group & cube ID & robot number & pause protocol)
        SetScheduledSteps_hexlist = self._generic_stepper_hexlist(SetScheduledSteps_hexlist, cube_ID, discovery_group, pause) 
        if step_type == 0: 
            ### set data size (stepper)
            SetScheduledSteps_hexlist[7:9] = Utils().int_to_hexlist(15 + 4*len(speed_seq_list), 2)
        elif step_type == 4:
            ### set data size (servo)
            SetScheduledSteps_hexlist[7:9] = Utils().int_to_hexlist(15 + 6*len(speed_seq_list), 2)
        ### step type (0: FullSteps, 4: SetServo)
        SetScheduledSteps_hexlist[11] = step_type 
        ### CRC16 
        #SetScheduledSteps_hexlist[13:15] = [0, 0]
        if step_type == 0: 
            ### Full Step mode
            for i in range(len(speed_seq_list)):
                ### set speed schedule
                SetScheduledSteps_hexlist[15+4*i:17+4*i] = self._RPM_to_hexlist(speed_seq_list[i], 2) 
                ### set step schedule (if speed = 0, sleep [step] ms.)
                SetScheduledSteps_hexlist[17+4*i:19+4*i] = Utils().int_to_hexlist(step_seq_list[i], 2) 
        elif step_type == 4: 
            ### Servo mode
            for i in range(len(speed_seq_list)):
                ### set speed schedule
                SetScheduledSteps_hexlist[15+6*i:17+6*i] = self._RPM_to_hexlist(speed_seq_list[i], 2) 
                ### set step schedule
                SetScheduledSteps_hexlist[17+6*i:19+6*i] = Utils().int_to_hexlist(step_seq_list[i], 2) 
                ### set servo angle (0 to 180 deg)
                SetScheduledSteps_hexlist[19+6*i] = servo_angle_list[i] 
                ### set servo timeout (1 to 255 sec, 0 for 21.845 min)
                SetScheduledSteps_hexlist[20+6*i] = servo_angle_timeout_list[i] 

        return serial.to_bytes(SetScheduledSteps_hexlist)


    def SetScheduledPoints_bytes(self, cube_ID, start_point_list, stop_point_list, repeats_list, discovery_group=None, \
            pause=False, step_type=0) -> bytes or list:
        ### FF FF FF 00 10 00 CB 00 0F 02 04 00 02 00 00 ~
        SetScheduledPoints_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCB, 0x00, 0x0F, 0x02, 0x03, 0x00, 0x02, 0x00, 0x00]
        
        ### generic process (cube ID & robot number & pause protocol)
        SetScheduledPoints_hexlist = self._generic_stepper_hexlist(SetScheduledPoints_hexlist, cube_ID, discovery_group, pause) 
        ### set data size
        SetScheduledPoints_hexlist[7:9] = Utils().int_to_hexlist(15 + 5*len(start_point_list), 2) 
        ### step type (0: FullSteps, 4: SetServo)
        SetScheduledPoints_hexlist[11] = step_type 
        ### CRC16 
        #SetScheduledPoints_hexlist[13:15] = [0, 0]
        for i in range(len(start_point_list)):
            ### set start point of schedule
            SetScheduledPoints_hexlist[15+5*i:17+5*i] = Utils().int_to_hexlist(start_point_list[i], 2)
            ### set stop point of schedule
            SetScheduledPoints_hexlist[17+5*i:19+5*i] = Utils().int_to_hexlist(stop_point_list[i], 2) 
            ### set repeat time of schedule
            SetScheduledPoints_hexlist[19+5*i] = repeats_list[i] 

        return serial.to_bytes(SetScheduledPoints_hexlist)


    def SetAggregateSteps_bytes(self, discovery_group, *in_bytes) -> bytes:
        """step motor command to master robot"""
        ### AA AA 01 AA 10 00 CD 00 12 02 00 00 00 ~
        SetAggregateSteps_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xCD, 0x00, 0x12, 0x02, 0x00, 0x00, 0x00]

        ### set discovery group ID (0 to 8)
        if discovery_group == None:
            SetAggregateSteps_hexlist[2] = 0xFF
        else:
            SetAggregateSteps_hexlist[2] = discovery_group
        ### set connection number
        SetAggregateSteps_hexlist[4] = self.connection_number*16 
        ### get total data size
        in_bytes_length = len(in_bytes)
        total_length = 0
        for i in range(in_bytes_length):
            total_length = total_length + len(in_bytes[i])
        ### set data number
        SetAggregateSteps_hexlist[7:9] = Utils().int_to_hexlist(13 + total_length, 2) 
        if in_bytes[0][6] == 0xCC:
            ### Continuous Steps
            SetAggregateSteps_hexlist[10] = 0 
        elif in_bytes[0][6] == 0xC1:
            ### Relative Single Steps
            SetAggregateSteps_hexlist[10] = 1
        elif in_bytes[0][6] == 0xCA:
            ### Scheduled Steps
            SetAggregateSteps_hexlist[10] = 3
        elif in_bytes[0][6] == 0xCB:
            ### Scheduled Points
            SetAggregateSteps_hexlist[10] = 4

        SetAggregateSteps_hexlist = serial.to_bytes(SetAggregateSteps_hexlist)
        for i in range(in_bytes_length):
             ### attatch in_bytes
            SetAggregateSteps_hexlist = SetAggregateSteps_hexlist + in_bytes[i]

        return SetAggregateSteps_hexlist


    def SetPauseSteps_bytes(self, pause, cube_ID=None, discovery_group=None, agg=False) -> bytes:
        if not agg:
            ### FF FF FF 00 10 00 C0 00 0A 02
            SetPauseSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC0, 0x00, 0x0A, 0x02]
            ### set discovery group
            if discovery_group == None:
                SetPauseSteps_hexlist[2] = 0xFF
            else:
                SetPauseSteps_hexlist[2] = discovery_group
            ### set cube ID (1 to 8 -> 0 to 7)
            if str(cube_ID).lower() == 'all':
                SetPauseSteps_hexlist[3] = 0xFF
            else:
                SetPauseSteps_hexlist[3] = int(cube_ID - 1) 
            ### set connection number
            SetPauseSteps_hexlist[4] = self.connection_number*16 
            if pause:
                ### pause protocol
                SetPauseSteps_hexlist[9] = 1 
            else:
                ### resume protocol
                SetPauseSteps_hexlist[9] = 2 
        else: 
            ### aggregate mode
            ### AA AA 01 AA 10 00 C0 00 0A 02
            SetPauseSteps_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xC0, 0x00, 0x0A, 0x02]
            ### set discovery group
            if discovery_group == None:
                SetPauseSteps_hexlist[2] = 0xFF
            else:
                SetPauseSteps_hexlist[2] = discovery_group
            ### set connection number
            SetPauseSteps_hexlist[4] = self.connection_number*16 
            if pause:
                ### pause protocol
                SetPauseSteps_hexlist[9] = 1 
            else:
                ### resume protocol
                SetPauseSteps_hexlist[9] = 2 
        return serial.to_bytes(SetPauseSteps_hexlist)


    def SetInstantTorque(self, is_max_torque, cube_ID=None, discovery_group=None, agg=False) -> bytes:
        # SPS > 700
        if not agg:
            ### FF FF FF 00 10 00 C0 00 0A 02
            SetInstantTorque_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC6, 0x00, 0x0A, 0x02]
            ### set discovery group
            if discovery_group == None:
                SetInstantTorque_hexlist[2] = 0xFF
            else:
                SetInstantTorque_hexlist[2] = discovery_group
            ### set cube ID (1 to 8 -> 0 to 7)
            if str(cube_ID).lower() == 'all':
                SetInstantTorque_hexlist[3] = 0xFF
            else:
                SetInstantTorque_hexlist[3] = int(cube_ID - 1) 
            ### set connection number
            SetInstantTorque_hexlist[4] = self.connection_number*16
            if is_max_torque:
                ### max torque
                SetInstantTorque_hexlist[9] = 1 
            else:
                ### default torque
                SetInstantTorque_hexlist[9] = 0 
        else: ### aggregate mode
            # AA AA 01 AA 10 00 C0 00 0A 02
            SetInstantTorque_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xC6, 0x00, 0x0A, 0x02]
            ### set discovery group
            if discovery_group == None:
                SetInstantTorque_hexlist[2] = 0xFF
            else:
                SetInstantTorque_hexlist[2] = discovery_group
            ### set connection number
            SetInstantTorque_hexlist[4] = self.connection_number*16 
            if is_max_torque:
                ### max torque
                SetInstantTorque_hexlist[9] = 1 
            else:
                ### default torque
                SetInstantTorque_hexlist[9] = 0 
        return serial.to_bytes(SetInstantTorque_hexlist)


    def SetSingleServo(self, cube_ID, servo_value, timeout, discovery_group=None):
        SetSingleServo_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0xE1, 0x00, 0x0D, 0x02, 0x00, 0x00, 0x01]
        ### set discovery group
        if discovery_group == None:
            SetSingleServo_hexlist[2] = 0xFF
        else:
            SetSingleServo_hexlist[2] = discovery_group
        ### set cube ID (1 to 8 -> 0 to 7)
        if str(cube_ID).lower() == 'all':
            SetSingleServo_hexlist[3] = 0xFF
        else:
            SetSingleServo_hexlist[3] = int(cube_ID - 1) 
        ### Method?
        #SetSingleServo_hexlist[10]
        ### set servo value (0 to 180 deg)
        SetSingleServo_hexlist[11] = servo_value
        ### set servo timeout (1 to 255 sec, 0 or 0xFF: 21.845 min ?)
        SetSingleServo_hexlist[12] = timeout