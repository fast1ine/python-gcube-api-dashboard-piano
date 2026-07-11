from protocols.motorprotocol import MotorProtocol
from protocols.musicprotocol import MusicProtocol
from protocols.ledmatrixprotocol import LEDMatrixProtocol
from protocols.cubeprotocol import CubeProtocol
from protocols.byteutils import ByteUtils

class GenerateProtocol(MotorProtocol, MusicProtocol, LEDMatrixProtocol, CubeProtocol):
    #FF FF FF FF 00 00 A8 00 0A 01
    PingPong_disconnect_hexlist = [0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0xA8, 0x00, 0x0A, 0x01]
    PingPong_disconnect_bytes = bytes(PingPong_disconnect_hexlist)

    def __init__(self, number, group_id=0):
        self.connection_number = number
        self.group_id = self._validate_group_id(group_id)
        MotorProtocol.__init__(self, number)
        MusicProtocol.__init__(self, number)
        LEDMatrixProtocol.__init__(self, number)
        CubeProtocol.__init__(self, number)

    def _validate_group_id(self, group_id):
        if isinstance(group_id, bool) or not isinstance(group_id, int):
            raise ValueError("Group ID must be an integer encoded as hexadecimal 00 to 77.")
        high_nibble = group_id >> 4
        low_nibble = group_id & 0x0F
        if group_id < 0 or high_nibble > 7 or low_nibble > 7:
            raise ValueError("Group ID must be hexadecimal 00 to 77 using digits 0 to 7.")
        return group_id

    def _process_cube_ID(self, cube_ID):
        if str(cube_ID).lower() == "all":
            cube_ID = 0xFF
        else:
            ByteUtils().integer_check(cube_ID, "all") # 정수 체크
            cube_ID = int(cube_ID) # 정수로 변환 
            if not (1 <= cube_ID and cube_ID <= 8):
                raise ValueError("Cube ID must be between 1 to 8.")
            elif cube_ID > self.connection_number:
                raise ValueError("Cube ID must be less than or equal to connection number.")
            cube_ID -= 1 # (1 to 8 -> 0 to 7)
        return cube_ID

    def _if_all_function(self, func, not_all_arg, all_cond) -> None:
        if all_cond:
            for idx in range(self.connection_number):
                func(idx)
        else:
            func(not_all_arg)

    def DongleInAction_bytes(self) -> bytes:
        #DD DD DD DD 00 01 DA 00 0B 00 0D
        DongleInAction_hexlist = [0xDD, 0xDD, 0xDD, 0xDD, 0x00, 0x01, 0xDA, 0x00, 0x0B, 0x00, 0x0D]
        return bytes(DongleInAction_hexlist)

    def PingPongDongle_connect_bytes(self) -> bytes:
        return bytes([0x00, 0x00, self.group_id, 0x00, 0x00, 0x00, 0xDA, 0x00, 0x0B, 0x00, 0x00])

    def PingPongBLE_connect_bytes(self) -> bytes:
        if self.connection_number == 1:
            return bytes([0xFF, 0xFF, 0x00, 0x07, 0x00, 0x00, 0xCE, 0x00, 0x0E, 0x02, 0x00, 0x00, 0x07, 0x50])

        packet = [
            0xFF,
            0xFF,
            0xFF,
            0xAA,
            self.connection_number << 4,
            0x00,
            0xAD,
            0x00,
            0x0B,
            0x0A,
            0x00,
        ]
        if self.group_id > 0:
            packet[9] = 0x1A
            packet[10] = self.group_id
        return bytes(packet)

    def PingPongGn_connect_bytes(self) -> bytes:
        if self.connection_number == 1: # 1개
            #DD DD 00 00 00 00 DA 00 0B 00 00
            PingPongG1_connect_hexlist = [0xDD, 0xDD, 0x00, 0x00, 0x00, 0x00, 0xDA, 0x00, 0x0B, 0x00, 0x00]
            PingPongG1_connect_hexlist[2] = self.group_id
            return bytes(PingPongG1_connect_hexlist)
        else: # 2개 이상
            #FF FF 00 FF 20 00 AD 00 0B 0A 00
            PingPongGn_connect_hexlist = [0xFF, 0xFF, 0x00, 0xFF, 0x20, 0x00, 0xAD, 0x00, 0x0B, 0x0A, 0x00] 
            PingPongGn_connect_hexlist[4] = self.connection_number*16 # connection number
            if self.group_id > 0:
                PingPongGn_connect_hexlist[2] = self.group_id
                PingPongGn_connect_hexlist[9] = 0x1A
                PingPongGn_connect_hexlist[10] = self.group_id
            return bytes(PingPongGn_connect_hexlist)
    
