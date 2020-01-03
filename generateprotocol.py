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
        Utils().integer_check(number)
        if number < 0:
            raise ValueError("Please enter non-negative number!")

        if number == 1: # 1개
            #DD DD 00 00 00 00 DA 00 0B 00 00
            PingPongG1_connect_hexlist = [0xDD, 0xDD, 0x00, 0x00, 0x00, 0x00, 0xDA, 0x00, 0x0B, 0x00, 0x00]
            return serial.to_bytes(PingPongG1_connect_hexlist)

        #FF FF 00 FF 20 00 AD 00 0B 0A 00
        PingPongGn_connect_hexlist = [0xFF, 0xFF, 0x00, 0xFF, 0x20, 0x00, 0xAD, 0x00, 0x0B, 0x0A, 0x00] # 2개 이상
        PingPongGn_connect_hexlist[4] = number # connection number
        return serial.to_bytes(PingPongGn_connect_hexlist)
    
    def SetContinuousSteps_bytes(self, cube_ID, speed) -> bytes:
        """continuous step motor run"""
        # FF FF FF 01 20 00 CC 00 0F 01 00 00 02 11 11
        PingPong_stepper_hexlist = [0xFF, 0xFF, 0xFF, 0x01, 0x10, 0x00, 0xCC, 0x00, 0x0F, 0x02, 0x00, 0x00, 0x02, 0x00, 0x00]
        
        if str(cube_ID).lower() == 'all':
            cube_ID = 0xFF
        else:
            Utils().integer_check(cube_ID, 'all')
        PingPong_stepper_hexlist[3] = cube_ID # set cube ID (1 to 8)
        
        Utils().integer_check(self.connection_number)
        PingPong_stepper_hexlist[4] = self.connection_number*16 # set connection number

        #PingPong_stepper_hexlist[9] 

        Utils().float_check(speed)
        speed = float(speed)
        if speed == 0:
            PingPong_stepper_hexlist[12] = 1 # pause
        else:
            PingPong_stepper_hexlist[12] = 2 # resume

        converted_speed = [int(speed), int(speed)] # need to convert differently
        PingPong_stepper_hexlist[13:15] = converted_speed
        return serial.to_bytes(PingPong_stepper_hexlist)

    def SetAggregateSteps_bytes(self, cube_ID, speed) -> bytes:
        """step motor command to master robot"""
        # AA AA 00 AA 10 00 CD ~
        PingPong_stepper_hexlist = []
        
        
        return serial.to_bytes(PingPong_stepper_hexlist)

