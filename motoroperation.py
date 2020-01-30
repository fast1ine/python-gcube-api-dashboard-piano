#from generateprotocol import GenerateProtocol
from utils import Utils
import time

class MotorOperation():
    def __init__(self, GenerateProtocolInstance, _robot_status, _start_check, _write):
        self.GenerateProtocolInstance = GenerateProtocolInstance
        self._robot_status = _robot_status
        self._start_check_copy = _start_check
        self._write_copy = _write

    
    # 모터 동작 (deprecated)
    def run_motor_prev(self, cube_ID, speed, step_cycle=None, pause=False, discovery_group=None, option="continue") -> None:
        ### start 체크
        self._start_check_copy()

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
                self._write_copy(self.GenerateProtocolInstance.SetContinuousSteps_bytes(cube_ID_element, speed_list[0], discovery_group, pause))
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
                self._write_copy(self.GenerateProtocolInstance.SetSingleSteps_bytes(cube_ID_element, speed_list[0], step[0], discovery_group, pause))
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
                self._write_copy(self.GenerateProtocolInstance.SetScheduledSteps_bytes(cube_ID_element, speed_list, step, discovery_group, True))
                time.sleep(0.2)
                #############################################확인될 때까지 잡아주는 코드 수정
                ### 포인트로 설정
                self._write_copy(self.GenerateProtocolInstance.SetScheduledPoints_bytes(cube_ID_element, [0], [len(speed_list)], [1], discovery_group, True))
                time.sleep(0.2)
                #############################################확인될 때까지 잡아주는 코드 수정
            ### 재생
            if not pause:
                for cube_ID_element in cube_ID_list:
                    self._write_copy(self.GenerateProtocolInstance.SetPauseSteps_bytes(False, cube_ID_element, discovery_group))
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
        self._start_check_copy()

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
            self._write_copy(self.GenerateProtocolInstance.SetScheduledPoints_bytes(cube_ID_element, start_point_list, stop_point_list, repeat_list, discovery_group, True, 0))
            time.sleep(0.2)
            #############################################확인될 때까지 잡아주는 코드 수정
        
        ### 작동
        for cube_ID_element in cube_ID_list:
            if not pause: # 재생
                self._write_copy(self.GenerateProtocolInstance.SetPauseSteps_bytes(False, cube_ID_element, discovery_group))
                time.sleep(0.2)


    # 모터 일시정지
    def pause_motor(self, cube_ID=None, discovery_group=None, group_mode=False) -> None:
        self._start_check_copy()
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
            self._write_copy(self.GenerateProtocolInstance.SetPauseSteps_bytes(True, x, discovery_group, group_mode))
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
        self._start_check_copy()
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
                self._write_copy(self.GenerateProtocolInstance.SetPauseSteps_bytes(False, x, discovery_group, group_mode))
                time.sleep(0.2)

        ### 작동 처리
        for cube_ID_element in cube_ID_list:
            self.GenerateProtocolInstance._if_all_function(proc_op, cube_ID_element, cube_ID_element == 0xFF)

    
    ### aggregate 모드
    def run_motor(self, 
        cube_ID_list, 
        speed_list=None, 
        step_list=None, 
        pause_list=False, 
        time_list=None, 
        discovery_group=None, 
        run_option="continue", 
        speed_option="RPM", 
        step_option="CYCLE", 
        sync=False, 
        time_step_mode=None) -> None:
        """
        Run stepper motors as syncronized mode.
        speed_list: Integer, range from +- 100 to +- 1000, or 0. The unit is SPS(step per second).
        """
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        if connection_number == 1: # 1개면 agg 불가능.
            raise ValueError("Sync mode cannot operate with single cube.") ###### 나중에 자동으로 고칠 것.

        ### 시작 체크
        self._start_check_copy()

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

        ### 일시정지 체크
        if pause_list == [] or pause_list == ():
            raise ValueError("pause_list must not be empty list (or tuple).")
        for pause in pause_list:
            if not isinstance(pause, bool):
                raise ValueError("pause_list elements must be bool.")
        
        ### 스피드, 스텝 옵션 체크
        if not isinstance(speed_option, str):
            raise ValueError("speed_option must be str.")
        if not isinstance(step_option, str):
            raise ValueError("step_option must be str.")

        ### 싱크 체크
        if not isinstance(sync, bool):
            raise ValueError("sync must be bool.")

        ### 속도 제한 함수 (RPM, SPS)
        def limit_speed(speed_list, is_schedule=False):
            ### RPM, SPS 모드 설정
            ### RPM 모드
            if speed_option.upper() == "RPM":
                ### list of list화
                if not is_schedule:
                    speed_list = [speed_list]
                    sleep_list = [[False]*len(speed_list)]
                else:
                    sleep_list = [[False]*len(speed_list[x]) for x in range(len(speed_list))]
                ### 속도 체크 & 변환
                for i in range(len(speed_list)):
                    for j in range(len(speed_list[i])):
                        if (isinstance(speed_list[i][j], str) and speed_list[i][j].lower() in ["stop", "sleep"]) or speed_list[i][j] == 0: # 스피드가 0이면 sleep 모드
                            speed_list[i][j] = 0
                            sleep_list[i][j] = True
                        Utils().float_check(speed_list[i][j], "stop or sleep")
                        speed_list[i][j] = self.GenerateProtocolInstance.truncate_RPM_speed(speed_list[i][j], sync) # speed 자르기
                        speed_list[i][j] = self.GenerateProtocolInstance.RPM_to_SPS(speed_list[i][j]) # 단위를 RPM에서 SPS로 변경
                ### 겉 list 제거
                if not is_schedule:
                    speed_list = speed_list[0]
                    sleep_list = sleep_list[0]                
                return speed_list, sleep_list
            ### SPS 모드
            elif speed_option.upper() == "SPS":
                ### list of list화
                if not is_schedule:
                    speed_list = [speed_list]
                ### 속도 체크
                for i in range(len(speed_list)):
                    for j in range(len(speed_list[i][j])):
                        Utils().integer_check(speed_list[i][j]) # SPS는 int
                        speed_list[i][j] = self.GenerateProtocolInstance.truncate_SPS_speed(speed_list[i][j], sync) # speed 자르기
                ### 겉 list 제거
                if not is_schedule:
                    speed_list = speed_list[0]
                return speed_list
            else:
                raise ValueError("Unknown speed_option.")

        ### 스텝 제한 함수 (CYCLE, STEP)
        def limit_step(step_list, sleep_list=None, is_schedule=False):
            if step_option.upper() == "CYCLE":
                pass
            elif step_option.upper() == "STEP":
                pass
            else:
                raise ValueError("Unknown step_option.")

            ##############################################






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
        


        ### 스텝 처리 (speed=0이면, step_cycle 초만큼 쉼.)
        step = [0]*len(step_cycle_list)
        if option.lower() == "step" or option.lower() == "schedule":
            for i in range(len(step_cycle_list)):
                if sleep_list[i]:
                    step_cycle_list[i] /= 2 # sleep이면 2로 나누면 초 단위가 됨.
                Utils().float_check(step_cycle_list[i], "stop")
                step_cycle_list[i] = self.GenerateProtocolInstance.truncate_cycle_step(step_cycle_list[i]) # step 자르기
                step[i] = self.GenerateProtocolInstance.cycle_to_step(step_cycle_list[i]) # 단위를 cycle에서 step으로 변경









        ### 옵션, 속도, 스텝, 정지 처리 & 작동
        check_all_in = Utils().all_cube_in_check(cube_ID_list, connection_number)
        ### 컨티뉴 모드
        if not isinstance(run_option, str):
            raise ValueError("run_option must be str.")
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
                self._write_copy(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, continue_bytes))
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
                self._write_copy(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, continue_bytes))
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
                self._write_copy(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, step_bytes))
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
                self._write_copy(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, step_bytes))
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
                self._write_copy(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, schedule_bytes))
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
                self._write_copy(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, step_bytes))
            time.sleep(0.2)
        ### 이외 옵션 오류 (cannot reach)
        else:
            raise ValueError("Unknown run_option.")


    def set_motor_schedule_sync(self) -> None:
        self._start_check_copy()

        pass


    def play_motor_schedule_sync(self) -> None:
        self._start_check_copy()

        pass
    
    
