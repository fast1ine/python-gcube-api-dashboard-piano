# Environment: Windows x64, Python x64 3.6.6
# pyserial==3.4

from serialprotocol import ReaderThread
from utils import Utils
from rawprotocol import rawProtocol
from generateprotocol import GenerateProtocol
import sys
import time
import serial

class PingPongThread(ReaderThread):
    _is_instance = False
    _is_start = False
    def __init__(self, number=1):
        Utils().integer_check(number)
        if 1 <= number and number <= 8: # 1개 이상 8개 이하 
            self._robot_status = {}
            self._robot_status[None] = RobotStatus(number, None) # 로봇 상태 저장 (key는 discovery group)
        else:
            raise ValueError("PingPong robot can connect only with 1 to 8 robots.")
        if not PingPongThread._is_instance:
            PingPongThread._is_instance = True # 인스턴스 생성 확인
            self.GenerateProtocolInstance = GenerateProtocol(number) # GenrateProtocol Instance 생성
            self.PORT = Utils().find_bluetooth_dongle(self.GenerateProtocolInstance.DongleInAction_bytes()) # 동글 포트 찾기
            self._play_once_flag = True
        else:
            raise ValueError("PingpongThread instance cannot be constructed above 1.")

    def __del__(self) -> None:
        PingPongThread.is_instance = False
        try:
            self.close()
        except:
            pass

    # 시작 체크
    def _start_check(self):
        if not PingPongThread._is_start:
            raise ValueError("Thread did not start! Please start() before do something, or end thread.")

    # 로봇 연결
    def _connect_robot_thread(self) -> None:
        ser = None
        while True:
            ser = Utils().connect_serial_URL(self.PORT)
            if ser:
                break
            else:
                self.PORT = Utils().find_bluetooth_dongle(self.GenerateProtocolInstance.DongleInAction_bytes())
        ReaderThread.__init__(self, ser, rawProtocol)
        self.write(self.GenerateProtocolInstance.PingPongGn_connect_bytes())

    # 쓰기
    def _write(self, protocol_bytes) -> None:
        try:
            self.write(protocol_bytes)
        except:
            print("Cannot write.")

    # 쓰레드 시작
    def start(self) -> None:
        if not PingPongThread._is_start:
            PingPongThread._is_start = True
            self._connect_robot_thread()
            ReaderThread.start(self)
        else:
            raise ValueError("PingPongThread instance cannot start above 1.")

    # 쓰레드 종료
    def end(self) -> None:
        self._start_check()
        self.disconnect_master_robot()
        self.close()
        print("End thread.")
        PingPongThread._is_start = False

        ## end flag -> serial 보수 ########################
    
    # 로봇 연결 해제
    def disconnect_master_robot(self, discovery_group="all") -> None:
        self._start_check()
        if isinstance(discovery_group, str) and discovery_group.lower() == "all":
            for key in self._robot_status.keys():
                if self._robot_status[key].processed_status.connected_number > 0:
                    self._write(self.GenerateProtocolInstance.PingPong_disconnect_bytes)
                    time.sleep(2) # 응답 기다림
                    self.set_robot_disconnect_flag(True)
                    print("Disconnect master robot.")
                    # 1개는 해제 응답을 안 받음. 2개 이상은 해제 응답을 받음.
                else:
                    print("Master robot is not connected.")
                self._robot_status[key] = RobotStatus(self._robot_status[key].contoller_status.connection_number, key)
        else:
            if self._robot_status[discovery_group].processed_status.connected_number > 0:
                    self._write(self.GenerateProtocolInstance.PingPong_disconnect_bytes)
                    time.sleep(2) # 응답 기다림
                    self.set_robot_disconnect_flag(True)
                    print("Disconnect master robot.")
                    # 1개는 해제 응답을 안 받음. 2개 이상은 해제 응답을 받음.
            else:
                print("Master robot is not connected.")
            self._robot_status[discovery_group] = RobotStatus(self._robot_status[discovery_group].contoller_status.connection_number, discovery_group)
        
    def reconnect_robot(self) -> None:
        print("Reconnect with robots.")
        #self.ReaderThreadInstance.serial.close()
        #self.ReaderThreadInstance.reconnect()
        self._write(self.GenerateProtocolInstance.PingPongGn_connect_bytes())

    def get_is_start(self) -> bool:
        if PingPongThread._is_start: # copy
            return True
        else:
            return False
        
    def get_robot_status(self, discovery_group=None) -> dict: ########### discovery group 하면 수정
        status = \
            {
                "controller_status": self._robot_status[discovery_group].controller_status.__dict__,
                "processed_status": self._robot_status[discovery_group].processed_status.__dict__
            }
        return status

    # 완전 연결 체크 (deprecated)
    def get_is_full_connect(self) -> bool:
        self._start_check()
        is_full_connect_flag = self.is_full_connect
        if not is_full_connect_flag:
            self._play_once_flag = True # play_once용
        return is_full_connect_flag

    # 완전 연결까지 기다림
    def wait_until_full_connect(self) -> None:
        self._start_check()
        while not self.is_full_connect: ##################full connect 다시
            pass
        time.sleep(1)

    # 한 번만 동작
    def play_once_full_connect(self):
        if not self.is_full_connect: # full connection에서 떨어지면 리셋
            self._play_once_flag = True
            return False
        else:
            if self._play_once_flag:
                self._play_once_flag = False
                time.sleep(1)
                return True
            else:
                return False

    # 모터 동작
    def run_motor(self, cube_ID, speed, step_cycle=None, pause=False, discovery_group=None, option="continue") -> None:
        ### start 체크
        self._start_check()

        ### cube_ID, speed, step 리스트화
        cube_ID_list = Utils().to_list(cube_ID)
        speed_list = Utils().to_list(speed)
        step_cycle_list = Utils().to_list(step_cycle)

        ### 옵션 체크, 속도, 스텝 길이 처리
        if not isinstance(option, str):
             raise ValueError("Option must be str.")
        elif option.lower() == "continue":
            if not (len(speed_list) == 1):
                raise ValueError("In Continue mode, speed must have 1 element.")
        elif option.lower() == "step":
            if not (len(speed_list) == len(step_cycle_list) == 1):
                raise ValueError("In Step mode, speed and step_cycle must have 1 element.")
        elif option.lower() == "schedule":
            if not (len(speed_list) == len(step_cycle_list)):
                raise ValueError("In Schedule mode, speed and step must have same length.")
        else:
            raise ValueError("Unknown option.")

        ### 일시정지 처리
        if not isinstance(pause, bool):
            raise ValueError("pause must be bool.")

        ### 큐브 ID 처리
        for i in range(len(cube_ID_list)):
            cube_ID_list[i] = self.GenerateProtocolInstance._process_cube_ID(cube_ID_list[i])
            if cube_ID_list[i] == 0xFF and len(cube_ID_list) != 1:
                raise ValueError("If cube ID is all, input must not be length-above-2 list.")
        
        ### 속도 처리
        sleep_list = [False]*len(speed_list)
        for i in range(len(speed_list)):
            if (str(speed_list[i]).lower() in ["stop", "sleep"]) or speed_list[i] == 0: # 스피드가 0이면 sleep 모드
                speed_list[i] = 0
                sleep_list[i] = True # i번째는 sleep 모드
            else:
                Utils().float_check(speed_list[i], "stop")
                speed_list[i] = self.GenerateProtocolInstance.truncate_speed(speed_list[i]) # speed 자르기
                speed_list[i] = round(self.GenerateProtocolInstance.RPM_to_SPS(speed_list[i])) # 단위를 RPM에서 SPS로 변경, 반올림 int화

        ### 스텝 처리 (speed=0이면, step_cycle 초만큼 쉼.)
        step = [0]*len(step_cycle_list)
        if option.lower() == "step" or option.lower() == "schedule":
            for i in range(len(step_cycle_list)):
                if sleep_list[i]:
                    step_cycle_list[i] /= 2 # sleep이면 2로 나누면 초 단위가 됨.
                Utils().float_check(step_cycle_list[i], "stop")
                step_cycle_list[i] = self.GenerateProtocolInstance.truncate_step(step_cycle_list[i]) # step 자르기
                step[i] = round(self.GenerateProtocolInstance.cycle_to_step(step_cycle_list[i])) # 단위를 cycle에서 step으로 변경, 반올림 int화

        ### 작동 (discovery_group 처리 해야함)
        for cube_ID_element in cube_ID_list:
            ### 옵션 처리
            if option.lower() == "continue": ### 컨티뉴 모드
                if speed_list[0] == 0:
                    print("Stop motor(s).")

                ### 동작
                self._write(self.GenerateProtocolInstance.SetContinuousSteps_bytes(cube_ID_element, speed_list[0], discovery_group, pause))
                time.sleep(0.2)

                ### status 등록
                if cube_ID_element == 0xFF: # all일 때
                    for i in range(self._robot_status[discovery_group].controller_status.connection_number):
                        self._robot_status[discovery_group].controller_status.stepper_mode[i] = "continue"
                        self._robot_status[discovery_group].controller_status.stepper_speed[i] = speed_list[0]
                        self._robot_status[discovery_group].controller_status.stepper_pause[i] = pause
                else:
                    self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "continue"
                    self._robot_status[discovery_group].controller_status.stepper_speed[cube_ID_element] = speed_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause

            elif option.lower() == "step": ### 스텝 모드
                ### 동작
                self._write(self.GenerateProtocolInstance.SetSingleSteps_bytes(cube_ID_element, speed_list[0], step[0], discovery_group, pause))
                time.sleep(0.2)

                ### status 등록
                if cube_ID_element == 0xFF: # all일 때
                    for i in range(self._robot_status[discovery_group].controller_status.connection_number):
                        self._robot_status[discovery_group].controller_status.stepper_mode[i] = "step"
                        self._robot_status[discovery_group].controller_status.stepper_speed[i] = speed_list[0]
                        self._robot_status[discovery_group].controller_status.stepper_step[i] = step[0]
                        self._robot_status[discovery_group].controller_status.stepper_pause[i] = pause
                else:
                    self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "step"
                    self._robot_status[discovery_group].controller_status.stepper_speed[cube_ID_element] = speed_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_step[cube_ID_element] = step[0]
                    self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause

            elif option.lower() == "schedule": ### 스케줄 모드
                ### pause=True 상태로 동작 
                self._write(self.GenerateProtocolInstance.SetScheduledSteps_bytes(cube_ID_element, speed_list, step, True, discovery_group))
                time.sleep(0.2)
                #############################################확인될 때까지 잡아주는 코드 수정

                ### pause=True 포인트로 동작
                if not pause: # 재생
                    self._write(self.GenerateProtocolInstance.SetScheduledPoints_bytes(cube_ID_element, [0], [len(speed_list)], [1], discovery_group, True))
                    time.sleep(0.2)
                    self._write(self.GenerateProtocolInstance.SetPauseSteps_bytes(False, cube_ID_element, discovery_group))
                    time.sleep(0.2)

                ### status 등록
                if cube_ID_element == 0xFF: # all일 때
                    for i in range(self._robot_status[discovery_group].controller_status.connection_number):
                        if not pause: # 재생일 때
                            self._robot_status[discovery_group].controller_status.stepper_mode[i] = "point"
                            self._robot_status[discovery_group].controller_status.stepper_pause[i] = False
                            self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[i] = [0]
                            self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[i] = [len(speed_list)]
                            self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[i] = [1]
                        else:
                            self._robot_status[discovery_group].controller_status.stepper_mode[i] = "schedule"
                            self._robot_status[discovery_group].controller_status.stepper_pause[i] = True
                        self._robot_status[discovery_group].controller_status.stepper_speed_schedule[i] = speed_list
                        self._robot_status[discovery_group].controller_status.stepper_step_schedule[i] = step[0]
                        self._robot_status[discovery_group].controller_status.stepper_pause[i] = pause
                else:
                    if not pause: # 재생일 때
                            self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "point"
                            self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = False
                            self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[cube_ID_element] = [0]
                            self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[cube_ID_element] = [len(speed_list)]
                            self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[cube_ID_element] = [1]
                    else:
                        self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "schedule"
                        self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = True
                    self._robot_status[discovery_group].controller_status.stepper_speed_schedule[cube_ID_element] = speed_list
                    self._robot_status[discovery_group].controller_status.stepper_step_schedule[cube_ID_element] = step
                    self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause

            else:
                # cannot reach
                print("?")



    '''

    # 스케줄 설정
    def set_motor_schedule(self, cube_ID, speed_list, step_cycle_list, pause=True, discovery_group=None) -> None:
        
        connection_number = self._robot_status["controller_status"]["connection_number"]
        self._start_check()
        if not isinstance(pause, bool):
            raise ValueError("pause must be bool.")
        cube_ID = Utils().to_list(cube_ID)
        for i in range(len(cube_ID)):
            if isinstance(cube_ID[i], str):
                if len(cube_ID) != 1:
                    raise ValueError("If cube_ID is list (or tuple), all elements must be int.")
                elif cube_ID[i].lower() != "all": 
                    # len(cube_ID) == 1
                    raise ValueError("cube_ID must be int, or list, or 'all'.")
            if connection_number > 1: # 1이면 반응이 안 옴
                self._write(self.run_motor_bytes(cube_ID[i], speed_list, step_cycle_list, True, discovery_group, "schedule")) # pause
                #while not self.is_schedule_set: # 스케줄 완료가 되면 실행 ####### 다시
                #    pass
                time.sleep(0.2)
                if not pause:
                    self._write(self.pause_motor_bytes(False, cube_ID[i], discovery_group, False)) # play motor
            else:
                self._write(self.run_motor_bytes(cube_ID[i], speed_list, step_cycle_list, pause, discovery_group, "schedule"))
            time.sleep(0.2)

    # 스케줄 실행
    def play_motor_schedule(self, cube_ID, repeat_list=1, start_point_list=None, stop_point_list=None, 
        start_and_stop_list=None, discovery_group=None, pause=False) -> None:
        ### start 체크
        self._start_check()

        ### start, stop, repeat 리스트화
        start_point_list = Utils().to_list(start_point_list)
        stop_point_list = Utils().to_list(stop_point_list)
        repeat_list = Utils().to_list(repeat_list)




        # 스케줄 체크는 play_motor_schedule_bytes 안에서 함
        if not isinstance(pause, bool):
            raise ValueError("pause must be bool.")
        if start_point_list == None and stop_point_list == None: # 스타트, 스탑 포인트 체크
            if start_and_stop_list != None:
                start_point_list, stop_point_list = self._check_start_and_stop_list(start_and_stop_list)
            else:
                start_point_list, stop_point_list = 0, "end"
        elif start_and_stop_list != None:
            print("Warning. start_point_list and stop_point_list are ignored. start_and_stop_list is accepted.")
            start_point_list, stop_point_list = self._check_start_and_stop_list(start_and_stop_list)
        elif start_point_list == None:
            start_point_list = 0
        elif stop_point_list == None:
            stop_point_list = "end"
        
        cube_ID = Utils().to_list(cube_ID)
        for i in range(len(cube_ID)):
            if isinstance(cube_ID[i], str):
                if len(cube_ID) != 1:
                    raise ValueError("If cube_ID is list (or tuple), all elements must be int.")
                elif cube_ID[i].lower() != "all": 
                    # len(cube_ID) == 1
                    raise ValueError("cube_ID must be int, or list, or 'all'.")
            if connection_number > 1: # 1이면 반응이 안 옴
                self._write(self.play_motor_schedule_bytes(cube_ID[i], start_point_list, stop_point_list, repeat_list, \
                    discovery_group, True)) # pause
                #while not self.is_point_set: # 포인트 완료가 되면 실행
                #    pass
                time.sleep(0.2)
                if not pause: # pause가 안 되어 있으면 play
                    self._write(self.pause_motor_bytes(False, cube_ID[i], discovery_group, False)) # play motor
            else:
                self._write(self.play_motor_schedule_bytes(cube_ID[i], start_point_list, stop_point_list, repeat_list, \
                    discovery_group, pause)) 
            time.sleep(0.2)





        

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



























    # 모터 일시정지
    def pause_motor(self, cube_ID=None, discovery_group=None, group_mode=False) -> None:
        self._start_check()
        cube_ID = Utils().to_list(cube_ID)
        for i in range(len(cube_ID)):
            if isinstance(cube_ID[i], str):
                if len(cube_ID) != 1:
                    raise ValueError("If cube_ID is list (or tuple), all elements must be int.")
                elif cube_ID[i].lower() != "all": 
                    # len(cube_ID) == 1
                    raise ValueError("cube_ID must be int, or list, or 'all'.")
            self._write(self.pause_motor_bytes(True, cube_ID[i], discovery_group, group_mode))
            time.sleep(0.2)

    # 모터 재생
    def play_motor(self, cube_ID=None, discovery_group=None, group_mode=False) -> None:
        #############################schedule이면 play 안함
        self._start_check()
        for i in range(len(cube_ID)):
            if isinstance(cube_ID[i], str):
                if len(cube_ID) != 1:
                    raise ValueError("If cube_ID is list (or tuple), all elements must be int.")
                elif cube_ID[i].lower() != "all": 
                    # len(cube_ID) == 1
                    raise ValueError("cube_ID must be int, or list, or 'all'.")
            self._write(self.pause_motor_bytes(False, cube_ID[i], discovery_group, group_mode))
            time.sleep(0.2)
    '''

    '''
    def run_motor_aggregate(self, speed_list) -> None:
        self._start_check()

        if len(speed_list) != self._connection_number:
            raise ValueError("Speed list must be equal to connection number.")

        Utils().float_check(speed_list)
        for i in range(len(speed_list)):
            speed_list[i] = super().truncate_speed(speed_list[i]) # truncate speed into -30 to 30 RPM
        self._write(super().SetAggregateSteps_bytes(1, speed_list))
    '''

#### 상태 저장용
class RobotStatus():
    def __init__(self, connection_number, discovery_group=None):
        self.controller_status = ControllerStatus(connection_number, discovery_group)
        self.processed_status = ProcessedStatus(connection_number)
class ControllerStatus():
    def __init__(self, connection_number, discovery_group):
        ### discovery group, connection status
        self.discovery_group = discovery_group
        self.connection_number = connection_number
        ### stepper status
        self.stepper_mode = [None]*connection_number
        self.stepper_pause = [None]*connection_number
        self.stepper_speed = [None]*connection_number
        self.stepper_step = [None]*connection_number
        self.stepper_speed_schedule = [[]]*connection_number
        self.stepper_step_schedule = [[]]*connection_number
        self.stepper_schedule_point_start = [[]]*connection_number
        self.stepper_schedule_point_end = [[]]*connection_number
        self.stepper_schedule_point_repeat = [[]]*connection_number
class ProcessedStatus():
    def __init__(self, connection_number):
        ### connection status
        self.connected_number = 0
        self.MAC_address = [0, 0]
        ### stpeer status
        self.stepper_played_pause = [None]*connection_number
        self.stepper_played_point_idx = [None]*connection_number
        self.stepper_played_schedule_idx = [None]*connection_number
        self.stepper_played_repeat_idx = [None]*connection_number


"""
def main():
    PingPongThreadInstance = PingPongThread(number=3)
    PingPongThreadInstance.start()
    PingPongThreadInstance.wait_until_full_connect()

    #PingPongThreadInstance.run_motor('all', 30)
    #PingPongThreadInstance.write(PingPongThreadInstance.SetSingleSteps_bytes(1, 20, 2000))
    #PingPongThreadInstance.write(PingPongThreadInstance.SetScheduledSteps_bytes(1, [60, -20], [2000, 1000]))
    #PingPongThreadInstance.write(PingPongThreadInstance.SetContinuousSteps_bytes(1, 20, pause=False))

    input1 = PingPongThreadInstance.SetSingleSteps_bytes(0, 1000, 1000, pause=True)
    input2 = PingPongThreadInstance.SetSingleSteps_bytes(1, 1000, 1000, pause=True)
    input3 = PingPongThreadInstance.SetSingleSteps_bytes(2, Utils().unsigned16(-1000), 1000, pause=True)
    input4 = PingPongThreadInstance.SetSingleSteps_bytes(0, -1000, 1000, pause=True)
    input5 = PingPongThreadInstance.SetSingleSteps_bytes(0xFF, 1000, 1000, pause=True)

    PingPongThreadInstance._write(PingPongThreadInstance.SetAggregateSteps_bytes(1, input1, input2, input3, input4, input5)) ### 안됨
    time.sleep(5)
    #PingPongThreadInstance._write(PingPongThreadInstance.SetPauseSteps_bytes(False, 0xFF))

    #PingPongThreadInstance.start()

    #PingPongThreadInstance.end()
    #PingPongThreadInstance.end()

    #PingPongThreadInstance = pingpongThread(2)
    #PingongThreadInstance.start()

    while True:
        #print("Thread working... (5 sec.)")
        time.sleep(10)
        #PingpongThreadInstance.disconnectMasterRobot()

if __name__ == "__main__":
    main()


"""
