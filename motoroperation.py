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
        if cube_ID_list == [] or cube_ID_list == ():
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
                ### 포인트로 설정
                self._write_copy(self.GenerateProtocolInstance.SetScheduledPoints_bytes(cube_ID_element, [0], [len(speed_list)], [1], discovery_group, True))
                time.sleep(0.2)
            ### 재생
            if not pause:
                for cube_ID_element in cube_ID_list:
                    self._write_copy(self.GenerateProtocolInstance.SetPauseSteps_bytes(False, cube_ID_element, discovery_group))
                    time.sleep(0.2)
        else:
            raise ValueError("cannot reach")
        
    # 모터 일시정지
    def pause_motor(self, cube_ID=None, discovery_group=None, group_mode=False) -> None:
        self._start_check_copy()
        cube_ID_list = Utils().to_list(cube_ID)

        #### 그룹 모드 나중에 #############################################33
        ### 큐브 ID 처리
        if cube_ID_list == [] or cube_ID_list == ():
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
        speed_list=None, 
        step_list=None, 
        pause_list=False, 
        time_list=None, 
        discovery_group=None, 
        run_option="continue", 
        speed_option="RPM", 
        step_option="CYCLE", 
        sync=False, 
        time_option=None,
        wait=0) -> None:
        """
        Run stepper motors as syncronized mode.
        speed_list: Integer, range from +- 100 to +- 1000, or 0. The unit is SPS(step per second?), or RPM(rotation per minute). 
        run_option: \"continue\", \"step\", \"schedule\"
        speed_option: \"RPM\", \"SPS\"
        step_option: \"CYCLE\", \"STEP\"
        sync: synchronous mode, True or False
        time_option: None, \"speed\", \"step\"
        wait: time(sec), \"step\", \"schedule\"
        """
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number

        ### 시작 체크
        self._start_check_copy()

        ### cube_ID, speed, step, pause 리스트화
        cube_ID_list = Utils().to_list(cube_ID_list)
        speed_list = Utils().to_list(speed_list)
        step_list = Utils().to_list(step_list)
        pause_list = Utils().to_list(pause_list)

        ### 큐브 ID 처리
        if cube_ID_list == [] or cube_ID_list == ():
            raise ValueError("cube ID must not be empty list.")
        for i in range(len(cube_ID_list)):
            cube_ID_list[i] = self.GenerateProtocolInstance._process_cube_ID(cube_ID_list[i])
            if cube_ID_list[i] == 0xFF and len(cube_ID_list) != 1:
                raise ValueError("If cube ID is all, input must not be length-above-2 list.")
        Utils().check_same_element(cube_ID_list) # 같은 원소가 있으면 error
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

        ### wait 체크
        if not isinstance(wait, int) and not isinstance(wait, float) and not isinstance(wait, str):
            raise ValueError("wait must be int, float, or str.")
        elif (isinstance(wait, int) or isinstance(wait, float)) and wait < 0:
            raise ValueError("wait must be positive.")
        elif isinstance(wait, str) and wait.lower() != "step" and wait.lower() != "schedule":
            raise ValueError("Unknown wait option.")

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
                        if not is_schedule and (isinstance(speed_list_in[i][j], list) or isinstance(speed_list_in[i][j], tuple)):
                            raise ValueError("In {} mode, elements of lists cannot be list or tuple.".format(run_option.lower()))
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
                        speed_list_in[i][j] = round(speed_list_in[i][j])
                        Utils().float_check(speed_list_in[i][j])
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
            len_changed = False
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
                                len_changed = True
                                if not offset_flag:
                                    for k in range(len(speed_list_in)):
                                        speed_list_in[k].insert(j+1, 0)
                                        step_list_in[k].insert(j+1, 0)
                                    offset_flag = True
                                step_list_in[i][j+1] += 1 # 1 ms
                                offset_list[i] -= 0.001
                            elif offset_list[i] < -0.001:
                                len_changed = True
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
            if len_changed:
                print("Warning. speed_list and step list length have changed due to time offset.")
                print("speed_list(in SPS):", speed_list_in)
                print("step_list(in STEP):", step_list_in)
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
            error_str = "In {} mode, each length of elements of {} and {} must be equal.".format(mode_name, input_list1_name, input_list2_name)
            if len(input_list1) == 1:
                for input_list2_element in input_list2:
                    if len(input_list2_element) != len(input_list1[0]):
                        raise ValueError(error_str)
            elif len(input_list2) == 1:
                for input_list1_element in input_list1:
                    if len(input_list1_element) != len(input_list2[0]):
                        raise ValueError(error_str)
            else:
                for input_list1_element, input_list2_element in zip(input_list1, input_list2):
                    if len(input_list1_element) != len(input_list2_element):
                        raise ValueError(error_str)
        
        ### sync 모드 내부 원소 길이 체크 함수
        def len_check_elemental_list_in_sync(input_list1, input_list2, mode_name, input_list1_name, input_list2_name):
            error_str = "In {} mode, each length of elements of {} must be equal."
            for input_list1_element in input_list1:
                if len(input_list1_element) != len(input_list1[0]):
                    raise ValueError(error_str.format(mode_name, input_list1_name))
            for input_list2_element in input_list2:
                if len(input_list2_element) != len(input_list2[0]):
                    raise ValueError(error_str.format(mode_name, input_list2_name))

        ### wait 처리 함수
        def convert_wait(is_schedule):
            # wait = "step" 또는 "schedule"이면 현재 run_option에 맞춰서 알아서 계산
            def cal_time(speed_element, step_element):
                if speed_element == 0:
                    new_time_out = step_element/1000
                else:
                    speed_element = self.GenerateProtocolInstance.SPS_to_RPM(speed_element)/60 # RPS
                    step_element = self.GenerateProtocolInstance.step_to_cycle(step_element)
                    new_time_out = abs(step_element/speed_element)
                return new_time_out
            # speed: SPS, step: STEP
            max_time = 0
            if not is_schedule:
                for i, (speed_element, step_element) in enumerate(zip(speed_list, step_list)):
                    if pause_list[i]: # pause이면 wait 무시
                        new_time = 0
                    else:
                        new_time = cal_time(speed_element, step_element)
                    if new_time > max_time:
                        max_time = new_time
            else:
                for i in range(len(speed_list)):
                    if pause_list[i]: # pause이면 wait 무시
                        new_time = 0
                    else:
                        new_time = 0
                        for (speed_element, step_element) in zip(speed_list[i], step_list[i]):
                            new_time += cal_time(speed_element, step_element)
                    if new_time > max_time:
                        max_time = new_time
            return max_time
            
        ### step 디폴트 처리 함수
        def set_default():
            nonlocal speed_list
            nonlocal step_list
            if speed_list == [None]:
                if run_option.lower() == "step" and speed_option.upper() == "RPM":
                    speed_list = [30]
                elif run_option.lower() == "step" and speed_option.upper() == "SPS":
                    speed_list = [1000]
            if step_list == [None]:
                if run_option.lower() == "step" and step_option.upper() == "CYCLE":
                    step_list = [1]
                elif run_option.lower() == "step" and step_option.upper() == "STEP":
                    step_list = [2000]

        ### 옵션, 속도, 스텝, 정지 처리 & 작동
        if not isinstance(run_option, str):
            raise ValueError("run_option must be str.")
        ### 컨티뉴 모드
        elif run_option.lower() == "continue":
            ### 디폴트 체크
            set_default()
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
            sending_bytes = b""
            for i, cube_ID_element in enumerate(cube_ID_list):
                if speed_list[i] == 0:
                    pause_list[i] = True # 0일 때 pause로 안 보내면 다음 명령어가 안 먹음
                ### status 등록
                self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "continue"
                self._robot_status[discovery_group].controller_status.stepper_speed[cube_ID_element] = speed_list[i]
                self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
                ### bytes 붙이기
                sending_bytes += self.GenerateProtocolInstance.SetContinuousSteps_bytes(cube_ID_element, speed_list[i], discovery_group, pause_list[i])
            if connection_number > 1:
                sending_bytes = self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, sending_bytes)
        ### 스텝 모드
        elif run_option.lower() == "step":
            ### 디폴트 체크
            set_default()
            ### time option 체크
            check_time_option()
            ### time option 없음
            if time_option.lower() == "none":
                ### speed, step 길이 체크
                len_check(speed_list, "step", "speed_list")
                len_check(step_list, "step", "pause_list")
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
            len_check(pause_list, "step", "pause_list")
            ### 바이트 확장
            speed_list, step_list, pause_list = expand_bytes(speed_list, step_list, pause_list)
            ### sync 모드 처리
            speed_list, step_list = check_time_sync_none(False, speed_list, step_list)
            ### wait 처리
            if not isinstance(wait, int) and not isinstance(wait, float):
                wait = convert_wait(False)
            ### 작동 처리 (discovery_group 처리 해야함)
            sending_bytes = b""
            for i, cube_ID_element in enumerate(cube_ID_list):
                ### status 등록
                self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "step"
                self._robot_status[discovery_group].controller_status.stepper_speed[cube_ID_element] = speed_list[i]
                self._robot_status[discovery_group].controller_status.stepper_step[cube_ID_element] = step_list[i]
                self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
                ### bytes 붙이기
                sending_bytes += self.GenerateProtocolInstance.SetSingleSteps_bytes(cube_ID_element, speed_list[i], step_list[i], discovery_group, pause_list[i])
            if connection_number > 1:
                sending_bytes = self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, sending_bytes)
        ### 스케줄 모드
        elif run_option.lower() == "schedule":
            ### 타임 옵션 체크
            check_time_option()
            ### time option 없음
            if time_option.lower() == "none":
                ### 디폴트 체크
                if speed_list == [None] or step_list == [None]:
                    raise ValueError("In schedule mode, speed and step must be entered.")
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
                ### 디폴트 체크
                if time_list == [None] or speed_list == [None]:
                    raise ValueError("In schedule and time-speed mode, time and speed must be entered.")
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
                ### 디폴트 체크
                if time_list == [None] or step_list == [None]:
                    raise ValueError("In schedule and time-step mode, time and step must be entered.")
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
            ### wait 처리
            if not isinstance(wait, int) and not isinstance(wait, float):
                wait = convert_wait(True)
            ### 작동 처리 (discovery_group 처리 해야함)
            sending_bytes = b""
            for i, cube_ID_element in enumerate(cube_ID_list):
                ### status 등록
                self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "schedule"
                self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[cube_ID_element] = [0]
                self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[cube_ID_element] = [len(speed_list[i])]
                self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[cube_ID_element] = [1]
                self._robot_status[discovery_group].controller_status.stepper_speed_schedule[cube_ID_element] = speed_list[i]
                self._robot_status[discovery_group].controller_status.stepper_step_schedule[cube_ID_element] = step_list[i]
                self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
                self._robot_status[discovery_group].controller_status.stepper_schedule_sync_on[cube_ID_element] = sync
                ### bytes 붙이기
                sending_bytes += self.GenerateProtocolInstance.SetScheduledSteps_bytes(cube_ID_element, speed_list[i], step_list[i], discovery_group, True)
            if connection_number > 1:
                sending_bytes = self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, sending_bytes)
        ### 스케줄 보내기
        self._write_copy(sending_bytes) 
        ### agg 설정이 올 때까지 잡아두기
        if connection_number > 1:
            while self._robot_status[discovery_group].processed_status.stepper_agg_set != True:
                pass
            self._robot_status[discovery_group].processed_status.stepper_agg_set = False
        if run_option.lower() == "schedule":
            time.sleep(0.2)
            ### 바이트 쓰기, 포인트로 작동
            sending_bytes = b""
            for i, cube_ID_element in enumerate(cube_ID_list):
                sending_bytes += self.GenerateProtocolInstance.SetScheduledPoints_bytes(cube_ID_element, [0], [len(speed_list[i])], [1], discovery_group, pause_list[i])
            sending_bytes = self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, sending_bytes)
            self._write_copy(sending_bytes)
        else:
            time.sleep(0.5)
        ### sleep
        if wait != 0:
            time.sleep(wait + 0.3)
        time.sleep(0.2)


    # 모터 멈춤
    def stop_motor(self, cube_ID_list="all", discovery_group=None) -> None:
        self.run_motor(cube_ID_list=cube_ID_list, speed_list=0, discovery_group=discovery_group) # continue mode


    # 스케줄 설정
    def set_motor_schedule(self, cube_ID_list, speed_list, step_list, pause_list=True, time_list=None, \
        discovery_group=None, speed_option="RPM", step_option="CYCLE", sync=False, time_option=None, \
        wait=0) -> None:
        self.run_motor(cube_ID_list, speed_list, step_list, pause_list, time_list, discovery_group, \
            "schedule", speed_option, step_option, sync, time_option, wait)
    

    # 스케줄 실행
    def play_motor_schedule(self, cube_ID_list="all", repeat_list=[[1]], start_point_list=[[None]], stop_point_list=[[None]], 
        start_and_stop_list=[[None]], pause_list=False, discovery_group=None, sync=False, wait=0) -> None:
        """
        Play motors with set schedule.
        """
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number

        ### start 체크
        self._start_check_copy()
        
        ### start, stop, repeat 리스트화
        start_point_list = Utils().to_list(start_point_list)
        stop_point_list = Utils().to_list(stop_point_list)
        repeat_list = Utils().to_list(repeat_list)
        cube_ID_list = Utils().to_list(cube_ID_list)
        pause_list = Utils().to_list(pause_list)
        start_and_stop_list = Utils().to_list(start_and_stop_list)

        ### 큐브 ID 처리
        if cube_ID_list == [] or cube_ID_list == ():
            raise ValueError("cube ID must not be empty list.")
        for i in range(len(cube_ID_list)):
            cube_ID_list[i] = self.GenerateProtocolInstance._process_cube_ID(cube_ID_list[i])
            if cube_ID_list[i] == 0xFF and len(cube_ID_list) != 1:
                raise ValueError("If cube ID is all, input must not be length-above-2 list.")
        Utils().check_same_element(cube_ID_list) # 같은 원소가 있으면 error
        if cube_ID_list[0] == 0xFF:
            run_number = connection_number
        else:
            run_number = len(cube_ID_list)

        ### 스케줄 셋 체크
        for cube_ID_element in cube_ID_list:
            if self._robot_status[discovery_group].controller_status.stepper_speed_schedule[cube_ID_element] == []: # 스케줄이 비었음
                raise ValueError("Set schedule before play.")
            #elif self._robot_status[discovery_group].controller_status.stepper_pause[x] == False: # 이전에 play 상태로 끝남
            #    pass

        ### 일시정지 체크
        if pause_list == [] or pause_list == ():
            raise ValueError("pause_list must not be empty list (or tuple).")
        for pause_element in pause_list:
            if not isinstance(pause_element, bool):
                raise ValueError("pause_list elements must be bool.")

        ### 싱크 체크
        if not isinstance(sync, bool):
            raise ValueError("sync must be bool.")

        ### wait 체크
        if not isinstance(wait, int) and not isinstance(wait, float) and not isinstance(wait, str):
            raise ValueError("wait must be int, float, or str.")
        elif (isinstance(wait, int) or isinstance(wait, float)) and wait < 0:
            raise ValueError("wait must be positive.")
        elif isinstance(wait, str) and wait.lower() != "step" and wait.lower() != "schedule":
            raise ValueError("Unknown wait option.")

        ### start_and_stop_list 변환 함수
        def check_start_and_stop_list(start_and_stop_list_in):
            # Ex)
            # [[1, 2], [3, 4]]
            # [1, 2]
            # [[1, 2], [3, 4], [5, 6]]
            # [2, [2, 3], 3, [4, 5]]
            start = []
            stop = []
            if isinstance(start_and_stop_list_in, list) or isinstance(start_and_stop_list_in, tuple):
                for i in range(len(start_and_stop_list_in)):
                    if isinstance(start_and_stop_list_in[i], list) or isinstance(start_and_stop_list_in[i], tuple):
                        if len(start_and_stop_list_in[i]) == 1:
                            start_and_stop_list_in[i] *= 2
                        elif len(start_and_stop_list_in[i]) != 2:
                            raise ValueError("If start_and_stop_list elements are list of lists (or tuple), elemental lists must be 1 or 2-length list (or tuple).")
                        if not isinstance(start_and_stop_list_in[i][0], int) or not isinstance(start_and_stop_list_in[i][1], int):
                            raise ValueError("If start_and_stop_list elements are list of lists (or tuple), elemental lists must have integer elements.")
                        else:
                            ### list 등록
                            start.append(start_and_stop_list_in[i][0])
                            stop.append(start_and_stop_list_in[i][1])
                    elif isinstance(start_and_stop_list_in[i], int):
                        ### list 등록
                        start.append(start_and_stop_list_in[i])
                        stop.append(start_and_stop_list_in[i])
                    else:
                        raise ValueError("start_and_stop_list must have list or int elements.")
                return start, stop
            elif isinstance(start_and_stop_list_in, int):
                ### list 등록
                start = start_and_stop_list_in
                stop = start_and_stop_list_in
                return start, stop
            else:
                raise ValueError("start_and_stop_list elements must be list (or tuple), or int.")

        ### 인스턴스 체크 & 디폴트 값 넣기
        if start_point_list == [[None]] and stop_point_list == [[None]]: # 스타트, 스탑 포인트 체크
            if start_and_stop_list != [[None]]:
                start_point_list = []
                stop_point_list = []
                for start_and_stop_list_element in start_and_stop_list:
                    if not isinstance(start_and_stop_list_element, list) and not isinstance(start_and_stop_list_element, tuple):
                        raise ValueError("start_and_stop_list elements must be list or tuple.")
                    start_point_list_out, stop_point_list_out = check_start_and_stop_list(start_and_stop_list_element)
                    start_point_list.append(start_point_list_out)
                    stop_point_list.append(stop_point_list_out)
            else:
                start_point_list, stop_point_list = [[0]], [["end"]] # 디폴트 0(처음), end(끝)
        elif start_and_stop_list != [[None]]:
            print("Warning. start_point_list and stop_point_list are ignored. start_and_stop_list is accepted.")
            start_point_list = []
            stop_point_list = []
            for start_and_stop_list_element in start_and_stop_list:
                if not isinstance(start_and_stop_list_element, list) and not isinstance(start_and_stop_list_element, tuple):
                    raise ValueError("start_and_stop_list elements must be list or tuple.")
                start_point_list_out, stop_point_list_out = check_start_and_stop_list(start_and_stop_list_element)
                start_point_list.append(start_point_list_out)
                stop_point_list.append(stop_point_list_out)
        elif start_point_list == [[None]]:
            start_point_list = [[0]]
        elif stop_point_list == [None]:
            stop_point_list = [["end"]]

        ### list of list 체크
        for start_point_list_element in start_point_list:
            if not (isinstance(start_point_list_element, list) or isinstance(start_point_list_element, tuple)):
                raise ValueError("All elements of start_point_list must be list or tuple.")
        for stop_point_list_element in stop_point_list:
            if not (isinstance(stop_point_list_element, list) or isinstance(stop_point_list_element, tuple)):
                raise ValueError("All elements of stop_point_list must be list or tuple.")
        for repeat_list_element in repeat_list:
            if not (isinstance(repeat_list_element, list) or isinstance(repeat_list_element, tuple)):
                raise ValueError("All elements of repeat_list must be list or tuple.")

        ### list 길이 체크
        if len(start_point_list) != 1 and len(start_point_list) != run_number:
            raise ValueError("start_point_list must have the same length as cube_ID_list, or have 1 length.")
        if len(stop_point_list) != 1 and len(stop_point_list) != run_number:
            raise ValueError("stop_point_list must have the same length as cube_ID_list, or have 1 length.")
        if len(repeat_list) != 1 and len(repeat_list) != run_number:
            raise ValueError("repeat_list must have the same length as cube_ID_list, or have 1 length.")
        if len(pause_list) != 1 and len(pause_list) != run_number:
            raise ValueError("pause_list must have the same length as cube_ID_list, or have 1 length.")

        ### 리스트 확장
        if cube_ID_list[0] == 0xFF:
            cube_ID_list = [i for i in range(connection_number)]
        if len(start_point_list) == 1: # 길이가 1이면 run_number 개수만큼 늘림
            start_point_list = Utils().list_product_copy(start_point_list, run_number)
        if len(stop_point_list) == 1: # 길이가 1이면 run_number 개수만큼 늘림
            stop_point_list = Utils().list_product_copy(stop_point_list, run_number)
        if len(repeat_list) == 1: # 길이가 1이면 run_number 개수만큼 늘림
            repeat_list = Utils().list_product_copy(repeat_list, run_number)
        if len(pause_list) == 1: # 길이가 1이면 run_number 개수만큼 늘림
            pause_list = pause_list*run_number
        
        ### 원소 길이 체크
        for start_point_list_element, stop_point_list_element, repeat_list_element in zip(start_point_list, stop_point_list, repeat_list):
            if len(start_point_list_element) != len(stop_point_list_element) or \
                len(start_point_list_element) != len(repeat_list_element):
                raise ValueError("Start list number, stop list, and repeat list number must be the same.")
                    
        ### sync 모드 체크
        if sync:
            if not self._robot_status[discovery_group].controller_status.stepper_schedule_sync_on[cube_ID_element]:
                raise ValueError("In sync mode, set schedule must be in sync mode.")
            else:
                for start_point_list_element, stop_point_list_element in zip(start_point_list, stop_point_list):
                    if start_point_list_element != start_point_list[0] or \
                        stop_point_list_element != stop_point_list_element[0]:
                        raise ValueError("In sync mode, each point schedule must be the same.")
        
        ### 스케줄 셋 체크 
        speed_length_list = list(map(len, self._robot_status[discovery_group].controller_status.stepper_speed_schedule))
        for i, cube_ID_element in enumerate(cube_ID_list):
            for j in range(len(start_point_list[i])):
                if isinstance(stop_point_list[i][j], str) and stop_point_list[i][j].lower() == "end":
                    stop_point_list[i][j] = speed_length_list[cube_ID_element]-1 # end이면 제일 뒤에 인덱스(stop은 마지막 인덱스)
                Utils().integer_check(start_point_list[i][j])
                Utils().integer_check(stop_point_list[i][j])
                Utils().integer_check(repeat_list[i][j])
                if start_point_list[i][j] < 0 or stop_point_list[i][j] < 0 \
                    or speed_length_list[cube_ID_element]-1 < start_point_list[i][j] \
                    or speed_length_list[cube_ID_element]-1 < stop_point_list[i][j]:
                    raise ValueError("Unavailable point index. Schedule does not have that index.")
                elif stop_point_list[i][j] < start_point_list[i][j]:
                    raise ValueError("Start index must be less than or equal to stop index.")
                if repeat_list[i][j] < 0 or 255 < repeat_list[i][j]:
                    raise ValueError("Unavailable number. Repeat must be positive, or smaller than 256.")

        ### wait 처리 함수
        def convert_wait():
            def cal_time(speed_element, step_element):
                if speed_element == 0:
                    new_time_out = step_element/1000
                else:
                    speed_element = self.GenerateProtocolInstance.SPS_to_RPM(speed_element)/60 # RPS
                    step_element = self.GenerateProtocolInstance.step_to_cycle(step_element)
                    new_time_out = abs(step_element/speed_element)
                return new_time_out
            # speed: SPS, step: STEP
            speed_list = []
            step_list = []
            for cube_ID_element in cube_ID_list:
                speed_list.append(self._robot_status[discovery_group].controller_status.stepper_speed_schedule[cube_ID_element])
                speed_list.append(self._robot_status[discovery_group].controller_status.stepper_step_schedule[cube_ID_element])
            ### max time 계산
            max_time = 0
            for i in range(len(start_point_list)): # i: cube ID 인덱스
                if pause_list[i]: # pause이면 wait 무시
                    new_time = 0
                else:
                    new_time = 0
                    for j in range(len(start_point_list[i])): # j: 포인트 인덱스
                        for k in range(start_point_list[i][j], stop_point_list[i][j]+1): # k: 스피드, 스텝 인덱스, +1은 마지막 인덱스 포함 때문.
                            new_time += cal_time(speed_list[i][k], step_list[i][k])
                if new_time > max_time:
                    max_time = new_time
            return max_time
        ### wait 처리
        if isinstance(wait, str) and (wait.lower() == "step" or wait.lower() == "schedule"):
            wait = convert_wait()

        ### 작동 처리 (discovery_group 처리 해야함)
        sending_bytes = b""
        for i, cube_ID_element in enumerate(cube_ID_list):
            ### status 등록
            self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "point"
            self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
            self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[cube_ID_element] = start_point_list[i]
            self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[cube_ID_element] = stop_point_list[i]
            self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[cube_ID_element] = repeat_list[i]
            ### 포인트 설정
            sending_bytes += self.GenerateProtocolInstance.SetScheduledPoints_bytes(cube_ID_element, start_point_list[i], stop_point_list[i], repeat_list[i], discovery_group, pause_list[i])
        
        ### 바이트 쓰기, 작동
        if connection_number > 1:
            sending_bytes = self.GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, sending_bytes)
        self._write_copy(sending_bytes)

        ### sleep
        if wait != 0:
            time.sleep(wait + 0.3)
        time.sleep(0.2)