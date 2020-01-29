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
            self._robot_status[None] = RobotStatus(number, None) # 로봇 상태 저장 (dict의 key는 discovery group)
        else:
            raise ValueError("PingPong robot can connect only with 1 to 8 robots.")
        if not PingPongThread._is_instance:
            PingPongThread._is_instance = True # 인스턴스 생성 확인
            self.GenerateProtocolInstance = GenerateProtocol(number) # GenrateProtocol instance 생성
            self.PORT = Utils().find_bluetooth_dongle(self.GenerateProtocolInstance.DongleInAction_bytes()) # 동글 포트 찾기
            self._play_once_flag = True
        else:
            raise ValueError("PingpongThread instance cannot be constructed above 1.")

    def __del__(self) -> None:
        PingPongThread._is_instance = False
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
        ReaderThread.start(self)
        self._write(self.GenerateProtocolInstance.PingPongGn_connect_bytes())

    # 쓰기
    def _write(self, protocol_bytes) -> None:
        try:
            ReaderThread.write(self, protocol_bytes)
        except:
            print("Cannot write.")

    def _init_robot_status(self, discovery_group="all") -> None:
        if isinstance(discovery_group, str) and discovery_group.lower() == "all":
            for key in self._robot_status.keys():
                self._robot_status[key] = RobotStatus(self._robot_status[key].controller_status.connection_number, key)
        else:
            self._robot_status[discovery_group] = RobotStatus(self._robot_status[discovery_group].controller_status.connection_number, discovery_group)

    # 쓰레드 시작
    def start(self) -> None:
        if not PingPongThread._is_start:
            PingPongThread._is_start = True
            self._connect_robot_thread()
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
        ################################# discovery_group 처리 해야함
        def discon_op(x):
            if self._robot_status[x].processed_status.connected_number > 0:
                    self._write(self.GenerateProtocolInstance.PingPong_disconnect_bytes)
                    time.sleep(2) # 응답 기다림
                    self.set_robot_disconnect_flag(True)
                    print("Disconnect master robot.")
                    # 1개는 해제 응답을 안 받음. 2개 이상은 해제 응답을 받음.
            else:
                print("Master robot is not connected.")
            self._init_robot_status(x) # 로봇 상태 초기화

        if isinstance(discovery_group, str) and discovery_group.lower() == "all":
            for key in self._robot_status.keys():
                discon_op(key)
        else:
            discon_op(discovery_group)
        
    # deprecated?
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
        
    def get_robot_status(self, discovery_group=None) -> dict: 
        ############################################### discovery group 하면 수정
        status = \
            {
                "controller_status": self._robot_status[discovery_group].controller_status.__dict__.copy(),
                "processed_status": self._robot_status[discovery_group].processed_status.__dict__.copy()
            }
        return status

    # 완전 연결까지 기다림
    def wait_until_full_connect(self, discovery_group=None) -> None:
        ################################# discovery_group 처리
        self._start_check()
        while self._robot_status[discovery_group].controller_status.connection_number != \
        self._robot_status[discovery_group].processed_status.connected_number:
            pass
        time.sleep(1)

    # 한 번만 동작
    def play_once_full_connect(self, discovery_group=None):
        ################################# discovery_group 처리
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        connected_robots_number = self._robot_status[discovery_group].processed_status.connected_number
        if connection_number != connected_robots_number:  # full connection에서 떨어지면 리셋
            self._play_once_flag = True
            return False
        else:
            if self._play_once_flag:
                self._play_once_flag = False
                time.sleep(1)
                return True
            else:
                return False

    # RPM을 SPS로 변환
    def RPM_to_SPS(self, RPM):
        if not (isinstance(RPM, float) or isinstance(RPM, int)):
            raise ValueError("RPM must be float or int value")
        else:
            return self.GenerateProtocolInstance.RPM_to_SPS(RPM)

    # SPS를 RPM으로 변환
    def SPS_to_RPM(self, SPS):
        if not isinstance(SPS, int):
            raise ValueError("SPS must be int value")
        else:
            return self.GenerateProtocolInstance.RPM_to_SPS(SPS)

    #############################################3 모터 동작은 다른 클래스로 상속시키는 것이 보기 편할 듯 (generatemotorprocotol)
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
             raise ValueError("option must be str.")
        elif option.lower() == "continue":
            if not (len(speed_list) == 1):
                raise ValueError("In Continue mode, speed must have 1 element.")
        elif option.lower() == "step":
            if not (len(speed_list) == len(step_cycle_list) == 1):
                raise ValueError("In Step mode, speed and step_cycle must have 1 element.")
        elif option.lower() == "schedule":
            if not (len(speed_list) == len(step_cycle_list)):
                raise ValueError("In Schedule mode, speed and step must have same length.")
            elif len(speed_list) == 0 or len(step_cycle_list) == 0:
                raise ValueError("In Schedule mode, speed and step must not be empty list.")
        else:
            raise ValueError("Unknown option.")
        
        ### 일시정지 처리
        if not isinstance(pause, bool):
            raise ValueError("pause must be bool.")
        
        ### 큐브 ID 처리
        if cube_ID_list == []:
            raise ValueError("cube ID must not be empty list.")
        Utils().check_same_element(cube_ID_list) # 같은 원소가 있으면 error
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
                speed_list[i] = self.GenerateProtocolInstance.truncate_RPM_speed(speed_list[i]) # speed 자르기
                speed_list[i] = self.GenerateProtocolInstance.RPM_to_SPS(speed_list[i]) # 단위를 RPM에서 SPS로 변경

        ### 스텝 처리 (speed=0이면, step_cycle 초만큼 쉼.)
        step = [0]*len(step_cycle_list)
        if option.lower() == "step" or option.lower() == "schedule":
            for i in range(len(step_cycle_list)):
                if sleep_list[i]:
                    step_cycle_list[i] /= 2 # sleep이면 2로 나누면 초 단위가 됨.
                Utils().float_check(step_cycle_list[i], "stop")
                step_cycle_list[i] = self.GenerateProtocolInstance.truncate_cycle_step(step_cycle_list[i]) # step 자르기
                step[i] = self.GenerateProtocolInstance.cycle_to_step(step_cycle_list[i]) # 단위를 cycle에서 step으로 변경

        ### 작동 처리 (discovery_group 처리 해야함)
        ### 컨티뉴 모드
        if option.lower() == "continue": 
            if speed_list[0] == 0:
                print("Stop motor(s).")
            for cube_ID_element in cube_ID_list:
                ### status 등록
                def reg_stat(x):
                    self._robot_status[discovery_group].controller_status.stepper_mode[x] = "continue"
                    self._robot_status[discovery_group].controller_status.stepper_speed[x] = speed_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_pause[x] = pause
                self.GenerateProtocolInstance._if_all_function(reg_stat, cube_ID_element, cube_ID_element == 0xFF)
                ### 동작
                self._write(self.GenerateProtocolInstance.SetContinuousSteps_bytes(cube_ID_element, speed_list[0], discovery_group, pause))
                time.sleep(0.2)
        ### 스텝 모드
        elif option.lower() == "step": 
            for cube_ID_element in cube_ID_list:
                ### status 등록
                def reg_stat(x):
                    self._robot_status[discovery_group].controller_status.stepper_mode[x] = "step"
                    self._robot_status[discovery_group].controller_status.stepper_speed[x] = speed_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_step[x] = step[0]
                    self._robot_status[discovery_group].controller_status.stepper_pause[x] = pause
                self.GenerateProtocolInstance._if_all_function(reg_stat, cube_ID_element, cube_ID_element == 0xFF)
                ### 동작
                self._write(self.GenerateProtocolInstance.SetSingleSteps_bytes(cube_ID_element, speed_list[0], step[0], discovery_group, pause))
                time.sleep(0.2)
        ### 스케줄 모드
        elif option.lower() == "schedule": 
            for cube_ID_element in cube_ID_list:
                ### status 등록
                def reg_stat(x):
                    self._robot_status[discovery_group].controller_status.stepper_mode[x] = "point"
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[x] = [0]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[x] = [len(speed_list)]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[x] = [1]
                    self._robot_status[discovery_group].controller_status.stepper_speed_schedule[x] = speed_list
                    self._robot_status[discovery_group].controller_status.stepper_step_schedule[x] = step[0]
                    self._robot_status[discovery_group].controller_status.stepper_pause[x] = pause
                self.GenerateProtocolInstance._if_all_function(reg_stat, cube_ID_element, cube_ID_element == 0xFF)
                ### pause=True 상태로 스케줄 설정
                self._write(self.GenerateProtocolInstance.SetScheduledSteps_bytes(cube_ID_element, speed_list, step, discovery_group, True))
                time.sleep(0.2)
                #############################################확인될 때까지 잡아주는 코드 수정
                ### 포인트로 설정
                self._write(self.GenerateProtocolInstance.SetScheduledPoints_bytes(cube_ID_element, [0], [len(speed_list)], [1], discovery_group, True))
                time.sleep(0.2)
                #############################################확인될 때까지 잡아주는 코드 수정
            ### 재생
            if not pause:
                for cube_ID_element in cube_ID_list:
                    self._write(self.GenerateProtocolInstance.SetPauseSteps_bytes(False, cube_ID_element, discovery_group))
                    time.sleep(0.2)
        else:
            raise ValueError("cannot reach")
            

    # 스케줄 설정
    def set_motor_schedule(self, cube_ID, speed_list, step_cycle_list, pause=True, discovery_group=None) -> None:
        self.run_motor(cube_ID, speed_list, step_cycle_list, pause, discovery_group, "schedule")
    

    # 스케줄 실행
    def play_motor_schedule(self, cube_ID, repeat_list=1, start_point_list=None, stop_point_list=None, 
        start_and_stop_list=None, discovery_group=None, pause=False) -> None:
        """
        Play motors with set schedule.
        """
        ### start 체크
        self._start_check()

        ### start, stop, repeat 리스트화
        start_point_list = Utils().to_list(start_point_list)
        stop_point_list = Utils().to_list(stop_point_list)
        repeat_list = Utils().to_list(repeat_list)
        cube_ID_list = Utils().to_list(cube_ID)

        # 디폴트 값 넣기
        if start_point_list == [None] and stop_point_list == [None]: # 스타트, 스탑 포인트 체크
            if start_and_stop_list != None:
                start_point_list, stop_point_list = self.GenerateProtocolInstance._check_start_and_stop_list(start_and_stop_list)
            else:
                start_point_list, stop_point_list = [0], ["end"] # 디폴트 0(처음), end(끝)
        elif start_and_stop_list != None:
            print("Warning. start_point_list and stop_point_list are ignored. start_and_stop_list is accepted.")
            start_point_list, stop_point_list = self.GenerateProtocolInstance._check_start_and_stop_list(start_and_stop_list)
        elif start_point_list == [None]:
            start_point_list = [0]
        elif stop_point_list == [None]:
            stop_point_list = ["end"]

        ### 전체 반복 모드 처리 (리스트 원소가 1개면 전체 반복 모드)
        if len(repeat_list) == 1 and not len(start_point_list) == 1 and not len(stop_point_list) == 1:
            if repeat_list[0] < 0 or 255 < repeat_list[0]:
                raise ValueError("Unavailable number. Repeat must be positive, or smaller than 256.")
            print("Entire repeat mode is on. In this mode, the repeat index is not appeared properly.")
            start_point_list = start_point_list*repeat_list[0]
            stop_point_list = stop_point_list*repeat_list[0]
            repeat_list = [1]*len(start_point_list)

        ### 길이 체크
        if not len(start_point_list) == len(stop_point_list) == len(repeat_list):
            print(len(start_point_list), len(stop_point_list), len(repeat_list))
            raise ValueError("Start, stop, repeats list length must be the same.")
        elif len(start_point_list) == 0:
            raise ValueError("Start, stop, repeats list must not be empty list.")
        
        ### 일시정지 처리
        if not isinstance(pause, bool):
            raise ValueError("pause must be bool.")
        
        ### 스케줄 셋 체크 & 처리 함수
        speed_length_list = list(map(len, self._robot_status[discovery_group].controller_status.stepper_speed_schedule))
        def proc_sched(x):
            ### 스케줄 셋 체크
            if self._robot_status[discovery_group].controller_status.stepper_speed_schedule[x] == []: # 스케줄이 비었음
                raise ValueError("Set schedule before play.")
            elif self._robot_status[discovery_group].controller_status.stepper_pause[x] == False: # 이전에 play 상태로 끝남
                pass
            
            ### 스케줄 처리
            for j in range(len(start_point_list)):
                if isinstance(stop_point_list[j], str) and stop_point_list[j].lower() == "end":
                    stop_point_list[j] = speed_length_list[x]-1 # end이면 제일 뒤에 인덱스(stop은 마지막 인덱스)
                Utils().integer_check(start_point_list[j])
                Utils().integer_check(stop_point_list[j])
                Utils().integer_check(repeat_list[j])
                if start_point_list[j] < 0 or stop_point_list[j] < 0 \
                    or speed_length_list[x]-1 < start_point_list[j] \
                    or speed_length_list[x]-1 < stop_point_list[j]:
                    raise ValueError("Unavailable number. Schedule does not have that index.")
                elif stop_point_list[j] < start_point_list[j]:
                    raise ValueError("Start index must be less than or equal to stop index.")
                elif repeat_list[j] < 0 or 255 < repeat_list[j]:
                    raise ValueError("Unavailable number. Repeat must be positive, or smaller than 256.")
        
        for i in range(len(cube_ID_list)):
            cube_ID_list[i] = self.GenerateProtocolInstance._process_cube_ID(cube_ID_list[i])
            if cube_ID_list[i] == 0xFF and len(cube_ID_list) != 1:
                raise ValueError("If cube ID is all, input must not be length-above-2 list.")
        
        ### 큐브 ID, 스케줄 처리
        if cube_ID_list == []:
            raise ValueError("cube ID must not be empty list.")
        Utils().check_same_element(cube_ID_list)
        for i in range(len(cube_ID_list)):
            ### 큐브 ID 처리
            cube_ID_list[i] = self.GenerateProtocolInstance._process_cube_ID(cube_ID_list[i])
            if cube_ID_list[i] == 0xFF and len(cube_ID_list) != 1:
                raise ValueError("If cube ID is all, input must not be length-above-2 list.")
            
            ### 스케줄 처리
            self.GenerateProtocolInstance._if_all_function(proc_sched, cube_ID_list[i], cube_ID_list[i] == 0xFF)
        
        ### status 등록 함수 
        def reg_stat(x):
            self._robot_status[discovery_group].controller_status.stepper_mode[x] = "point"
            self._robot_status[discovery_group].controller_status.stepper_pause[x] = pause
            self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[x] = start_point_list
            self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[x] = stop_point_list
            self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[x] = repeat_list
            self._robot_status[discovery_group].controller_status.stepper_pause[x] = pause

        ### 작동 처리 (discovery_group 처리 해야함)
        for cube_ID_element in cube_ID_list:
            ### status 등록
            self.GenerateProtocolInstance._if_all_function(reg_stat, cube_ID_element, cube_ID_element == 0xFF)

            ### 포인트 설정
            self._write(self.GenerateProtocolInstance.SetScheduledPoints_bytes(cube_ID_element, start_point_list, stop_point_list, repeat_list, discovery_group, True, 0))
            time.sleep(0.2)
            #############################################확인될 때까지 잡아주는 코드 수정
        
        ### 작동
        for cube_ID_element in cube_ID_list:
            if not pause: # 재생
                self._write(self.GenerateProtocolInstance.SetPauseSteps_bytes(False, cube_ID_element, discovery_group))
                time.sleep(0.2)


    # 모터 일시정지
    def pause_motor(self, cube_ID=None, discovery_group=None, group_mode=False) -> None:
        self._start_check()
        cube_ID_list = Utils().to_list(cube_ID)

        #### 그룹 모드 나중에 #############################################33
        ### 큐브 ID 처리
        if cube_ID_list == []:
            raise ValueError("cube ID must not be empty list.")
        Utils().check_same_element(cube_ID_list) # 같은 원소가 있으면 error
        for i in range(len(cube_ID_list)):
            cube_ID_list[i] = self.GenerateProtocolInstance._process_cube_ID(cube_ID_list[i])
            if cube_ID_list[i] == 0xFF and len(cube_ID_list) != 1:
                raise ValueError("If cube ID is all, input must not be length-above-2 list.")

        ### 작동 처리 함수
        def proc_op(x):
            self._robot_status[discovery_group].controller_status.stepper_pause[x] = True
            ### 작동
            self._write(self.GenerateProtocolInstance.SetPauseSteps_bytes(True, x, discovery_group, group_mode))
            time.sleep(0.2)

        ### 작동 처리
        for cube_ID_element in cube_ID_list: 
            self.GenerateProtocolInstance._if_all_function(proc_op, cube_ID_element, cube_ID_element == 0xFF)

    
    # 모터 재생
    def play_paused_motor(self, cube_ID=None, discovery_group=None, group_mode=False) -> None:
        """
        Play only paused stepper/servo motor operation.
        """
        ### 시작 체크, 리스트 처리
        self._start_check()
        cube_ID_list = Utils().to_list(cube_ID)
 
        #### 그룹 모드 나중에 #############################################33
        ### 큐브 ID 처리
        if cube_ID_list == []:
            raise ValueError("cube ID must not be empty list.")
        Utils().check_same_element(cube_ID_list) # 같은 원소가 있으면 error
        for i in range(len(cube_ID_list)):
            cube_ID_list[i] = self.GenerateProtocolInstance._process_cube_ID(cube_ID_list[i])
            if cube_ID_list[i] == 0xFF and len(cube_ID_list) != 1:
                raise ValueError("If cube ID is all, input must not be length-above-2 list.")
        
        ### 작동 처리 함수
        def proc_op(x):
            if self._robot_status[discovery_group].controller_status.stepper_pause[x] == False: 
                raise ValueError("Set paused motor operation before play.")
            else:
                ### status 저장
                self._robot_status[discovery_group].controller_status.stepper_pause[x] = False
                ### 작동
                self._write(self.GenerateProtocolInstance.SetPauseSteps_bytes(False, x, discovery_group, group_mode))
                time.sleep(0.2)

        ### 작동 처리
        for cube_ID_element in cube_ID_list:
            self.GenerateProtocolInstance._if_all_function(proc_op, cube_ID_element, cube_ID_element == 0xFF)

    
    ### aggregate 모드
    def run_motor_sync(self, cube_ID_list, speed_list=None, step_list=None, pause_list=False, time_list=None, discovery_group=None, \
        run_option="continue", speed_option="RPM", step_option="STEP", time_step_mode=None) -> None:
        """
        Run stepper motors as syncronized mode.
        speed_list: Integer, range from +- 100 to +- 1000, or 0. The unit is SPS(step per second).
        """
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        if connection_number == 1: # 1개면 agg 불가능.
            raise ValueError("Sync mode cannot operate with single cube.") ###### 나중에 자동으로 고칠 것.

        ### 시작 체크
        self._start_check()

        ### cube_ID, speed, step, pause 리스트화
        cube_ID_list = Utils().to_list(cube_ID_list)
        speed_list = Utils().to_list(speed_list)
        step_list = Utils().to_list(step_list)
        pause_list = Utils().to_list(pause_list)

        ### 큐브 ID 처리
        if cube_ID_list == [] or pause_list == ():
            raise ValueError("cube ID must not be empty list.")
        Utils().check_same_element(cube_ID_list) # 같은 원소가 있으면 error
        for i in range(len(cube_ID_list)):
            cube_ID_list[i] = self.GenerateProtocolInstance._process_cube_ID(cube_ID_list[i])
            if cube_ID_list[i] == 0xFF and len(cube_ID_list) != 1:
                raise ValueError("If cube ID is all, input must not be length-above-2 list.")

        ### 일시정지 체크, 처리
        if pause_list == [] or pause_list == ():
            raise ValueError("pause_list must not be empty list.")
        for pause in pause_list:
            if not isinstance(pause, bool):
                raise ValueError("pause_list elements must be bool.")
        
        ### 속도 제한 함수 (SPS)
        def limit_speed(is_schedule=False):
            if not is_schedule:
                for speed_element in speed_list:
                    Utils().integer_check(speed_element) # SPS는 정수값
                    if speed_element < -1000 or speed_element > 1000: 
                        raise ValueError("Speed must be between +- 100 to +-1000, or 0.")
                    elif -100 < speed_element and speed_element < 100 and speed_element != 0:
                        raise ValueError("Speed must be between +- 100 to +-1000, or 0")
            else:
                for speed_element in speed_list:
                    for speed_element_element in speed_element:
                        Utils().integer_check(speed_element_element) # SPS는 정수값
                        if speed_element_element < -1000 or speed_element_element > 1000: 
                            raise ValueError("Speed must be between +- 100 to +-1000, or 0.")
                        elif -100 < speed_element_element and speed_element_element < 100 and speed_element_element != 0:
                            raise ValueError("Speed must be between +- 100 to +-1000, or 0")

        ### 스텝 제한 함수 (STEP)
        def limit_step(is_schedule=False):
            if not is_schedule:
                for step_element in step_list:
                    Utils().integer_check(step_element) # Step은 정수값
                    if step_element < 0 or 65535 < step_element:
                        raise ValueError("Step must be between 0 to 65535.")
            else:
                for step_element in step_list:
                    for step_element_element in step_element:
                        Utils().integer_check(step_element_element) # Step은 정수값
                        if step_element_element < 0 or 65535 < step_element_element:
                            raise ValueError("Step must be between 0 to 65535.")
                    
        ### 옵션 체크 & 속도, 스텝, 정지 처리
        check_all_in = Utils().all_cube_in_check(cube_ID_list, connection_number)
        if not isinstance(run_option, str):
            raise ValueError("run_option must be str.")
        ### 컨티뉴 모드
        elif run_option.lower() == "continue":
            ### speed, pause 길이 체크
            if not (len(speed_list) == 1 or len(speed_list) == len(cube_ID_list) \
                or (cube_ID_list[0] == 0xFF and len(speed_list) == connection_number)):
                raise ValueError("In continue mode, speed_list must have same length as cube_ID_list, or have 1 length.")
            if not (len(pause_list) == 1 or len(pause_list) == len(cube_ID_list) \
                or (cube_ID_list[0] == 0xFF and len(pause_list) == connection_number)):
                raise ValueError("In continue mode, pause_list must have same length as cube_ID_list, or have 1 length.")
            ### 바이트 1줄
            ### speed, pause의 길이가 1이거나 원소가 모두 같은 경우, 그리고 cube ID에 전부 있거나 all인 경우
            if (len(speed_list) == 1 or speed_list[1:] == speed_list[:-1]) and \
                (len(pause_list) == 1 or pause_list[1:] == pause_list[:-1]) and \
                (check_all_in or cube_ID_list[0] == 0xFF):
                cube_ID_list = [0xFF]
                speed_list = [speed_list[0]]
                pause_list = [pause_list[0]]
            ### 바이트 여러 줄
            if not (cube_ID_list[0] == 0xFF and len(speed_list) == 1 and len(pause_list) == 1):
                ### all이면 모든 cube ID로 늘림
                if cube_ID_list[0] == 0xFF:
                    cube_ID_list = [i for i in range(connection_number)]
                ### speed 길이가 1이면 cube ID 개수만큼 늘림
                if len(speed_list) == 1:
                    speed_list = speed_list*len(cube_ID_list)
                ### pause 길이가 1이면 cube ID 개수만큼 늘림
                if len(pause_list) == 1:
                    pause_list = pause_list*len(cube_ID_list)
            ### 속도 제한
            limit_speed()
            ### 작동 처리 (discovery_group 처리 해야함)
            ### all인 경우 (바이트 1줄)
            if cube_ID_list[0] == 0xFF: 
                ### 모터 정지
                if speed_list[0] == 0: 
                    print("Stop all motors.")
                ### status 등록
                def reg_stat(x):
                    self._robot_status[discovery_group].controller_status.stepper_mode[x] = "continue"
                    self._robot_status[discovery_group].controller_status.stepper_speed[x] = speed_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_pause[x] = pause_list[0]
                self.GenerateProtocolInstance._if_all_function(reg_stat, None, True)
                ### 동작
                continue_bytes = self.GenerateProtocolInstance.SetContinuousSteps_bytes(cube_ID_list[0], speed_list[0], discovery_group, pause_list[0])
                ####################################### pause 했다가 다시?
                self._write(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, continue_bytes))
            ### all이 아닌 경우 (바이트 여러 줄)
            else: 
                continue_bytes = b""
                for i, cube_ID_element in enumerate(cube_ID_list):
                    ### status 등록
                    self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "continue"
                    self._robot_status[discovery_group].controller_status.stepper_speed[cube_ID_element] = speed_list[i]
                    self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
                    ### bytes 붙이기
                    continue_bytes += self.GenerateProtocolInstance.SetContinuousSteps_bytes(cube_ID_element, speed_list[i], discovery_group, pause_list[i])
                self._write(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, continue_bytes))
            time.sleep(0.2)
        ### 스텝 모드
        elif run_option.lower() == "step":
            ### speed, step, pause 길이 체크
            if not (len(speed_list) == 1 or len(speed_list) == len(cube_ID_list) \
                or (cube_ID_list[0] == 0xFF and len(speed_list) == connection_number)):
                raise ValueError("In step mode, speed_list must have same length as cube_ID_list, or have 1 length.")
            if not (len(step_list) == 1 or len(step_list) == len(cube_ID_list) \
                or (cube_ID_list[0] == 0xFF and len(step_list) == connection_number)):
                raise ValueError("In step mode, step_list must have same length as cube_ID_list, or have 1 length.")
            if not (len(pause_list) == 1 or len(pause_list) == len(cube_ID_list) \
                or (cube_ID_list[0] == 0xFF and len(pause_list) == connection_number)):
                raise ValueError("In step mode, pause_list must have same length as cube_ID_list, or have 1 length.")
            ### 바이트 1줄
            ### speed, step, pause의 길이가 1이거나 원소가 모두 같은 경우, 그리고 cube ID에 전부 있거나 all인 경우
            if (len(speed_list) == 1 or speed_list[1:] == speed_list[:-1]) and \
                (len(pause_list) == 1 or pause_list[1:] == pause_list[:-1]) and \
                (len(step_list) == 1 or step_list[1:] == step_list[:-1]) and \
                (check_all_in or cube_ID_list[0] == 0xFF):
                cube_ID_list = [0xFF]
                speed_list = [speed_list[0]]
                step_list = [step_list[0]]
                pause_list = [pause_list[0]]
            ### 바이트 여러 줄
            if not (cube_ID_list[0] == 0xFF and len(speed_list) == 1 and len(step_list) and len(pause_list) == 1):
                ### all이면 모든 cube ID로 늘림
                if cube_ID_list[0] == 0xFF:
                    cube_ID_list = [i for i in range(connection_number)]
                ### speed 길이가 1이면 cube ID 개수만큼 늘림
                if len(speed_list) == 1:
                    speed_list = speed_list*len(cube_ID_list)
                ### step 길이가 1이면 cube ID 개수만큼 늘림
                if len(step_list) == 1:
                    step_list = step_list*len(cube_ID_list)
                ### pause 길이가 1이면 cube ID 개수만큼 늘림
                if len(pause_list) == 1:
                    pause_list = pause_list*len(cube_ID_list)
            ### 속도, 스텝 제한
            limit_speed()
            limit_step()
            ### 작동 처리 (discovery_group 처리 해야함)
            ### all인 경우 (바이트 1줄)
            if cube_ID_list[0] == 0xFF: 
                ### status 등록
                def reg_stat(x):
                    self._robot_status[discovery_group].controller_status.stepper_mode[x] = "step"
                    self._robot_status[discovery_group].controller_status.stepper_speed[x] = speed_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_step[x] = step_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_pause[x] = pause_list[0]
                self.GenerateProtocolInstance._if_all_function(reg_stat, None, True)
                ### 동작
                step_bytes = self.GenerateProtocolInstance.SetSingleSteps_bytes(cube_ID_list[0], speed_list[0], step_list[0], discovery_group, pause_list[0])
                ####################################### pause 했다가 다시?
                self._write(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, step_bytes))
            ### all이 아닌 경우 (바이트 여러 줄)
            else: 
                step_bytes = b""
                for i, cube_ID_element in enumerate(cube_ID_list):
                    ### status 등록
                    self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "step"
                    self._robot_status[discovery_group].controller_status.stepper_speed[cube_ID_element] = speed_list[i]
                    self._robot_status[discovery_group].controller_status.stepper_step[cube_ID_element] = step_list[i]
                    self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
                    ### bytes 붙이기
                    step_bytes += self.GenerateProtocolInstance.SetSingleSteps_bytes(cube_ID_element, speed_list[i], step_list[i], discovery_group, pause_list[i])
                self._write(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, step_bytes))
            time.sleep(0.2)
        ### 스케줄 모드
        elif run_option.lower() == "schedule":
            ### speed, step이 list of list인지 체크 (dataframe, array 이용? from numpy)
            for speed_element in speed_list:
                if not (isinstance(speed_element, list) or isinstance(speed_element, tuple)):
                    raise ValueError("In schedule mode, all elements of speed_list must be list or tuple.")
            for step_element in step_list:
                if not (isinstance(step_element, list) or isinstance(step_element, tuple)):
                    raise ValueError("In schedule mode, all elements of step_list must be list or tuple.")
            ### speed, pause 길이 체크
            if not (len(speed_list) == 1 or len(speed_list) == len(cube_ID_list) \
                or (cube_ID_list[0] == 0xFF and len(speed_list) == connection_number)):
                raise ValueError("In Continue mode, speed_list must have same length as cube_ID_list, or have 1 length.")
            if not (len(pause_list) == 1 or len(pause_list) == len(cube_ID_list) \
                or (cube_ID_list[0] == 0xFF and len(pause_list) == connection_number)):
                raise ValueError("In Continue mode, pause_list must have same length as cube_ID_list, or have 1 length.")

            ####################################### 내부 원소 길이 체크
            

            ### 바이트 1줄
            ### speed, step, pause의 길이가 1이거나 원소가 모두 같은 경우, 그리고 cube ID에 전부 있거나 all인 경우
            if (len(speed_list) == 1 or speed_list[1:] == speed_list[:-1]) and \
                (len(pause_list) == 1 or pause_list[1:] == pause_list[:-1]) and \
                (len(step_list) == 1 or step_list[1:] == step_list[:-1]) and \
                (check_all_in or cube_ID_list[0] == 0xFF):
                cube_ID_list = [0xFF]
                speed_list = [speed_list[0]]
                step_list = [step_list[0]]
                pause_list = [pause_list[0]]
            ### 바이트 여러 줄
            if not (cube_ID_list[0] == 0xFF and len(speed_list) == 1 and len(step_list) and len(pause_list) == 1):
                ### all이면 모든 cube ID로 늘림
                if cube_ID_list[0] == 0xFF:
                    cube_ID_list = [i for i in range(connection_number)]
                ### speed 길이가 1이면 cube ID 개수만큼 늘림
                if len(speed_list) == 1:
                    speed_list = speed_list*len(cube_ID_list)
                ### step 길이가 1이면 cube ID 개수만큼 늘림
                if len(step_list) == 1:
                    step_list = step_list*len(cube_ID_list)
                ### pause 길이가 1이면 cube ID 개수만큼 늘림
                if len(pause_list) == 1:
                    pause_list = pause_list*len(cube_ID_list)
            ### 속도, 스텝 제한
            limit_speed(True)
            limit_step(True)
            ### 작동 처리 (discovery_group 처리 해야함)
            ### all인 경우 (바이트 1줄)
            if cube_ID_list[0] == 0xFF: 
                ### status 등록
                def reg_stat(x):
                    self._robot_status[discovery_group].controller_status.stepper_mode[x] = "schedule"
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[x] = [0]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[x] = [len(speed_list)]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[x] = [1]
                    self._robot_status[discovery_group].controller_status.stepper_speed_schedule[x] = speed_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_step_schedule[x] = step_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_pause[x] = pause_list[0]
                self.GenerateProtocolInstance._if_all_function(reg_stat, None, True)
                ### 동작
                schedule_bytes = self.GenerateProtocolInstance.SetScheduledSteps_bytes(cube_ID_list[0], speed_list[0], step_list[0], discovery_group, False)
                ####################################### pause 했다가 다시?
                self._write(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, schedule_bytes))
            ### all이 아닌 경우 (바이트 여러 줄)
            else: 
                step_bytes = b""
                for i, cube_ID_element in enumerate(cube_ID_list):
                    ### status 등록
                    self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "schedule"
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[cube_ID_element] = [0]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[cube_ID_element] = [len(speed_list)]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[cube_ID_element] = [1]
                    self._robot_status[discovery_group].controller_status.stepper_speed_schedule[cube_ID_element] = speed_list[i]
                    self._robot_status[discovery_group].controller_status.stepper_step_schedule[cube_ID_element] = step_list[i]
                    self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
                    ### bytes 붙이기
                    step_bytes += self.GenerateProtocolInstance.SetScheduledSteps_bytes(cube_ID_element, speed_list[i], step_list[i], discovery_group, False)
                self._write(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, step_bytes))
            time.sleep(0.2)
        ### 이외 옵션 오류
        else:
            raise ValueError("Unknown run_option.")


    def set_motor_schedule_sync(self) -> None:
        pass


    def play_motor_schedule_sync(self) -> None:
        pass
    

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
        self.MAC_address = [None]*2
        ### stepper status
        self.stepper_schedule_set = [None]*connection_number
        self.stepper_point_set = [None]*connection_number
        self.stepper_played_pause = [None]*connection_number
        self.stepper_played_schedule_idx = [None]*connection_number
        self.stepper_played_point_idx = [None]*connection_number
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
