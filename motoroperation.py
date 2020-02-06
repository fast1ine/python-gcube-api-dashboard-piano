#from generateprotocol import GenerateProtocol
from utils import Utils
import time, copy

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
        cube_ID_list="all", 
        speed_list=30, 
        step_list=None, 
        pause_list=False, 
        time_list=None, 
        discovery_group=None, 
        run_option="continue", 
        speed_option="RPM", 
        step_option="CYCLE", 
        sync=False, 
        time_option=None) -> None:
        """
        Run stepper motors as syncronized mode.
        speed_list: Integer, range from +- 100 to +- 1000, or 0. The unit is SPS(step per second?), or RPM(rotation per minute). 
        run_option: continue, step, schedule
        speed_option: RPM, SPS
        step_option: CYCLE, STEP
        sync: synchronous mode
        time_option: None, speed, step
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
        if cube_ID_list[0] == 0xFF:
            run_number = connection_number
        else:
            run_number = len(cube_ID_list)
        
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
        
        ### 타임 옵션 체크 함수
        def check_time_option(is_continue=False):
            nonlocal time_option
            if not is_continue:
                if time_option == None:
                    time_option = "none"
                elif not isinstance(time_option, str):
                    raise ValueError("time_option must be str or None.")
                elif time_option.lower() != "none" and time_option.lower() != "speed" and time_option.lower() != "step":
                    raise ValueError("Unknown time_option.")
            else:
                if time_option != None and time_option != "none":
                    print("In continue mode, time_option is unavailable.")

        ### 속도 제한 함수 (RPM, SPS)
        def limit_speed(speed_list_in, is_schedule=False):
            raise_error = sync and run_option != "continue" and run_number > 1 # sync 모드이고, continue 모드가 아니면 에러 체크
            ### list of list화
            if not is_schedule:
                speed_list_in = [speed_list_in]
                sleep_list = [[False]*len(speed_list_in[0])]
            else:
                sleep_list = [[False]*len(speed_list_in[x]) for x in range(len(speed_list_in))]
            ### RPM 모드
            if speed_option.upper() == "RPM":
                ### 속도 체크 & 변환
                for i in range(len(speed_list_in)):
                    for j in range(len(speed_list_in[i])):
                        if (isinstance(speed_list_in[i][j], str) and speed_list_in[i][j].lower() in ["stop", "sleep"]) or speed_list_in[i][j] == 0: # 스피드가 0이면 sleep 모드
                            speed_list_in[i][j] = 0
                            sleep_list[i][j] = True
                        Utils().float_check(speed_list_in[i][j], "stop or sleep")
                        speed_list_in[i][j] = self.GenerateProtocolInstance.truncate_RPM_speed(speed_list_in[i][j], raise_error) # speed 자르기
                        speed_list_in[i][j] = self.GenerateProtocolInstance.RPM_to_SPS(speed_list_in[i][j]) # 단위를 RPM에서 SPS로 변경
            ### SPS 모드
            elif speed_option.upper() == "SPS":
                ### 속도 체크
                for i in range(len(speed_list_in)):
                    for j in range(len(speed_list_in[i])):
                        if (isinstance(speed_list_in[i][j], str) and speed_list_in[i][j].lower() in ["stop", "sleep"]) or speed_list_in[i][j] == 0: # 스피드가 0이면 sleep 모드
                            speed_list_in[i][j] = 0
                            sleep_list[i][j] = True
                        Utils().integer_check(speed_list_in[i][j]) # SPS는 integer이어야 함.
                        speed_list_in[i][j] = self.GenerateProtocolInstance.truncate_SPS_speed(speed_list_in[i][j], raise_error) # speed 자르기
            ### 이외 옵션 오류
            else:
                raise ValueError("Unknown speed_option.")
            ### 겉 list 제거
            if not is_schedule:
                speed_list_in = speed_list_in[0]
                sleep_list = sleep_list[0]                
            return speed_list_in, sleep_list

        ### 스텝 제한 함수 (CYCLE, STEP)
        def limit_step(step_list_in, speed_list_in, sleep_list, is_schedule=False):
            raise_error = sync and run_option != "continue" and run_number > 1 # sync 모드이고, continue 모드가 아니면 에러 체크
            ### list of list화
            if not is_schedule:
                step_list_in = [step_list_in]
                speed_list_in = [speed_list_in]
                sleep_list = [sleep_list]
            ### 1줄일 때 복제
            if len(speed_list_in) == 1:
                speed_list_in = Utils().list_product_copy(speed_list_in, run_number)
                sleep_list = Utils().list_product_copy(sleep_list, run_number)
            elif len(step_list_in) == 1:
                step_list_in = Utils().list_product_copy(step_list_in, run_number)
            ### CYCLE 모드
            if step_option.upper() == "CYCLE":
                ### 사이클 체크 & 변환 
                for i in range(len(step_list_in)):
                    for j in range(len(step_list_in[i])):
                        if sleep_list[i][j]:
                            step_list_in[i][j] /= 2 # sleep이면 2로 나누고 step으로 변환하면 초 단위가 됨.
                        Utils().float_check(step_list_in[i][j])
                        if step_list_in[i][j] < 0: 
                            step_list_in[i][j] = -step_list_in[i][j] # step이 -이면 speed를 -로 바꾸기
                            speed_list_in[i][j] = -speed_list_in[i][j]
                        step_list_in[i][j] = self.GenerateProtocolInstance.truncate_cycle_step(step_list_in[i][j], raise_error) # cycle 자르기
                        step_list_in[i][j] = self.GenerateProtocolInstance.cycle_to_step(step_list_in[i][j]) # 단위를 cycle에서 step으로 변경
            ### STEP 모드
            elif step_option.upper() == "STEP":
                ### 스텝 체크 & 변환 
                for i in range(len(step_list_in)):
                    for j in range(len(step_list_in[i])):
                        Utils().integer_check(step_list_in[i][j]) # step은 integer이어야 함.
                        if step_list_in[i][j] < 0: 
                            step_list_in[i][j] = -step_list_in[i][j] # step이 -이면 speed를 -로 바꾸기
                            speed_list_in[i][j] = -speed_list_in[i][j]
                        step_list_in[i][j] = self.GenerateProtocolInstance.truncate_step_step(step_list_in[i][j], raise_error) # cycle 자르기
            ### 이외 옵션 오류
            else:
                raise ValueError("Unknown step_option.")
            ### 겉 list 제거
            if not is_schedule:
                step_list_in = step_list_in[0]
                speed_list_in = speed_list_in[0]
            return step_list_in, speed_list_in

        ### sync 체크 함수 (time_option이 none일 때 사용, limit과 확장 이후)
        def check_time_sync_none(is_schedule, speed_list_in, step_list_in):
            if sync and run_number > 1:
                ### 스텝 모드 (speed: SPS, step: STEP)
                if not is_schedule:
                    step_element_idx0 = self.GenerateProtocolInstance.step_to_cycle(step_list_in[0])
                    speed_element_idx0 = self.GenerateProtocolInstance.SPS_to_RPM(speed_list_in[0])
                    for i in range(1, len(speed_list_in)):
                        step_element_idxi = self.GenerateProtocolInstance.step_to_cycle(step_list_in[i])
                        speed_element_idxi = self.GenerateProtocolInstance.SPS_to_RPM(speed_list_in[i])
                        if abs(step_element_idx0/speed_element_idx0)-abs(step_element_idxi/speed_element_idxi) > 0.001:
                            raise ValueError("Step is not syncronous. Time offset of each step must be less than 0.001 sec.")
                ### 스케줄 모드 (speed: SPS, step: STEP)
                else:
                    # len(speed_list_in) == len(step_list_in) == run_number
                    offset_list = [0]*len(speed_list_in)
                    offset_flag = False
                    j = 0
                    while j < len(speed_list_in[0]): # len(speed_list_in[0])가 계속 변함
                        step_element_idx0j_step = step_list_in[0][j]
                        step_element_idx0j_cycle = self.GenerateProtocolInstance.step_to_cycle(step_list_in[0][j])
                        speed_element_idx0j = self.GenerateProtocolInstance.SPS_to_RPM(speed_list_in[0][j])
                        i = 1
                        while i < len(speed_list_in):
                            step_element_idxij_step = step_list_in[i][j]
                            step_element_idxij_cycle = self.GenerateProtocolInstance.step_to_cycle(step_list_in[i][j])
                            speed_element_idxij = self.GenerateProtocolInstance.SPS_to_RPM(speed_list_in[i][j])
                            if speed_element_idx0j == 0 and speed_element_idxij == 0:
                                offset = abs(step_element_idx0j_step/1000)-abs(step_element_idxij_step/1000)
                            elif speed_element_idx0j == 0:
                                offset = abs(step_element_idx0j_step/1000)-abs(step_element_idxij_cycle/speed_element_idxij)
                            elif speed_element_idxij == 0:
                                offset = abs(step_element_idx0j_cycle/speed_element_idx0j)-abs(step_element_idxij_step/1000)
                            else:
                                offset = abs(step_element_idx0j_cycle/speed_element_idx0j)-abs(step_element_idxij_cycle/speed_element_idxij)
                            if abs(offset) > 0.001:
                                raise ValueError("Schedule is not syncronous. Time offset of each schedule must be less than 0.001 sec.")
                            offset_list[i] += offset
                            if offset_list[i] > 0.001:
                                if not offset_flag:
                                    for k in range(len(speed_list_in)):
                                        speed_list_in[k].insert(j+1, 0)
                                        step_list_in[k].insert(j+1, 0)
                                    offset_flag = True
                                step_list_in[i][j+1] += 1 # 1 ms
                                offset_list[i] -= 0.001
                            elif offset_list[i] < -0.001:
                                if not offset_flag:
                                    for k in range(len(speed_list_in)):
                                        speed_list_in[k].insert(j+1, 0)
                                        step_list_in[k].insert(j+1, 1)
                                    offset_flag = True
                                step_list_in[i][j+1] -= 1 # 1 ms
                                offset_list[i] += 0.001
                            i += 1
                        if offset_flag:
                            j += 2
                        else:
                            j += 1
                        offset_flag = False
            return speed_list_in, step_list_in

        ### time_list 변환 함수
        def convert_time_list(time_list_in, is_schedule):
            ### 현재 스코프로 변수 가져오기
            nonlocal step_list
            nonlocal speed_list
            nonlocal step_option
            nonlocal speed_option
            step_list_inscope = step_list.copy()
            speed_list_inscope = speed_list.copy()
            ### list of list화
            if not is_schedule:
                time_list_in = [time_list_in]
                out_list = [[None]*run_number]
                speed_list_inscope = [speed_list_inscope]
                step_list_inscope = [step_list_inscope]
            else:
                if time_option.lower() == "speed":
                    if len(speed_list_inscope) == 1:
                        speed_list_inscope = Utils().list_product_copy(speed_list_inscope, run_number)
                    out_list = [[None]*len(speed_list_inscope[x]) for x in range(len(speed_list_inscope))] 
                elif time_option.lower() == "step":
                    if len(step_list_inscope) == 1:
                        step_list_inscope = Utils().list_product_copy(step_list_inscope, run_number)
                    out_list = [[None]*len(step_list_inscope[x]) for x in range(len(step_list_inscope))]
            if len(time_list_in) == 1:
                time_list_in = Utils().list_product_copy(time_list_in, run_number)
            if time_option.lower() == "speed": # speed 단위: SPS, time 단위: sec, speed_limit 이후
                for i in range(len(time_list_in)):
                    ### 내부 원소 길이는 이미 정리 함.
                    for j in range(len(time_list_in[i])):
                        Utils().float_check(time_list_in[i][j])
                        if time_list_in[i][j] < 0:
                            raise ValueError("Time cannot smaller than 0.")
                        ### step_list 작성, 단위는 STEP
                        if speed_list_inscope[i][j] == 0:
                            out_list[i][j] = round(time_list_in[i][j]*1000)
                            if out_list[i][j] > 65535:
                                raise ValueError("Sleep time cannot bigger than 65.535.")
                        else:
                            speed_element = self.GenerateProtocolInstance.SPS_to_RPM(speed_list_inscope[i][j])/60 # RPS
                            out_list[i][j] = abs(round(self.GenerateProtocolInstance.cycle_to_step(speed_element*time_list_in[i][j])))
                            if out_list[i][j] > 65535:
                                raise ValueError("Step cannot bigger than 65535. Maximum time is {} sec.".format(32.7675/speed_element))
                step_option = "STEP"
            elif time_option.lower() == "step": # step 단위: STEP, time 단위: sec, step_limit 이전
                ### 사이클 체크 & 변환 
                if step_option.upper() == "CYCLE":
                    raise_error = sync and run_number > 1
                    for i in range(len(step_list_inscope)):
                        for j in range(len(step_list_inscope[i])):
                            if isinstance(step_list_inscope[i][j], str) and step_list[i][j].lower() in ["stop", "sleep"]: # 스텝이 0이면 sleep 모드
                                step_list_inscope[i][j] = 0
                            else:
                                Utils().float_check(step_list_inscope[i][j])
                                step_list_inscope[i][j] = self.GenerateProtocolInstance.truncate_cycle_step(step_list_inscope[i][j], raise_error) # cycle 자르기
                                step_list_inscope[i][j] = self.GenerateProtocolInstance.cycle_to_step(step_list_inscope[i][j]) # 단위를 cycle에서 step으로 변경
                    step_option = "STEP"
                for i in range(len(time_list_in)):
                    ### 내부 원소 길이는 이미 정리 함.
                    for j in range(len(time_list_in[i])):
                        ### time 체크
                        Utils().float_check(time_list_in[i][j])
                        if time_list_in[i][j] < 0:
                            raise ValueError("Time cannot smaller than 0.")
                        ### speed_list 작성, 단위는 SPS
                        if step_list_inscope[i][j] == 0: # step이 0이면 sleep 모드
                            step_list_inscope[i][j] = round(time_list_in[i][j]*1000) # step 변경
                            if step_list_inscope[i][j] > 65535:
                                raise ValueError("Sleep time cannot bigger than 65.535 sec.")
                            out_list[i][j] = 0
                        else:
                            step_element = self.GenerateProtocolInstance.step_to_cycle(step_list_inscope[i][j]) # step to cycle
                            RPM = step_element/time_list_in[i][j]*60
                            if RPM < -30 or -3 < RPM < 3 or RPM > 30:
                                if not is_schedule:
                                    og_speed = speed_list[j]
                                else:
                                    og_speed = speed_list[i][j]
                                raise ValueError("Speed cannot bigger than +-30 RPM or smaller than +-3 RPM. Maximum time is {} sec, and minimum time is {} sec of speed {}.".format(abs(step_element*20), abs(step_element*2), og_speed))
                            out_list[i][j] = round(self.GenerateProtocolInstance.RPM_to_SPS(RPM)) # RPM to SPS
                speed_option = "SPS"
            ### 겉 list 제거
            if not is_schedule:
                out_list = out_list[0]
                step_list_inscope = step_list_inscope[0]        
            return out_list, step_list_inscope

        ### 길이 체크 함수
        def len_check(input_list, mode_name, list_name):
            if cube_ID_list[0] != 0xFF:
                if len(input_list) != 1 and len(input_list) != len(cube_ID_list):
                    raise ValueError("In {} mode, {} must have the same length as cube_ID_list, or have 1 length.".format(mode_name, list_name))
            elif len(input_list) != connection_number and len(input_list) != 1:
                raise ValueError("In {} mode with all cube IDs, {} must have the same length as connection number, or have 1 length.".format(mode_name, list_name))

        ### 바이트 확장 or 축소
        def expand_bytes(*input_list):
            nonlocal cube_ID_list
            input_list_copy = list(copy.deepcopy(input_list))
            ### 바이트 1줄
            ### speed, pause의 길이가 1이거나 원소가 모두 같은 경우, 그리고 cube ID에 전부 있거나 all인 경우
            one_byte_bool = True
            for input_list_element in input_list_copy:
                ### 길이가 1이거나 원소가 모두 같은 경우
                one_byte_bool = one_byte_bool and (len(input_list_element) == 1 or input_list_element[1:] == input_list_element[:-1])
            if one_byte_bool and (Utils().all_cube_in_check(cube_ID_list, connection_number) or cube_ID_list[0] == 0xFF):
                cube_ID_list = [0xFF]
                for i in range(len(input_list)):
                    input_list_copy[i] = [input_list[i][0]]
            ### 바이트 여러 줄
            else:
                ### all이면 모든 cube ID로 늘림
                if cube_ID_list[0] == 0xFF:
                    cube_ID_list = [i for i in range(connection_number)]
                ### 길이가 1이면 run_number 개수만큼 늘림
                for i in range(len(input_list_copy)):
                    if len(input_list_copy[i]) == 1:
                        input_list_copy[i] = input_list_copy[i]*run_number
            return input_list_copy

        ### list_of_list 체크 함수
        def check_list_of_list(input_list):
            for input_list_element in input_list:
                if not (isinstance(input_list_element, list) or isinstance(input_list_element, tuple)):
                    raise ValueError("In schedule mode, all elements of speed_list must be list or tuple.")

        ### 내부 원소 리스트 길이 체크 함수
        def len_check_elemental_list(input_list1, input_list2, mode_name, input_list1_name, input_list2_name):
            if len(input_list1) == 1:
                for input_list2_element in input_list2:
                    if len(input_list2_element) != len(input_list1[0]):
                        raise ValueError("In {} mode, each length of elements of {} and {} must be equal.".format(mode_name, input_list1_name, input_list2_name))
            elif len(input_list2) == 1:
                for input_list1_element in input_list1:
                    if len(input_list1_element) != len(input_list2[0]):
                        raise ValueError("In {} mode, each length of elements of {} and {} must be equal.".format(mode_name, input_list1_name, input_list2_name))
            else:
                for input_list1_element, input_list2_element in zip(input_list1, input_list2):
                    if len(input_list1_element) != len(input_list2_element):
                        raise ValueError("In {} mode, each length of elements of {} and {} must be equal.".format(mode_name, input_list1_name, input_list2_name))
        
        ### sync 모드 내부 원소 길이 체크
        def len_check_elemental_list_in_sync(input_list1, input_list2, mode_name, input_list1_name, input_list2_name):
            for input_list1_element in input_list1:
                if len(input_list1_element) != len(input_list1[0]):
                    raise ValueError("In {} mode, each length of elements of {} must be equal.".format(mode_name, input_list1_name))
            for input_list2_element in input_list2:
                if len(input_list2_element) != len(input_list2[0]):
                    raise ValueError("In {} mode, each length of elements of {} must be equal.".format(mode_name, input_list2_name))

        ### 옵션, 속도, 스텝, 정지 처리 & 작동
        if not isinstance(run_option, str):
            raise ValueError("run_option must be str.")
        ### 컨티뉴 모드
        elif run_option.lower() == "continue":
            ### time option 체크
            check_time_option(is_continue=True)
            ### speed, pause 길이 체크
            len_check(speed_list, "continue", "speed_list")
            len_check(speed_list, "continue", "pause_list")
            ### 속도 제한
            speed_list, _ = limit_speed(speed_list, False)
            ### 바이트 확장
            speed_list, pause_list = expand_bytes(speed_list, pause_list)
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
                ####################################### pause 했다가 다시?
            self._write_copy(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, continue_bytes))
            time.sleep(0.2)
        ### 스텝 모드
        elif run_option.lower() == "step":
            ### time option 체크
            check_time_option()
            ### time option 없음
            if time_option.lower() == "none":
                ### speed, step 길이 체크
                len_check(speed_list, "step", "speed_list")
                len_check(speed_list, "step", "pause_list")
                ### 속도, 스텝 제한
                speed_list, sleep_list = limit_speed(speed_list)
                step_list, speed_list = limit_step(step_list, speed_list, sleep_list, False)
            ### time option speed 모드
            elif time_option.lower() == "speed":
                ### time, speed 길이 체크
                len_check(time_list, "step and time-speed", "time_list")
                len_check(speed_list, "step and time-speed", "speed_list")
                ### 속도 제한
                speed_list, sleep_list = limit_speed(speed_list)
                step_list, _ = convert_time_list(time_list, False)
                step_list, speed_list = limit_step(step_list, speed_list, sleep_list, False)
            ### time option step 모드
            elif time_option.lower() == "step":
                ### time, step 길이 체크
                len_check(time_list, "step and time-step", "time_list")
                len_check(step_list, "step and time-step", "step_list")
                ### 속도 제한
                speed_list, step_list = convert_time_list(time_list, False)
                speed_list, sleep_list = limit_speed(speed_list)
                step_list, speed_list = limit_step(step_list, speed_list, sleep_list, False)
            ### pause 길이 체크
            len_check(time_list, "step", "pause_list")
            ### 바이트 확장
            speed_list, step_list, pause_list = expand_bytes(speed_list, step_list, pause_list)
            ### sync 모드 처리
            speed_list, step_list = check_time_sync_none(False, speed_list, step_list)
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
            ####################################### pause 했다가 다시?
            self._write_copy(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, step_bytes))
            time.sleep(0.2)
        ### 스케줄 모드
        elif run_option.lower() == "schedule":
            ### 타임 옵션 체크
            check_time_option()
            ### time option 없음
            if time_option.lower() == "none":
                ### speed, step이 list of list인지 체크 (dataframe, array 이용? from numpy)
                check_list_of_list(speed_list)
                check_list_of_list(step_list)
                ### speed, step 길이 체크
                len_check(speed_list, "schedule", "speed_list")
                len_check(speed_list, "schedule", "step_list")
                ### 내부 원소 길이 체크
                len_check_elemental_list(speed_list, step_list, "schedule", "speed_list", "step_list")
                ### sync 모드일 때 내부 원소 길이 체크
                if sync:
                    len_check_elemental_list_in_sync(speed_list, step_list, "schedule sync", "speed_list", "step_list")
                ### 속도, 스텝 제한
                speed_list, sleep_list = limit_speed(speed_list, True)
                step_list, speed_list = limit_step(step_list, speed_list, sleep_list, True)
            ### time option speed 모드
            elif time_option.lower() == "speed":
                ### time, speed가 list of list인지 체크 (dataframe, array 이용? from numpy)
                check_list_of_list(time_list)
                check_list_of_list(speed_list)
                ### time, speed 길이 체크
                len_check(time_list, "schedule and time-speed", "time_list")
                len_check(speed_list, "schedule and time-speed", "speed_list")
                ### 내부 원소 길이 체크
                len_check_elemental_list(speed_list, time_list, "schedule", "speed_list", "time_list")
                ### sync 모드일 때 내부 원소 길이 체크
                if sync:
                    len_check_elemental_list_in_sync(speed_list, time_list, "schedule sync", "speed_list", "time_list")
                ### 속도 제한
                speed_list, sleep_list = limit_speed(speed_list, True)
                step_list, _ = convert_time_list(time_list, True)
                step_list, speed_list = limit_step(step_list, speed_list, sleep_list, True)
            ### time option step 모드
            elif time_option.lower() == "step":
                ### time, step이 list of list인지 체크 (dataframe, array 이용? from numpy)
                check_list_of_list(time_list)
                check_list_of_list(step_list)
                ### time, step 길이 체크
                len_check(time_list, "schedule and time-step", "time_list")
                len_check(step_list, "schedule and time-step", "step_list")
                ### 내부 원소 길이 체크
                len_check_elemental_list(step_list, time_list, "schedule", "step_list", "time_list")
                ### sync 모드일 때 내부 원소 길이 체크
                if sync:
                    len_check_elemental_list_in_sync(step_list, time_list, "schedule sync", "step_list", "time_list")
                ### 속도 제한
                speed_list, step_list = convert_time_list(time_list, True)
                speed_list, sleep_list = limit_speed(speed_list, True)
                step_list, speed_list = limit_step(step_list, speed_list, sleep_list, True)    
            ### pause 길이 체크
            len_check(pause_list, "schedule", "pause_list")
            ### 바이트 확장
            speed_list, step_list, pause_list = expand_bytes(speed_list, step_list, pause_list)
            ### sync 모드 처리
            speed_list, step_list = check_time_sync_none(True, speed_list, step_list)
            ### 작동 처리 (discovery_group 처리 해야함)
            ### all인 경우 (바이트 1줄)
            if cube_ID_list[0] == 0xFF: 
                ### status 등록
                def reg_stat(x):
                    self._robot_status[discovery_group].controller_status.stepper_mode[x] = "schedule"
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[x] = [0]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[x] = [len(speed_list[0])]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[x] = [1]
                    self._robot_status[discovery_group].controller_status.stepper_speed_schedule[x] = speed_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_step_schedule[x] = step_list[0]
                    self._robot_status[discovery_group].controller_status.stepper_pause[x] = pause_list[0]
                self.GenerateProtocolInstance._if_all_function(reg_stat, None, True)
                ### 동작
                schedule_bytes = self.GenerateProtocolInstance.SetScheduledSteps_bytes(cube_ID_list[0], speed_list[0], step_list[0], discovery_group, False)
                ####################################### pause 했다가 다시?
            ### all이 아닌 경우 (바이트 여러 줄)
            else: 
                schedule_bytes = b""
                for i, cube_ID_element in enumerate(cube_ID_list):
                    ### status 등록
                    self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "schedule"
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[cube_ID_element] = [0]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[cube_ID_element] = [len(speed_list[i])]
                    self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[cube_ID_element] = [1]
                    self._robot_status[discovery_group].controller_status.stepper_speed_schedule[cube_ID_element] = speed_list[i]
                    self._robot_status[discovery_group].controller_status.stepper_step_schedule[cube_ID_element] = step_list[i]
                    self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
                    ### bytes 붙이기
                    schedule_bytes += self.GenerateProtocolInstance.SetScheduledSteps_bytes(cube_ID_element, speed_list[i], step_list[i], discovery_group, False)
            self._write_copy(self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, schedule_bytes))
            time.sleep(0.2)


    def set_motor_schedule_sync(self) -> None:
        self._start_check_copy()

        pass


    def play_motor_schedule_sync(self) -> None:
        self._start_check_copy()

        pass
    
    
