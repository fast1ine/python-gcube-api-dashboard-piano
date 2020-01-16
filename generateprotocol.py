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
        self.speed_schedule_list = [[]]*self.connection_number
        self.step_schedule_list = [[]]*self.connection_number
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
                raise ValueError("Cube ID must be less or equal to connection number.")
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
                        start.append(start_and_stop_list[i][0])
                        stop.append(start_and_stop_list[i][1])
                elif isinstance(start_and_stop_list[i], int):
                    start.append(start_and_stop_list[i])
                    stop.append(start_and_stop_list[i])
                else:
                    raise ValueError("start_and_stop_list must have list or int elements.")
            return start, stop
        elif isinstance(start_and_stop_list, int):
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
    
    def run_motor_bytes(self, cube_ID, speed, step_cycle=None, pause=False, discovery_group=None, option="continue") -> bytes:
        pass

    def play_motor_schedule_bytes(self, cube_ID, start_point_list, stop_point_list, repeat_list, discovery_group=None, \
            pause=False):
        ### start, stop, repeat 리스트화
        start_point_list = Utils().to_list(start_point_list)
        stop_point_list = Utils().to_list(stop_point_list)
        repeat_list = Utils().to_list(repeat_list)

        ### 큐브 ID 처리
        cube_ID = self._process_cube_ID(cube_ID)
        if cube_ID == 0xFF:
            cube_ID_idx = 0
        else:
            cube_ID_idx = cube_ID

        # 반복 처리 (리스트 원소가 1개면 전체 반복 모드)
        if len(repeat_list) == 1 and not len(start_point_list) == 1 and not len(stop_point_list) == 1:
            if repeat_list[0] < 0 or 255 < repeat_list[0]:
                raise ValueError("Unavailable number. Repeat must be positive, or smaller than 256.")
            print("Entire repeat mode is on. In this mode, the repeat index is not appeared properly.")
            start_point_list = start_point_list*repeat_list[0]
            stop_point_list = stop_point_list*repeat_list[0]
            repeat_list = [1]*len(start_point_list)

        # 스케줄 체크
        if self.speed_schedule_list[cube_ID_idx] == []:
            raise ValueError("Schedule is not set. Set schedule first before play.")

        ### 길이 처리
        if not len(start_point_list) == len(stop_point_list) == len(repeat_list):
            print(len(start_point_list), len(stop_point_list), len(repeat_list))
            raise ValueError("Start, stop, repeats list length are must be the same.")
        for i in range(len(start_point_list)):
            if isinstance(stop_point_list[i], str) and stop_point_list[i].lower() == "end":
                stop_point_list[i] = list(map(len, self.speed_schedule_list))[cube_ID_idx]-1 # end이면 제일 뒤에 인덱스
            Utils().integer_check(start_point_list[i])
            Utils().integer_check(stop_point_list[i])
            Utils().integer_check(repeat_list[i])
            if start_point_list[i] < 0 or stop_point_list[i] < 0 \
                or len(self.speed_schedule_list[cube_ID_idx])-1 < start_point_list[i] \
                or len(self.speed_schedule_list[cube_ID_idx])-1 < stop_point_list[i]:
                raise ValueError("Unavailable number. Schedule does not have that index.")
            elif stop_point_list[i] < start_point_list[i]:
                raise ValueError("Start index must be less than or equal to stop index.")
            elif repeat_list[i] < 0 or 255 < repeat_list[i]:
                raise ValueError("Unavailable number. Repeat must be positive, or smaller than 256.")

        ### (discovery_group, step_type 처리해야 함)
        return self.SetScheduledPoints_bytes(cube_ID, start_point_list, stop_point_list, repeat_list, discovery_group, pause, 0)

    def pause_motor_bytes(self, pause, cube_ID=None, discovery_group=None, group_mode=False):
        ### 오류 처리
        if not isinstance(group_mode, bool):
            raise ValueError("group_mode must be boolean value.")
        elif not isinstance(pause, bool):
            raise ValueError("pause must be boolean value.")

        ### 그룹 모드 오류 처리
        if group_mode:
            if discovery_group == None:
                raise ValueError("In group mode, discovery_group must not be None.")
            else:
                Utils().integer_check(discovery_group)
        else:
            if cube_ID == None:
                raise ValueError("Not in group mode, cube_ID must not be None.")
            else:
                cube_ID = self._process_cube_ID(cube_ID)

        ### (discovery_group 처리해야 함)
        return self.SetPauseSteps_bytes(pause, cube_ID, discovery_group, group_mode)

    def sync_motor_bytes(self, cube_ID_list):
        pass
