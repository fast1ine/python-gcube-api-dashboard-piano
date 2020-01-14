import serial
from motorprotocol import MotorProtocol
from musicprotocol import MusicProtocol
from utils import Utils

class GenerateProtocol(MotorProtocol, MusicProtocol):
    #FF FF FF FF 00 00 A8 00 0A 01
    PingPong_disconnect_hexlist = [0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0xA8, 0x00, 0x0A, 0x01]
    PingPong_disconnect_bytes = serial.to_bytes(PingPong_disconnect_hexlist)

    def __init__(self, connection_number=1):
        self.connection_number = connection_number
        self.speed_schedule_list = [[]]*self.connection_number
        self.step_schedule_list = [[]]*self.connection_number
        MotorProtocol.__init__(self, self.connection_number)
        MusicProtocol.__init__(self, self.connection_number)

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
        """큐브 1개 작동"""
        ### speed, step 리스트화
        speed = Utils().to_list(speed)
        step_cycle = Utils().to_list(step_cycle)

        ### 옵션, 길이 처리
        if not isinstance(option, str):
             raise ValueError("Option must be str.")
        elif option.lower() == "continue":
            if not (len(speed) == 1):
                raise ValueError("In Continue mode, speed must have 1 element.")
        elif option.lower() == "step":
            if not (len(speed) == len(step_cycle) == 1):
                raise ValueError("In Step mode, speed and step_cycle must have 1 element.")
        elif option.lower() == "schedule":
            if not (len(speed) == len(step_cycle)):
                raise ValueError("In Schedule mode, speed and step must have same length.")
        else:
            raise ValueError("Unknown option.")
        
        ### 큐브 ID 처리
        cube_ID = self._process_cube_ID(cube_ID)

        ### 속도 처리
        sleep_list = [False]*len(speed)
        for i in range(len(speed)):
            if (str(speed[i]).lower() in ["stop", "sleep"]) or speed[i] == 0:
                speed[i] = 0
                sleep_list[i] = True # i번째는 sleep 모드
            else:
                Utils().float_check(speed[i], "stop")
                speed[i] = self.truncate_speed(speed[i]) # speed 자르기
                speed[i] = round(self.RPM_to_SPS(speed[i])) # 단위를 RPM에서 SPS로 변경, 반올림 int화
        ### 속도 스케줄 저장
        if cube_ID != 0xFF:
            self.speed_schedule_list[cube_ID] = speed
        else:
            for i in range(len(self.speed_schedule_list)):
                self.speed_schedule_list[i] = speed

        ### 스텝 처리 (speed=0이면, step_cycle 초만큼 쉼.)
        step = [0]*len(step_cycle)
        if option.lower() == "step" or option.lower() == "schedule":
            for i in range(len(step_cycle)):
                if sleep_list[i]:
                    step_cycle[i] /= 2 # sleep이면 2로 나누면 초 단위가 됨.
                Utils().float_check(step_cycle[i], "stop")
                step_cycle[i] = self.truncate_step(step_cycle[i]) # step 자르기
                step[i] = round(self.cycle_to_step(step_cycle[i])) # 단위를 cycle에서 step으로 변경, 반올림 int화
            ### 스텝 스케줄 저장
            if cube_ID != 0xFF:
                self.step_schedule_list[cube_ID] = step
            else:
                for i in range(len(self.speed_schedule_list)):
                    self.step_schedule_list[i] = step

        ### 일시정지 처리
        if not isinstance(pause, bool):
            raise ValueError("pause must be boolean value.")

        ### 작동 (discovery_group 처리 해야함)
        if option.lower() == "continue":
            if speed[0] == 0:
                print("Stop motor(s).")
            return self.SetContinuousSteps_bytes(cube_ID, speed[0], discovery_group=discovery_group, pause=pause)
        elif option.lower() == "step":
            return self.SetSingleSteps_bytes(cube_ID, speed[0], step[0], discovery_group=discovery_group, pause=pause)
        elif option.lower() == "schedule":
            return self.SetScheduledSteps_bytes(cube_ID, speed, step, discovery_group=discovery_group, pause=pause)

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
        
        ### 길이 처리
        if not len(start_point_list) == len(stop_point_list) == len(repeat_list):
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