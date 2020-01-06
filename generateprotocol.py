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

    def PingPongGn_connect_bytes(self, number) -> bytes:
        if number < 0:
            raise ValueError("Please enter non-negative number!")

        if number == 1: # 1개
            #DD DD 00 00 00 00 DA 00 0B 00 00
            PingPongG1_connect_hexlist = [0xDD, 0xDD, 0x00, 0x00, 0x00, 0x00, 0xDA, 0x00, 0x0B, 0x00, 0x00]
            return serial.to_bytes(PingPongG1_connect_hexlist)

        #FF FF 00 FF 20 00 AD 00 0B 0A 00
        PingPongGn_connect_hexlist = [0xFF, 0xFF, 0x00, 0xFF, 0x20, 0x00, 0xAD, 0x00, 0x0B, 0x0A, 0x00] # 2개 이상
        PingPongGn_connect_hexlist[4] = self.connection_number*16 # connection number
        return serial.to_bytes(PingPongGn_connect_hexlist)
    
    def SetContinuousSteps_bytes(self, cube_ID, speed) -> bytes:
        """continuous step motor run"""
        # FF FF FF 01 20 00 CC 00 0F 01 00 00 02 11 11
        SetContinuousSteps_hexlist = [0xFF, 0xFF, 0xFF, 0x01, 0x10, 0x00, 0xCC, 0x00, 0x0F, 0x02, 0x00, 0x00, 0x02, 0x00, 0x00]
        
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

        return serial.to_bytes(SetContinuousSteps_hexlist)

    def SetAggregateSteps_bytes(self, discovery_group, speed_list) -> bytes:
        """step motor command to master robot"""
        # AA AA 01 AA 10 00 CD 00 12 02 00 00 00 ~
        SetAggregateSteps_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0x00, 0xCD, 0x00, 0x12, 0x02, 0x00, 0x00, 0x00]
        
        SetAggregateSteps_hexlist[2] = discovery_group # set discovery group ID (1 to 8)

        SetAggregateSteps_hexlist[4] = self.connection_number*16 # set connection number

        SetAggregateSteps_hexlist[8] = 13 + self.connection_number*15 # set data number

        #SetAggregateSteps_hexlist[10] # set mode (0: Continuous Steps, 1: Relative Single Steps, 2: Absolute Single Steps,
                                       #           3: Scheduled Steps, 4: Scheduled Points)

        for i in range(self.connection_number):
            SetAggregateSteps_hexlist = SetAggregateSteps_hexlist + self.SetContinuousSteps_bytes(i+1, speed_list[i])

        return serial.to_bytes(SetAggregateSteps_hexlist)

