import serial
from utils import Utils

class GenerateProtocol():
    #DD DD DD DD 00 01 DA 00 0B 00 0D
    PingPongDongle_connect_hexlist = [0xDD, 0xDD, 0xDD, 0xDD, 0x00, 0x01, 0xDA, 0x00, 0x0B, 0x00, 0x0D]
    DongleInAction_bytes = serial.to_bytes(PingPongDongle_connect_hexlist)

    #FF FF FF FF 00 00 A8 00 0A 01
    PingPong_disconnect_hexlist = [0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0xA8, 0x00, 0x0A, 0x01]
    PingPong_disconnect_bytes = serial.to_bytes(PingPong_disconnect_hexlist)

    def __init__(self, connection_number=1):
        self.connection_number = connection_number
        self.current_speed_list = [0]*self.connection_number

    def truncate_speed(self, speed) -> int or float:
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

    def PingPongGn_connect_bytes(self, number) -> bytes:
        if number == 1: # 1개
            #DD DD 00 00 00 00 DA 00 0B 00 00
            PingPongG1_connect_hexlist = [0xDD, 0xDD, 0x00, 0x00, 0x00, 0x00, 0xDA, 0x00, 0x0B, 0x00, 0x00]
            return serial.to_bytes(PingPongG1_connect_hexlist)
        else: # 2개 이상
            #FF FF 00 FF 20 00 AD 00 0B 0A 00
            PingPongGn_connect_hexlist = [0xFF, 0xFF, 0x00, 0xFF, 0x20, 0x00, 0xAD, 0x00, 0x0B, 0x0A, 0x00] 
            PingPongGn_connect_hexlist[4] = self.connection_number*16 # connection number
            return serial.to_bytes(PingPongGn_connect_hexlist)
    
    def _generic_stepper_hexlist(self, hexlist, cube_ID, pause) -> list:
        if str(cube_ID).lower() == 'all':
            cube_ID = 0xFF
            hexlist[3] = cube_ID
        else:
            hexlist[3] = int(cube_ID - 1) # set cube ID (1 to 8 -> 0 to 7)
        hexlist[4] = self.connection_number*16 # set connection number
        if pause:
            hexlist[12] = 1 # pause protocol
        else:
            hexlist[12] = 2 # resume protocol
        return hexlist

    def _RPM_to_hexlist(self, speed, n) -> list:
        unsigned_speed = Utils().unsigned16(round(Utils().RPM_to_SPS(speed)))
        return Utils().int_to_hexlist(unsigned_speed, n)

    def SetContinuousSteps_bytes(self, cube_ID, speed, pause=False, _option=None) -> bytes or list:
        # FF FF FF 00 10 00 CC 00 0F 01 00 00 02 11 11
        SetContinuousSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCC, 0x00, 0x0F, 0x02, 0x00, 0x00, 0x02, 0x00, 0x00]
        
        SetContinuousSteps_hexlist = self._generic_stepper_hexlist(SetContinuousSteps_hexlist, cube_ID, pause) # generic process (cube ID & robot number & pause protocol)
        #SetContinuousSteps_hexlist[9] 
        SetContinuousSteps_hexlist[13:15] = self._RPM_to_hexlist(speed, 2) # convert & set speed

        if _option == None:
            return serial.to_bytes(SetContinuousSteps_hexlist)
        elif _option == "hex":
            return SetContinuousSteps_hexlist

    def SetSingleSteps_bytes(self, cube_ID, speed, step, pause=False, _option=None) -> bytes or list:
        # FF FF FF 00 10 00 C1 00 13 02 01 00 02 00 00 00 00 00 00 ~
        SetSingleSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC1, 0x00, 0x13, 0x02, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        
        SetSingleSteps_hexlist = self._generic_stepper_hexlist(SetSingleSteps_hexlist, cube_ID, pause) # generic process (cube ID & robot number & pause protocol)
        #SetSingleSteps_hexlist[10] = method # set method (1: RelativeSingleSteps, 2: AbsoluteSingleSteps)
        SetSingleSteps_hexlist[13:15] = self._RPM_to_hexlist(speed, 2) # convert & set speed
        #SetSingleSteps_hexlist[15:17] = [0, 0] # set start phase
        SetSingleSteps_hexlist[17:19] = Utils().int_to_hexlist(step, 2) # set step value (0 to 65535, [2000 = 1 cycle])
        
        if _option == None:
            return serial.to_bytes(SetSingleSteps_hexlist)
        elif _option == "hex":
            return SetSingleSteps_hexlist

    def SetScheduledSteps_bytes(self, cube_ID, speed_seq_list, step_seq_list, pause=False, \
            servo_angle_list=None, servo_angle_timeout_list=None, step_type=0, _option=None) -> bytes or list:
        # FF FF FF 00 10 00 CA 00 0F 02 03 00 02 00 00 ~
        SetScheduledSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCA, 0x00, 0x0F, 0x02, 0x03, 0x00, 0x02, 0x00, 0x00]
        
        SetScheduledSteps_hexlist = self._generic_stepper_hexlist(SetScheduledSteps_hexlist, cube_ID, pause) # generic process (cube ID & robot number & pause protocol)
        if step_type == 0: # set data size (stepper)
            SetScheduledSteps_hexlist[7:9] = Utils().int_to_hexlist(15 + 4*len(speed_seq_list), 2)
        elif step_type == 4:# set data size (servo)
            SetScheduledSteps_hexlist[7:9] = Utils().int_to_hexlist(15 + 6*len(speed_seq_list), 2)
        SetScheduledSteps_hexlist[11] = step_type # step type (0: FullSteps, 4: SetServo)
        #SetScheduledSteps_hexlist[13:15] = [0, 0] # CRC16 
        if step_type == 0: # Full Step mode
            for i in range(len(speed_seq_list)):
                SetScheduledSteps_hexlist[15+4*i:17+4*i] = self._RPM_to_hexlist(speed_seq_list[i], 2) # set speed schedule
                SetScheduledSteps_hexlist[17+4*i:19+4*i] = Utils().int_to_hexlist(step_seq_list[i], 2) # set speed schedule (if speed = 0, sleep [step]ms.)
        elif step_type == 4: # Servo mode
            for i in range(len(speed_seq_list)):
                SetScheduledSteps_hexlist[15+6*i:17+6*i] = self._RPM_to_hexlist(speed_seq_list[i], 2) # set speed schedule
                SetScheduledSteps_hexlist[17+6*i:19+6*i] = Utils().int_to_hexlist(step_seq_list[i], 2) # set speed schedule
                SetScheduledSteps_hexlist[19+6*i] = servo_angle_list[i] # set servo angle (0 to 180 deg)
                SetScheduledSteps_hexlist[20+6*i] = servo_angle_timeout_list[i] # set servo timeout (1 to 255 sec, 0 for 21.845 min)

        if _option == None:
            return serial.to_bytes(SetScheduledSteps_hexlist)
        elif _option == "hex":
            return SetScheduledSteps_hexlist

    def SetScheduledPoints_bytes(self, cube_ID, start_point_list, stop_point_list, repeats_list, pause=False, \
            step_type=0, _option=None) -> bytes or list:
        # FF FF FF 00 10 00 CB 00 0F 02 04 00 02 00 00 ~
        SetScheduledPoints_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCB, 0x00, 0x0F, 0x02, 0x03, 0x00, 0x02, 0x00, 0x00]
        
        SetScheduledPoints_hexlist = self._generic_stepper_hexlist(SetScheduledPoints_hexlist, cube_ID, pause) # generic process (cube ID & robot number & pause protocol)
        SetScheduledPoints_hexlist[7:9] = Utils().int_to_hexlist(15 + 5*len(start_point_list), 2) # set data size
        SetScheduledPoints_hexlist[11] = step_type # step type (0: FullSteps, 4: SetServo)
        #SetScheduledPoints_hexlist[13:15] = [0, 0] # CRC16 
        for i in range(len(start_point_list)):
            SetScheduledPoints_hexlist[15+5*i:17+5*i] = Utils().int_to_hexlist(start_point_list[i], 2) # set start point of schedule
            SetScheduledPoints_hexlist[17+5*i:19+5*i] = Utils().int_to_hexlist(stop_point_list[i], 2) # set stop point of schedule
            SetScheduledPoints_hexlist[19+5*i] = repeats_list[i] # set stop point of schedule
    
        if _option == None:
            return serial.to_bytes(SetScheduledPoints_hexlist)
        elif _option == "hex":
            return SetScheduledPoints_hexlist

    def SetAggregateSteps_bytes(self, discovery_group, speed_group_list) -> bytes:
        """step motor command to master robot"""
        # AA AA 01 AA 10 00 CD 00 12 02 00 00 00 ~
        SetAggregateSteps_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xCD, 0x00, 0x12, 0x02, 0x00, 0x00, 0x00]

        SetAggregateSteps_hexlist[2] = discovery_group # set discovery group ID (1 to 8)(?)
        SetAggregateSteps_hexlist[4] = self.connection_number*16 # set connection number
        SetAggregateSteps_hexlist[7:9] = Utils().int_to_hexlist(13 + self.connection_number*15, 2) # set data number
        #SetAggregateSteps_hexlist[10] # set mode (0: Continuous Steps, 1: Relative Single Steps, 2: Absolute Single Steps,
                                       #           3: Scheduled Steps, 4: Scheduled Points)
        for i in range(self.connection_number):
            SetAggregateSteps_hexlist = SetAggregateSteps_hexlist + self.SetContinuousSteps_bytes(i+1, speed_group_list[i], _option="hex")

        return serial.to_bytes(SetAggregateSteps_hexlist)

    def SetPauseSteps_bytes(self, pause, cube_ID=None, agg=False, discovery_group=None) -> bytes:
        if not agg:
            # FF FF FF 00 10 00 C0 00 0A 02
            SetPauseSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC0, 0x00, 0x0A, 0x02]
            if str(cube_ID).lower() == 'all':
                cube_ID = 0xFF
                SetPauseSteps_hexlist[3] = cube_ID
            else:
                SetPauseSteps_hexlist[3] = int(cube_ID - 1) # set cube ID (1 to 8 -> 0 to 7)
            SetPauseSteps_hexlist[4] = self.connection_number*16 # set connection number
            if pause:
                SetPauseSteps_hexlist[9] = 1 # pause protocol
            else:
                SetPauseSteps_hexlist[9] = 2 # resume protocol
        else: # aggregate mode
            # AA AA 01 AA 10 00 C0 00 0A 02
            SetPauseSteps_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xC0, 0x00, 0x0A, 0x02]
            SetPauseSteps_hexlist[2] = discovery_group
            SetPauseSteps_hexlist[4] = self.connection_number*16 # set connection number
            if pause:
                SetPauseSteps_hexlist[9] = 1 # pause protocol
            else:
                SetPauseSteps_hexlist[9] = 2 # resume protocol
        return serial.to_bytes(SetPauseSteps_hexlist)

    def SetInstantTorque(self, is_max_torque, cube_ID=None, agg=False, discovery_group=None):
        # SPS > 700
        if not agg:
            # FF FF FF 00 10 00 C0 00 0A 02
            SetInstantTorque_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC6, 0x00, 0x0A, 0x02]
            if str(cube_ID).lower() == 'all':
                cube_ID = 0xFF
                SetInstantTorque_hexlist[3] = cube_ID
            else:
                SetInstantTorque_hexlist[3] = int(cube_ID - 1) # set cube ID (1 to 8 -> 0 to 7)
            SetInstantTorque_hexlist[4] = self.connection_number*16 # set connection number
            if is_max_torque:
                SetInstantTorque_hexlist[9] = 1 # max torque
            else:
                SetInstantTorque_hexlist[9] = 0 # default torque
        else: # aggregate mode
            # AA AA 01 AA 10 00 C0 00 0A 02
            SetInstantTorque_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xC6, 0x00, 0x0A, 0x02]
            SetInstantTorque_hexlist[2] = discovery_group
            SetInstantTorque_hexlist[4] = self.connection_number*16 # set connection number
            if is_max_torque:
                SetInstantTorque_hexlist[9] = 1 # max torque
            else:
                SetInstantTorque_hexlist[9] = 0 # default torque
        return serial.to_bytes(SetInstantTorque_hexlist)