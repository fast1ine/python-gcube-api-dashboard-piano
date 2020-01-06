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

    def truncate_speed(self, speed) -> int:
        if speed < -60: 
            speed = -60
            print("Warning. Maximum speed is +-60 RPM.")
        elif -6 < speed and speed < 6:
            distance = [abs(speed+6), abs(speed), abs(speed-6)]
            if speed != 0: 
                print("Warning. Minimum speed is +-6 RPM.")
            speed = [-6, 0, 6][distance.index(min(distance))]
        elif speed > 60:
            speed = 60
            print("Warning. Maximum speed is +-60 RPM.")
        return speed

    def PingPongGn_connect_bytes(self, number) -> bytes or list:
        if number < 0:
            raise ValueError("Please enter non-negative number!")
        elif number == 1: # 1개
            #DD DD 00 00 00 00 DA 00 0B 00 00
            PingPongG1_connect_hexlist = [0xDD, 0xDD, 0x00, 0x00, 0x00, 0x00, 0xDA, 0x00, 0x0B, 0x00, 0x00]
            return serial.to_bytes(PingPongG1_connect_hexlist)
        else: # 2개 이상
            #FF FF 00 FF 20 00 AD 00 0B 0A 00
            PingPongGn_connect_hexlist = [0xFF, 0xFF, 0x00, 0xFF, 0x20, 0x00, 0xAD, 0x00, 0x0B, 0x0A, 0x00] 
            PingPongGn_connect_hexlist[4] = self.connection_number*16 # connection number
            return serial.to_bytes(PingPongGn_connect_hexlist)
    
    def SetContinuousSteps_bytes(self, cube_ID, speed, _option = None) -> bytes or list:
        """continuous step motor run"""
        # FF FF FF 00 10 00 CC 00 0F 01 00 00 02 11 11
        SetContinuousSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCC, 0x00, 0x0F, 0x02, 0x00, 0x00, 0x02, 0x00, 0x00]
        
        if str(cube_ID).lower() == 'all':
            cube_ID = 0xFF
        SetContinuousSteps_hexlist[3] = int(cube_ID - 1) # set cube ID (1 to 8 -> 0 to 7)
        SetContinuousSteps_hexlist[4] = self.connection_number*16 # set connection number
        #SetContinuousSteps_hexlist[9] 
        speed = Utils().unsigned16(round(speed * 100/6)) # convert into unsigned16 integer steprate
        if speed == 0:
            SetContinuousSteps_hexlist[12] = 1 # pause
        else:
            SetContinuousSteps_hexlist[12] = 2 # resume
        SetContinuousSteps_hexlist[13:15] = Utils().int_to_hex_n_bytes(speed, 2) # set speed

        if _option == None:
            return serial.to_bytes(SetContinuousSteps_hexlist)
        elif _option == "hex":
            return SetContinuousSteps_hexlist
        else:
            print("Warning: Unavailable option.")
            return serial.to_bytes(SetContinuousSteps_hexlist)

    def SetSingleSteps_bytes(self, cube_ID, method, speed, start_phase, step_value, _option = None) -> bytes:
        """continuous step motor run"""
        # FF FF FF 00 10 00 C1 00 13 02 01 00 02 00 00 00 00 00 00 ~
        SetSingleSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xC1, 0x00, 0x13, 0x02, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        
        if str(cube_ID).lower() == 'all':
            cube_ID = 0xFF
        SetSingleSteps_hexlist[3] = int(cube_ID - 1) # set cube ID (1 to 8 -> 0 to 7)
        SetSingleSteps_hexlist[4] = self.connection_number*16 # set connection number
        SetSingleSteps_hexlist[10] = method # set method (1: RelativeSingleSteps, 2: AbsoluteSingleSteps)
        speed = Utils().unsigned16(round(speed * 100/6)) # convert into unsigned16 integer steprate
        if speed == 0:
            SetSingleSteps_hexlist[12] = 1 # pause
        else:
            SetSingleSteps_hexlist[12] = 2 # resume
        SetSingleSteps_hexlist[13:15] = Utils().int_to_hex_n_bytes(speed, 2) # set speed
        SetSingleSteps_hexlist[15:17] = [0, 0] # set start phase###########3
        SetSingleSteps_hexlist[17:] = [0, 0] # set step value ##############
        
        if _option == None:
            return serial.to_bytes(SetSingleSteps_hexlist)
        elif _option == "hex":
            return SetSingleSteps_hexlist
        else:
            print("Warning: Unavailable option.")
            return serial.to_bytes(SetSingleSteps_hexlist)

    def SetScheduledSteps_bytes(self, cube_ID, speed, step_type, _option = None) -> bytes:
        """continuous step motor run"""
        # FF FF FF 00 10 00 CA 00 15 02 03 00 02 00 00 ~
        SetScheduledSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCA, 0x00, 0x15, 0x02, 0x03, 0x00, 0x02, 0x00, 0x00]
        
        if str(cube_ID).lower() == 'all':
            cube_ID = 0xFF
        SetScheduledSteps_hexlist[3] = int(cube_ID - 1) # set cube ID (1 to 8 -> 0 to 7)
        SetScheduledSteps_hexlist[4] = self.connection_number*16 # set connection number
        SetScheduledSteps_hexlist[11] = step_type # step type (0: FullSteps, 4: SetServo)
        speed = Utils().unsigned16(round(speed * 100/6)) # convert into unsigned16 integer steprate
        if speed == 0:
            SetScheduledSteps_hexlist[12] = 1 # pause
        else:
            SetScheduledSteps_hexlist[12] = 2 # resume
        SetScheduledSteps_hexlist[13:] = [0, 0] # CRC16 ###############
        
        if _option == None:
            return serial.to_bytes(SetScheduledSteps_hexlist)
        elif _option == "hex":
            return SetScheduledSteps_hexlist
        else:
            print("Warning: Unavailable option.")
            return serial.to_bytes(SetScheduledSteps_hexlist)

    def SetScheduledPoints_bytes(self, cube_ID, speed, step_type, _option = None) -> bytes:
        """continuous step motor run"""
        # FF FF FF 00 10 00 CB 00 15 02 04 00 02 00 00 ~
        SetScheduledPoints_hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x10, 0x00, 0xCA, 0x00, 0x15, 0x02, 0x03, 0x00, 0x02, 0x00, 0x00]
        
        if str(cube_ID).lower() == 'all':
            cube_ID = 0xFF
        SetScheduledPoints_hexlist[3] = int(cube_ID - 1) # set cube ID (1 to 8 -> 0 to 7)
        SetScheduledPoints_hexlist[4] = self.connection_number*16 # set connection number
        SetScheduledPoints_hexlist[11] = step_type # step type (0: FullSteps, 4: SetServo)
        speed = Utils().unsigned16(round(speed * 100/6)) # convert into unsigned16 integer steprate
        if speed == 0:
            SetScheduledPoints_hexlist[12] = 1 # pause
        else:
            SetScheduledPoints_hexlist[12] = 2 # resume
        SetScheduledPoints_hexlist[13:] = [0, 0] # CRC16 ###############
        
        if _option == None:
            return serial.to_bytes(SetScheduledPoints_hexlist)
        elif _option == "hex":
            return SetScheduledPoints_hexlist
        else:
            print("Warning: Unavailable option.")
            return serial.to_bytes(SetScheduledPoints_hexlist)

    def SetAggregateSteps_bytes(self, discovery_group, speed_list) -> bytes:
        """step motor command to master robot"""
        # AA AA 01 AA 10 00 CD 00 12 02 00 00 00 ~
        SetAggregateSteps_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xCD, 0x00, 0x12, 0x02, 0x00, 0x00, 0x00]
        SetAggregateSteps_hexlist[2] = discovery_group # set discovery group ID (1 to 8)(?)
        SetAggregateSteps_hexlist[4] = self.connection_number*16 # set connection number
        SetAggregateSteps_hexlist[8] = 13 + self.connection_number*15 # set data number
        #SetAggregateSteps_hexlist[10] # set mode (0: Continuous Steps, 1: Relative Single Steps, 2: Absolute Single Steps,
                                       #           3: Scheduled Steps, 4: Scheduled Points)
        for i in range(self.connection_number):
            SetAggregateSteps_hexlist = SetAggregateSteps_hexlist + self.SetContinuousSteps_bytes(i+1, speed_list[i], _option="hex")

        return serial.to_bytes(SetAggregateSteps_hexlist)

