from protocols.generateprotocol import GenerateProtocol
from operations.cube.cubeoperationutils import CubeOperationUtils
import time

class CubeOperation():
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

    ### 센서 데이터 얻기
    def receive_sensor_data(self, cube_ID, method, period=1, discovery_group=None):
        ### start 체크
        self._start_check_copy()
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        ### cube ID 처리
        cube_ID = CubeOperationUtils().process_cube_ID(cube_ID, connection_number)
        ### method 체크 (str, "oneshot", "periodic", "stop")
        CubeOperationUtils().check_method(method, cube_ID, discovery_group, self._get_robot_status, self._set_robot_status)
        ### period 체크 & 처리 (int or float, 0.01 to 1 (sec))
        period = CubeOperationUtils().process_period(method, period)
        ### 바이트 쓰기
        sending_bytes = self._GenerateProtocolInstance.GetSensors_bytes(cube_ID, period, discovery_group)
        self._write_copy(sending_bytes) 
        ### sleep
        time.sleep(0.2)

    ### 센서 데이터 끄기
    def stop_sensor_data(self, cube_ID, discovery_group=None):
        self.receive_sensor_data(self, cube_ID, "stop", 1, discovery_group)