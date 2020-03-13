from protocols.generateprotocol import GenerateProtocol
from operations.servo.servooperationutils import ServoOperationUtils
import time

class ServoOperation():
    def __init__(self, number, robot_status, start_check, write):
        self._GenerateProtocolInstance = GenerateProtocol(number)
        self._robot_status = robot_status
        self._start_check_copy = start_check
        self._write_copy = write
        
    def run_single_servo(self, cube_ID, angle, discovery_group=None):
        """
        1개 (또는 모두) 큐브 서보 모터 작동

        cube_ID: 1 to 8, 또는 \"all\".
        angle: int, 0 to 180.
        discovery_group: 작동시킬 큐브가 소속된 그룹 (0 to 7?). None이면 0xFF.
        """
        ### start 체크
        self._start_check_copy()
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        ### cube ID 처리
        cube_ID = ServoOperationUtils().process_cube_ID(cube_ID, connection_number)
        ### angle 체크
        ServoOperationUtils().check_servo_angle(angle)
        ### status 등록
        if cube_ID == 0xFF:
            for i in range(connection_number):
                self._robot_status[discovery_group].controller_status.servo_mode[i] = "single"
                self._robot_status[discovery_group].controller_status.servo_angle[i] = angle
        else:
            self._robot_status[discovery_group].controller_status.servo_mode[cube_ID] = "single"
            self._robot_status[discovery_group].controller_status.servo_angle[cube_ID] = angle
        ### byte 쓰기
        # timeout = 1 sec
        sending_bytes = self._GenerateProtocolInstance.SetSingleServo(cube_ID, angle, timeout=1, discovery_group=discovery_group)
        self._write_copy(sending_bytes) 
        ### sleep
        time.sleep(0.2)

    def run_servo_schedule(self, 
        cube_ID_list="all", 
        servo_angle_list=None,
        servo_duration=None,

        pause_list=False,
        speed_list=None, 
        step_list=None, 
        time_list=None, 
        discovery_group=None, 
        speed_option="RPM", 
        step_option="CYCLE", 
        sync=False, 
        time_option=None,
        wait=0) -> None:
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        ### 시작 체크
        self._start_check_copy()
        ### cube_ID, speed, step, pause 리스트화
        cube_ID_list = ServoOperationUtils().to_list(cube_ID_list)
        servo_angle_list = ServoOperationUtils().to_list(servo_angle_list)
        servo_duration = ServoOperationUtils().to_list(servo_duration)
        pause_list = ServoOperationUtils().to_list(pause_list)
        speed_list = ServoOperationUtils().to_list(speed_list)
        step_list = ServoOperationUtils().to_list(step_list)
        time_list = ServoOperationUtils().to_list(time_list)
        ### 큐브 ID 리스트 처리
        cube_ID_list = ServoOperationUtils().process_cube_ID_list(cube_ID_list, connection_number)
        ### run_number 정의
        run_number = ServoOperationUtils().set_run_number(cube_ID_list, connection_number)
        ### pause 리스트 체크
        ServoOperationUtils().check_pause_list(pause_list)
        ### speed 옵션 체크
        ServoOperationUtils().check_speed_option(speed_option)
        ### step 옵션 체크
        ServoOperationUtils().check_step_option(step_option)
        ### sync 옵션 체크
        ServoOperationUtils().check_sync_option(sync)
        ### time 옵션 체크 & 처리
        time_option = ServoOperationUtils().check_time_option(time_option)
        ### wait 체크
        ServoOperationUtils().check_wait(wait, run_option="schedule")
        ### 디폴트 체크 & 처리
        if servo_duration == [None]:
            duration_option = False
        else:
            duration_option = True
        servo_angle_list, servo_duration = ServoOperationUtils().set_default_servo(input_list=[servo_angle_list, servo_duration, speed_list, step_list, time_list], option_list=[duration_option, time_option], run_option="schedule")
        ### servo_angle_list

                

        ### time 옵션 분기 설정
        ### time 옵션 없음
        if time_option.lower() == "none":
            ### speed, step 리스트가 list of list인지 체크 (dataframe, array 이용? (numpy, pandas 등 사용))
            StepperOperationUtils().check_list_of_list(speed_list, mode_name="schedule", list_name="speed_list", run_option="schedule")
            StepperOperationUtils().check_list_of_list(step_list, mode_name="schedule", list_name="step_list", run_option="schedule")
            ### speed, step 리스트 길이 체크
            StepperOperationUtils().len_check(speed_list, cube_ID_list, connection_number, mode_name="schedule", list_name="speed_list", run_number=run_number, run_option="schedule")
            StepperOperationUtils().len_check(step_list, cube_ID_list, connection_number, mode_name="schedule", list_name="step_list", run_number=run_number, run_option="schedule")
            ### 내부 원소 길이 체크
            StepperOperationUtils().len_check_elemental_list(speed_list, step_list, mode_name="schedule", input_list1_name="speed_list", input_list2_name="step_list")
            ### sync 모드일 때 내부 원소 길이 체크
            StepperOperationUtils().len_check_elemental_list_in_sync(sync, speed_list, step_list, mode_name="schedule sync", input_list1_name="speed_list", input_list2_name="step_list")
            ### 속도, 스텝 제한
            speed_list, sleep_list = StepperOperationUtils().limit_speed(speed_list, speed_option, run_number, sync, run_option="schedule")
            step_list, speed_list = StepperOperationUtils().limit_step(step_list, speed_list, sleep_list, step_option, run_number, sync, run_option="schedule")
        ### time 옵션 speed 모드
        elif time_option.lower() == "speed":
            ### time, speed 리스트가 list of list인지 체크 (dataframe, array 이용? (numpy, pandas 등 사용))
            StepperOperationUtils().check_list_of_list(time_list, mode_name="schedule", list_name="time_list", run_option="schedule")
            StepperOperationUtils().check_list_of_list(speed_list, mode_name="schedule", list_name="speed_list", run_option="schedule")
            ### time, speed 리스트 길이 체크
            StepperOperationUtils().len_check(time_list, cube_ID_list, connection_number, mode_name="schedule", list_name="time_list", run_number=run_number, run_option="schedule")
            StepperOperationUtils().len_check(speed_list, cube_ID_list, connection_number, mode_name="schedule", list_name="speed_list", run_number=run_number, run_option="schedule")
            ### 내부 원소 길이 체크
            StepperOperationUtils().len_check_elemental_list(time_list, speed_list, mode_name="schedule", input_list1_name="time_list", input_list2_name="speed_list")
            ### sync 모드일 때 내부 원소 길이 체크
            StepperOperationUtils().len_check_elemental_list_in_sync(sync, time_list, speed_list, mode_name="schedule sync", input_list1_name="time_list", input_list2_name="speed_list")
            ### 시간 변환, 속도, 스텝 제한
            speed_list, sleep_list = StepperOperationUtils().limit_speed(speed_list, speed_option, run_number, sync, run_option="schedule")
            step_list, _, speed_option, step_option = StepperOperationUtils().convert_time_list(time_list, speed_list, step_list=None, speed_option=speed_option, step_option=None, run_number=run_number, sync=sync, run_option="schedule", time_option="speed")
            step_list, speed_list = StepperOperationUtils().limit_step(step_list, speed_list, sleep_list, step_option="STEP", run_number=run_number, sync=sync, run_option="schedule")
        ### time 옵션 step 모드
        elif time_option.lower() == "step":
            ### time, step 리스트가 list of list인지 체크 (dataframe, array 이용? (numpy, pandas 등 사용))
            StepperOperationUtils().check_list_of_list(time_list, mode_name="schedule", list_name="time_list", run_option="schedule")
            StepperOperationUtils().check_list_of_list(step_list, mode_name="schedule", list_name="step_list", run_option="schedule")
            ### time, step 리스트 길이 체크
            StepperOperationUtils().len_check(time_list, cube_ID_list, connection_number, mode_name="schedule", list_name="time_list", run_number=run_number, run_option="schedule")
            StepperOperationUtils().len_check(step_list, cube_ID_list, connection_number, mode_name="schedule", list_name="step_list", run_number=run_number, run_option="schedule")
            ### 내부 원소 길이 체크
            StepperOperationUtils().len_check_elemental_list(time_list, step_list, mode_name="schedule", input_list1_name="time_list", input_list2_name="step_list")
            ### sync 모드일 때 내부 원소 길이 체크
            StepperOperationUtils().len_check_elemental_list_in_sync(sync, time_list, step_list, mode_name="schedule sync", input_list1_name="time_list", input_list2_name="step_list")
            ### 시간 변환, 속도, 스텝 제한
            speed_list, step_list, speed_option, step_option = StepperOperationUtils().convert_time_list(time_list, speed_list=None, step_list=step_list, speed_option=None, step_option=step_option, run_number=run_number, sync=sync, run_option="schedule", time_option="step")
            speed_list, sleep_list = StepperOperationUtils().limit_speed(speed_list, speed_option, run_number, sync, run_option="schedule")
            step_list, speed_list = StepperOperationUtils().limit_step(step_list, speed_list, sleep_list, step_option="STEP", run_number=run_number, sync=sync, run_option="schedule")
        ### pause 길이 체크
        StepperOperationUtils().len_check(pause_list, cube_ID_list, connection_number, mode_name="schedule", list_name="pause_list", run_number=run_number, run_option="schedule")
        ### 바이트 확장
        cube_ID_list, speed_list, step_list, pause_list = StepperOperationUtils().expand_bytes(cube_ID_list, connection_number, run_number, speed_list, step_list, pause_list)
        ### sync 모드 처리
        speed_list, step_list = StepperOperationUtils().check_time_sync_none(speed_list, step_list, sync, run_number, run_option="schedule")
        ### wait 변환 (wait = "step" 또는 "schedule"이면 현재 run_option에 맞춰서 알아서 계산)
        if isinstance(wait, str):
            wait = StepperOperationUtils().convert_wait(speed_list, step_list, pause_list, run_option="step")
        ### 작동 처리 (discovery_group 처리 해야함)
        sending_bytes = b""
        for i, cube_ID_element in enumerate(cube_ID_list):
            ### status 등록
            self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "point"
            self._robot_status[discovery_group].controller_status.stepper_schedule_point_start[cube_ID_element] = [0]
            self._robot_status[discovery_group].controller_status.stepper_schedule_point_end[cube_ID_element] = [len(speed_list[i])]
            self._robot_status[discovery_group].controller_status.stepper_schedule_point_repeat[cube_ID_element] = [1]
            self._robot_status[discovery_group].controller_status.stepper_speed_schedule[cube_ID_element] = speed_list[i]
            self._robot_status[discovery_group].controller_status.stepper_step_schedule[cube_ID_element] = step_list[i]
            self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
            self._robot_status[discovery_group].controller_status.stepper_schedule_sync_on[cube_ID_element] = sync
            ### bytes 붙이기
            sending_bytes += self._GenerateProtocolInstance.SetScheduledSteps_bytes(cube_ID_element, speed_list[i], step_list[i], discovery_group, True)
        if connection_number > 1:
            sending_bytes = self._GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, sending_bytes)
        ### 스케줄 설정 작동
        self._write_copy(sending_bytes) 
        ### 1개 이상이면 agg 설정이 올 때까지 잡아두기
        StepperOperationUtils().wait_until_agg_set(self._get_robot_status, self._set_robot_status, discovery_group, connection_number)
        ### 포인트로 작동
        time.sleep(0.2)
        sending_bytes = b""
        for i, cube_ID_element in enumerate(cube_ID_list):
            sending_bytes += self._GenerateProtocolInstance.SetScheduledPoints_bytes(cube_ID_element, [0], [len(speed_list[i])], [1], discovery_group, pause_list[i])
        if connection_number > 1:
            sending_bytes = self._GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, sending_bytes)
        self._write_copy(sending_bytes)
        ### sleep
        if wait != 0:
            time.sleep(wait + 0.3)
        time.sleep(0.2)

    def set_servo_schedule(self):
        pass

    def play_servo_schedule(self):
        pass