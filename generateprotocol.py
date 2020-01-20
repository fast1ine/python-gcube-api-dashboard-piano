import serial
from motorprotocol import MotorProtocol
from musicprotocol import MusicProtocol
from utils import Utils

class GenerateProtocol(MotorProtocol, MusicProtocol):
    #FF FF FF FF 00 00 A8 00 0A 01
    PingPong_disconnect_hexlist = [0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0xA8, 0x00, 0x0A, 0x01]
    PingPong_disconnect_bytes = serial.to_bytes(PingPong_disconnect_hexlist)

    def __init__(self, number):
        self.connection_number = number
        MotorProtocol.__init__(self, number)
        MusicProtocol.__init__(self, number)

    def _process_cube_ID(self, cube_ID):
        if str(cube_ID).lower() == "all":
            cube_ID = 0xFF
        else:
            Utils().integer_check(cube_ID, "all") # 정수 체크
            cube_ID = int(cube_ID) # 정수로 변환 
            if not (1 <= cube_ID and cube_ID <= 8):
                raise ValueError("Cube ID must be between 1 to 8.")
            elif cube_ID > self.connection_number:
                raise ValueError("Cube ID must be less than or equal to connection number.")
            cube_ID -= 1 # (1 to 8 -> 0 to 7)
        return cube_ID
    
    def _check_start_and_stop_list(self, start_and_stop_list) -> (list, list) or (int, int):
        # Ex)
        # [[1, 2], [3, 4]]
        # [1, 2]
        # [[1, 2], [3, 4], [5, 6]]
        # [2, [2, 3], 3, [4, 5]]
        start = []
        stop = []
        if isinstance(start_and_stop_list, list) or isinstance(start_and_stop_list, tuple):
            for i in range(len(start_and_stop_list)):
                if isinstance(start_and_stop_list[i], list) or isinstance(start_and_stop_list[i], tuple):
                    if len(start_and_stop_list[i]) != 2:
                        raise ValueError("If start_and_stop_list is list of lists (or tuple), elemental list must be 2-length list (or tuple).")
                    elif not isinstance(start_and_stop_list[i][0], int) or not isinstance(start_and_stop_list[i][1], int):
                        #print(start_and_stop_list[0], start_and_stop_list[1])
                        raise ValueError("If start_and_stop_list is list of lists (or tuple), elemental list must have integer elements.")
                    else:
                        ### list 등록
                        start.append(start_and_stop_list[i][0])
                        stop.append(start_and_stop_list[i][1])
                elif isinstance(start_and_stop_list[i], int):
                    ### list 등록
                    start.append(start_and_stop_list[i])
                    stop.append(start_and_stop_list[i])
                else:
                    raise ValueError("start_and_stop_list must have list or int elements.")
            return start, stop
        elif isinstance(start_and_stop_list, int):
            ### list 등록
            start = start_and_stop_list
            stop = start_and_stop_list
            return start, stop
        else:
            raise ValueError("start_and_stop_list must be list (or tuple), or int.")

    def DongleInAction_bytes(self) -> bytes:
        #DD DD DD DD 00 01 DA 00 0B 00 0D
        DongleInAction_hexlist = [0xDD, 0xDD, 0xDD, 0xDD, 0x00, 0x01, 0xDA, 0x00, 0x0B, 0x00, 0x0D]
        return serial.to_bytes(DongleInAction_hexlist)

    def PingPongGn_connect_bytes(self) -> bytes:
        if self.connection_number == 1: # 1개
            #DD DD 00 00 00 00 DA 00 0B 00 00
            PingPongG1_connect_hexlist = [0xDD, 0xDD, 0x00, 0x00, 0x00, 0x00, 0xDA, 0x00, 0x0B, 0x00, 0x00]
            return serial.to_bytes(PingPongG1_connect_hexlist)
        else: # 2개 이상
            #FF FF 00 FF 20 00 AD 00 0B 0A 00
            PingPongGn_connect_hexlist = [0xFF, 0xFF, 0x00, 0xFF, 0x20, 0x00, 0xAD, 0x00, 0x0B, 0x0A, 0x00] 
            PingPongGn_connect_hexlist[4] = self.connection_number*16 # connection number
            return serial.to_bytes(PingPongGn_connect_hexlist)
    
