import serial
from utils import Utils

class MotorProtocol():
    def __init__(self, number):
        self.connection_number = number


    def _set_discovery_group(self, hexlist, discovery_group):
        ### set discovery group ID (1 to 8)
        if discovery_group == None:
            hexlist[2] = 0xFF
        else:
            hexlist[2] = discovery_group
        return hexlist
    

    def _set_cube_ID(self, hexlist, cube_ID):
        ### set cube ID 
        hexlist[3] = cube_ID
        return hexlist


    def _set_connection_number_motor(self, hexlist):
        ### set connection number
        hexlist[4] = self.connection_number*16 
        return hexlist


    def _set_pause(self, hexlist, pause, pause_location):
        ### set pause
        if pause:
            ### pause protocol
            hexlist[pause_location] = 1 
        else:
            ### resume protocol
            hexlist[pause_location] = 2 
        return hexlist


    def _generic_stepper_hexlist(self, hexlist, cube_ID, discovery_group, pause) -> list:
        """generic protocol (discovery_group, cube ID, connection number, pause)"""
        ### set discovery group
        hexlist = self._set_discovery_group(hexlist, discovery_group)
        ### set cube ID (1 to 8 -> 0 to 7)
        hexlist = self._set_cube_ID(hexlist, cube_ID)
        ### set connection number
        hexlist = self._set_connection_number_motor(hexlist)
        ### set pause
        hexlist = self._set_pause(hexlist, pause, 12)
        return hexlist


    def _SPS_to_hexlist(self, speed: int, n: int) -> list:
        """convert SPS to unsigned 16 hex list with n bytes"""
        unsigned_speed = Utils().unsigned16(speed)
        return Utils().int_to_hexlist(unsigned_speed, n)


    def _register_schedule(self):
        pass


    def RPM_to_SPS(self, RPM) -> float:
        if 3 <= RPM and RPM <= 30:
            SPS = 50*(-60/RPM+22)
        elif -30 <= RPM and RPM <= -3:
            SPS = 50*(-60/RPM-22)
        elif RPM == 0:
            SPS = 0
        else:
            SPS = None
        return SPS # -1000 to 1000


    def cycle_to_step(self, cycle) -> float:
        step = cycle*2000
        return step


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


    def truncate_step(self, step) -> int or float:
        """truncate step between 0 to 32.7675 cycle"""
        if step < 0:
            step = 0
            print("Warning. Minimum step cycle is 0.")
        elif step > 32.7675:
            step = 32.7675
            print("Warning. Maximum step cycle is 32.7675.")
        return step


    def make_dummy(self, in_bytes) -> bytes:
        """make OP code into 0"""
        in_bytes_list = list(in_bytes)
        in_bytes_list[6] = 0
        return serial.to_bytes(in_bytes_list)


    def SetContinuousSteps_bytes(self, cube_ID, speed, discovery_group=None, pause=False) -> bytes:
        ### FF FF FF 00 10 00 CC 00 0F 01 00 00 02 11 11
        hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCC, 0x00, 0x0F, 0x02, 0x00, 0x00, 0x02, 0x00, 0x00]
        
        ### generic process (discovery group & cube ID & robot number & pause protocol)
        hexlist = self._generic_stepper_hexlist(hexlist, cube_ID, discovery_group, pause)
        ### Set mode multirole 
        #hexlist[9] 
        ### convert & set speed
        hexlist[13:15] = self._SPS_to_hexlist(round(speed), 2) 
        return serial.to_bytes(hexlist)


    def SetSingleSteps_bytes(self, cube_ID, speed, step, discovery_group=None, pause=False) -> bytes:
        ### FF FF FF 00 10 00 C1 00 13 02 01 00 02 00 00 00 00 00 00 ~
        hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC1, 0x00, 0x13, 0x02, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        
        ### generic process (discovery group & cube ID & robot number & pause protocol)
        hexlist = self._generic_stepper_hexlist(hexlist, cube_ID, discovery_group, pause) 
        ### set method (1: RelativeSingleSteps, 2: AbsoluteSingleSteps)
        #hexlist[10] = method 
        ### convert & set speed
        hexlist[13:15] = self._SPS_to_hexlist(round(speed), 2) 
        ### set start phase
        #hexlist[15:17] = [0, 0] 
        ### set step value (0 to 65535, [2000 = 1 cycle])
        hexlist[17:19] = Utils().int_to_hexlist(round(step), 2) 
        return serial.to_bytes(hexlist)


    def SetScheduledSteps_bytes(self, cube_ID, speed_seq_list, step_seq_list, discovery_group=None, pause=False, \
            step_type=0, servo_angle_list=None, servo_angle_timeout_list=None) -> bytes:
        ### FF FF FF 00 10 00 CA 00 0F 02 03 00 02 00 00 ~
        hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCA, 0x00, 0x0F, 0x02, 0x03, 0x00, 0x02, 0x00, 0x00]
        
        ### generic process (discovery group & cube ID & robot number & pause protocol)
        hexlist = self._generic_stepper_hexlist(hexlist, cube_ID, discovery_group, pause) 
        if step_type == 0: 
            ### set data size (stepper)
            hexlist[7:9] = Utils().int_to_hexlist(15 + 4*len(speed_seq_list), 2)
        elif step_type == 4:
            ### set data size (servo)
            hexlist[7:9] = Utils().int_to_hexlist(15 + 6*len(speed_seq_list), 2)
        ### step type (0: FullSteps, 4: SetServo)
        hexlist[11] = step_type 
        ### CRC16 
        hexlist[13:15] = [0, 0]
        if step_type == 0: 
            ### Full Step mode
            for i in range(len(speed_seq_list)):
                ### set speed schedule
                hexlist.extend(self._SPS_to_hexlist(round(speed_seq_list[i]), 2))
                ### set step schedule (if speed = 0, sleep [step] ms.)
                hexlist.extend(Utils().int_to_hexlist(round(step_seq_list[i]), 2))
        elif step_type == 4: 
            ### Servo mode
            for i in range(len(speed_seq_list)):
                ### set speed schedule
                hexlist.extend(self._SPS_to_hexlist(round(speed_seq_list[i]), 2))
                ### set step schedule
                hexlist.extend(Utils().int_to_hexlist(round(step_seq_list[i]), 2))
                ### set servo angle (0 to 180 deg)
                hexlist.append(servo_angle_list[i])
                ### set servo timeout (1 to 255 sec, 0 for 21.845 min)
                hexlist.append(servo_angle_timeout_list[i])
        return serial.to_bytes(hexlist)


    def SetScheduledPoints_bytes(self, cube_ID, start_point_list, stop_point_list, repeat_list, discovery_group=None, \
            pause=False, step_type=0) -> bytes:
        ### FF FF FF 00 10 00 CB 00 0F 02 04 00 02 00 00 ~
        hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCB, 0x00, 0x0F, 0x02, 0x04, 0x00, 0x02, 0x00, 0x00]
        
        ### generic process (cube ID & robot number & pause protocol)
        hexlist = self._generic_stepper_hexlist(hexlist, cube_ID, discovery_group, pause) 
        ### set data size
        hexlist[7:9] = Utils().int_to_hexlist(15 + 5*len(start_point_list), 2) 
        ### step type (0: FullSteps, 4: SetServo)
        hexlist[11] = step_type 
        ### CRC16 
        #hexlist[13:15] = [0, 0]
        for i in range(len(start_point_list)):
            ### set start point of schedule
            hexlist.extend(Utils().int_to_hexlist(start_point_list[i], 2))
            ### set stop point of schedule
            hexlist.extend(Utils().int_to_hexlist(stop_point_list[i], 2))
            ### set repeat time of schedule
            hexlist.append(repeat_list[i])
        return serial.to_bytes(hexlist)


    def SetAggregateSteps_bytes(self, discovery_group, *in_bytes) -> bytes:
        """step motor command to master robot"""
        ### AA AA 01 AA 10 00 CD 00 12 02 00 00 00 ~
        hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xCD, 0x00, 0x12, 0x02, 0x00, 0x00, 0x00]

        ### set discovery group ID (0 to 8)
        hexlist = self._set_discovery_group(hexlist, discovery_group)
        ### set connection number
        hexlist = self._set_connection_number_motor(hexlist)
        ### get total data size
        in_bytes_length = len(in_bytes)
        total_length = 0
        for i in range(in_bytes_length):
            total_length = total_length + len(in_bytes[i])
        ### set data number
        hexlist[7:9] = Utils().int_to_hexlist(13 + total_length, 2) 
        if in_bytes[0][6] == 0xCC:
            ### Continuous Steps
            hexlist[10] = 0 
        elif in_bytes[0][6] == 0xC1:
            ### Relative Single Steps
            hexlist[10] = 1
        elif in_bytes[0][6] == 0xCA:
            ### Scheduled Steps
            hexlist[10] = 3
        elif in_bytes[0][6] == 0xCB:
            ### Scheduled Points
            hexlist[10] = 4
        ### attatch in_bytes
        for i in range(in_bytes_length):
            hexlist.extend(list(in_bytes[i]))
        return serial.to_bytes(hexlist)


    def SetPauseSteps_bytes(self, pause, cube_ID=None, discovery_group=None, agg=False) -> bytes:
        if not agg:
            ### FF FF FF 00 10 00 C0 00 0A 02
            hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC0, 0x00, 0x0A, 0x02]
            ### set discovery group
            hexlist = self._set_discovery_group(hexlist, discovery_group)
            ### set cube ID 
            hexlist = self._set_cube_ID(hexlist, cube_ID)
            ### set connection number
            hexlist = self._set_connection_number_motor(hexlist)
            ### set pause
            hexlist = self._set_pause(hexlist, pause, 9)
        else: 
            ### aggregate mode
            ### AA AA 01 AA 10 00 C0 00 0A 02
            hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xC0, 0x00, 0x0A, 0x02]
            ### set discovery group
            hexlist = self._set_discovery_group(hexlist, discovery_group)
            ### set connection number
            hexlist = self._set_connection_number_motor(hexlist)
            ### set pause
            hexlist = self._set_pause(hexlist, pause, 9)
        return serial.to_bytes(hexlist)


    def SetInstantTorque(self, is_max_torque, cube_ID=None, discovery_group=None, agg=False) -> bytes:
        # SPS > 700
        if not agg:
            ### FF FF FF 00 10 00 C0 00 0A 02
            hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC6, 0x00, 0x0A, 0x02]
            ### set discovery group
            hexlist = self._set_discovery_group(hexlist, discovery_group)
            ### set cube ID (1 to 8 -> 0 to 7)
            hexlist = self._set_cube_ID(hexlist, cube_ID)
            ### set connection number
            hexlist = self._set_connection_number_motor(hexlist)
            if is_max_torque:
                ### max torque
                hexlist[9] = 1 
            else:
                ### default torque
                hexlist[9] = 0 
        else: 
            ### aggregate mode
            # AA AA 01 AA 10 00 C0 00 0A 02
            hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xC6, 0x00, 0x0A, 0x02]
            ### set discovery group
            hexlist = self._set_discovery_group(hexlist, discovery_group)
            ### set connection number
            hexlist = self._set_connection_number_motor(hexlist)
            if is_max_torque:
                ### max torque
                hexlist[9] = 1 
            else:
                ### default torque
                hexlist[9] = 0 
        return serial.to_bytes(hexlist)


    def SetSingleServo(self, cube_ID, servo_value, timeout, discovery_group=None) -> bytes:
        hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0xE1, 0x00, 0x0D, 0x02, 0x00, 0x00, 0x01]
        ### set discovery group
        hexlist = self._set_discovery_group(hexlist, discovery_group)
        ### set cube ID (1 to 8 -> 0 to 7)
        hexlist = self._set_cube_ID(hexlist, cube_ID)
        ### Method?
        #hexlist[10]
        ### set servo value (0 to 180 deg)
        hexlist[11] = servo_value
        ### set servo timeout (1 to 255 sec, 0 or 0xFF: 21.845 min ?)
        hexlist[12] = timeout
        return serial.to_bytes(hexlist)