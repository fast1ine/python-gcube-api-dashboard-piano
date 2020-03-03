from generateprotocol import GenerateProtocol
from operationutils import OperationUtils
import time

class MotorOperationBase():
    def __init__(self, number, robot_status, start_check, write):
        self._GenerateProtocolInstance = GenerateProtocol(number)
        self._robot_status = robot_status
        self._start_check_copy = start_check
        self._write_copy = write

    ### robot_status 얻기
    def _get_robot_status(self, discovery_group, status, variable):
        return eval("self._robot_status[{}].{}.{}".format(discovery_group, status, variable))

    ### robot_status 설정
    def _set_robot_status(self, discovery_group, status, variable, value):
        exec("self._robot_status[{}].{}.{} = {}".format(discovery_group, status, variable, value))


class ContinuousMotorOperation(MotorOperationBase):
    def __init__(self, number, robot_status, start_check, write):
        MotorOperationBase.__init__(self, number, robot_status, start_check, write)

    ### 컨티뉴 모드 모터 작동
    def run_motor_continue(self, 
        cube_ID_list="all", 
        speed_list=None, 
        pause_list=False, 
        discovery_group=None, 
        speed_option="RPM", 
        wait=0) -> None:
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        ### 시작 체크
        self._start_check_copy()
        ### cube_ID, speed, pause 리스트화
        cube_ID_list = OperationUtils().to_list(cube_ID_list)
        speed_list = OperationUtils().to_list(speed_list)
        pause_list = OperationUtils().to_list(pause_list)
        ### 큐브 ID 리스트 처리
        cube_ID_list = OperationUtils().process_cube_ID_list(cube_ID_list, connection_number)
        ### run_number 정의
        run_number = OperationUtils().set_run_number(cube_ID_list, connection_number)
        ### pause 리스트 체크
        OperationUtils().check_pause_list(pause_list)
        ### speed 옵션 체크
        OperationUtils().check_speed_option(speed_option)
        ### wait 체크
        OperationUtils().check_wait(wait, run_option="continue")
        ### 디폴트 설정
        speed_list = OperationUtils().set_default(speed_list=speed_list, step_list=None, speed_option=speed_option, step_option=None, run_option="continue")
        ### speed, pause 길이 체크
        OperationUtils().len_check(speed_list, cube_ID_list, connection_number, mode_name="continue", list_name="speed_list")
        OperationUtils().len_check(pause_list, cube_ID_list, connection_number, mode_name="continue", list_name="pause_list")
        ### 속도 제한
        speed_list, _ = OperationUtils().limit_speed(speed_list, speed_option, run_number, sync=False, run_option="continue")
        ### 바이트 확장
        cube_ID_list, speed_list, pause_list = OperationUtils().expand_bytes(cube_ID_list, connection_number, run_number, speed_list, pause_list)
        ### 작동 처리
        sending_bytes = b""
        print(cube_ID_list)
        for i, cube_ID_element in enumerate(cube_ID_list):
            ### 멈춤 설정
            if speed_list[i] == 0:
                pause_list[i] = True # 0일 때 pause로 안 보내면 다음 명령어가 안 먹음
            ### status 등록
            self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "continue"
            self._robot_status[discovery_group].controller_status.stepper_speed[cube_ID_element] = speed_list[i]
            self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
            ### bytes 붙이기
            sending_bytes += self._GenerateProtocolInstance.SetContinuousSteps_bytes(cube_ID_element, speed_list[i], discovery_group, pause_list[i])
        ### agg로 설정
        if connection_number > 1:
            sending_bytes = self._GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, sending_bytes)
        ### 바이트 쓰기
        self._write_copy(sending_bytes) 
        ### agg 설정이 올 때까지 잡아두기
        OperationUtils().wait_until_agg_set(self._get_robot_status, self._set_robot_status, discovery_group, connection_number)
        ### sleep
        if wait != 0:
            time.sleep(wait + 0.3)
        time.sleep(0.2)


class SingleStepMotorOperation(MotorOperationBase):
    def __init__(self, number, robot_status, start_check, write):
        MotorOperationBase.__init__(self, number, robot_status, start_check, write)

    ### 스텝 모드 모터 작동
    def run_motor_step(self, 
        cube_ID_list="all", 
        speed_list=None, 
        step_list=None, 
        pause_list=False, 
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
        cube_ID_list = OperationUtils().to_list(cube_ID_list)
        speed_list = OperationUtils().to_list(speed_list)
        step_list = OperationUtils().to_list(step_list)
        pause_list = OperationUtils().to_list(pause_list)
        ### 큐브 ID 리스트 처리
        cube_ID_list = OperationUtils().process_cube_ID_list(cube_ID_list, connection_number)
        ### run_number 정의
        run_number = OperationUtils().set_run_number(cube_ID_list, connection_number)
        ### pause 리스트 체크
        OperationUtils().check_pause_list(pause_list)
        ### speed 옵션 체크
        OperationUtils().check_speed_option(speed_option)
        ### step 옵션 체크
        OperationUtils().check_step_option(step_option)
        ### sync 옵션 체크
        OperationUtils().check_sync_option(sync)
        ### time 옵션 체크 & 처리
        time_option = OperationUtils().check_time_option(time_option)
        ### wait 체크
        OperationUtils().check_wait(wait, run_option="step")
        ### 디폴트 설정
        speed_list, step_list = OperationUtils().set_default(speed_list, run_option="step", speed_option=speed_option, step_list=step_list, step_option=step_option)
        ### time 옵션 분기 설정
        ### time 옵션 없음
        if time_option.lower() == "none":
            ### speed, step 길이 체크
            OperationUtils().len_check(speed_list, cube_ID_list, connection_number, mode_name="step", list_name="speed_list")
            OperationUtils().len_check(step_list, cube_ID_list, connection_number, mode_name="step", list_name="step_list")
            ### 속도, 스텝 제한
            speed_list, sleep_list = OperationUtils().limit_speed(speed_list, speed_option, run_number, sync, run_option="step")
            step_list, speed_list = OperationUtils().limit_step(step_list, speed_list, sleep_list, step_option, run_number, sync, run_option="step")
        ### time 옵션 speed 모드
        elif time_option.lower() == "speed":
            ### time, speed 길이 체크
            OperationUtils().len_check(time_list, cube_ID_list, connection_number, mode_name="step and time-speed", list_name="time_list")
            OperationUtils().len_check(speed_list, cube_ID_list, connection_number, mode_name="step and time-speed", list_name="speed_list")
            ### 속도 제한
            speed_list, sleep_list = OperationUtils().limit_speed(speed_list, speed_option, run_number, sync, run_option="step")
            step_list, _, speed_option, step_option = OperationUtils().convert_time_list(time_list, speed_list, step_list=None, speed_option=speed_option, step_option=None, run_number=run_number, sync=sync, run_option="step", time_option="speed")
            step_list, speed_list = OperationUtils().limit_step(step_list, speed_list, sleep_list, step_option="STEP", run_number=run_number, sync=sync, run_option="step")
        ### time 옵션 step 모드
        elif time_option.lower() == "step":
            ### time, step 길이 체크
            OperationUtils().len_check(time_list, cube_ID_list, connection_number, mode_name="step and time-step", list_name="time_list")
            OperationUtils().len_check(step_list, cube_ID_list, connection_number, mode_name="step and time-step", list_name="step_list")
            ### 속도 제한
            speed_list, step_list, speed_option, step_option = OperationUtils().convert_time_list(time_list, speed_list=None, step_list=step_list, speed_option=None, step_option=step_option, run_number=run_number, sync=sync, run_option="step", time_option="step")
            speed_list, sleep_list = OperationUtils().limit_speed(speed_list, speed_option, run_number, sync, run_option="step")
            step_list, speed_list = OperationUtils().limit_step(step_list, speed_list, sleep_list, step_option="STEP", run_number=run_number, sync=sync, run_option="step")
        ### pause 길이 체크
        OperationUtils().len_check(pause_list, cube_ID_list, connection_number, mode_name="step", list_name="pause_list")
        ### 바이트 확장
        cube_ID_list, speed_list, step_list, pause_list = OperationUtils().expand_bytes(cube_ID_list, connection_number, run_number, speed_list, step_list, pause_list)
        ### sync 모드 처리
        speed_list, step_list = OperationUtils().check_time_sync_none(speed_list, step_list, sync, run_number, run_option="step")
        ### wait 변환 (wait = "step" 또는 "schedule"이면 현재 run_option에 맞춰서 알아서 계산)
        if isinstance(wait, str):
            wait = OperationUtils().convert_wait(speed_list, step_list, pause_list, run_option="step")
        ### 작동 처리 (discovery_group 처리 해야함)
        sending_bytes = b""
        for i, cube_ID_element in enumerate(cube_ID_list):
            ### status 등록
            self._robot_status[discovery_group].controller_status.stepper_mode[cube_ID_element] = "step"
            self._robot_status[discovery_group].controller_status.stepper_speed[cube_ID_element] = speed_list[i]
            self._robot_status[discovery_group].controller_status.stepper_step[cube_ID_element] = step_list[i]
            self._robot_status[discovery_group].controller_status.stepper_pause[cube_ID_element] = pause_list[i]
            ### bytes 붙이기
            sending_bytes += self._GenerateProtocolInstance.SetSingleSteps_bytes(cube_ID_element, speed_list[i], step_list[i], discovery_group, pause_list[i])
        if connection_number > 1:
            sending_bytes = self._GenerateProtocolInstance.SetAggregateSteps_bytes(discovery_group, sending_bytes)
        ### 바이트 쓰기
        self._write_copy(sending_bytes) 
        ### agg 설정이 올 때까지 잡아두기
        OperationUtils().wait_until_agg_set(self._get_robot_status, self._set_robot_status, discovery_group, connection_number)
        ### sleep
        if wait != 0:
            time.sleep(wait + 0.3)
        time.sleep(0.2)