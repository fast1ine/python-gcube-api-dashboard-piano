from protocols.generateprotocol import GenerateProtocol
from operations.ledmatrix.ledmatrixutils import LEDMatrixUtils
import time

class LEDMatrixOperation():
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

    ### pixel 쓰기
    def LED_matrix_write_pixel(self, cube_ID, x_coordinate, y_coordinate, onoff=True, discovery_group=None):
        ### start 체크
        self._start_check_copy()
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        ### cube ID 처리
        cube_ID = LEDMatrixUtils().process_cube_ID(cube_ID, connection_number)
        ### coordinate 체크 (int, 0 to 7)
        LEDMatrixUtils().check_pixel_coord(x_coordinate)
        LEDMatrixUtils().check_pixel_coord(y_coordinate)
        ### on/off 체크 (bool)
        LEDMatrixUtils().check_onoff(onoff)
        ### 바이트 쓰기
        sending_bytes = self._GenerateProtocolInstance.ArduinoI2CLEDMatrixWritePixel_bytes(cube_ID, x_coordinate, y_coordinate, onoff, discovery_group)
        self._write_copy(sending_bytes) 
        ### sleep
        time.sleep(0.2)

    def LED_matrix_write_string(self, cube_ID, scroll_time, string, discovery_group=None):
        ### start 체크
        self._start_check_copy()
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        ### cube ID 처리
        cube_ID = LEDMatrixUtils().process_cube_ID(cube_ID, connection_number)
        ### string 체크 (str, len: 1 to 20, ASCII)
        LEDMatrixUtils().check_string(string)
        ### scroll time 처리 (float, sec, return: 1 to 200)
        scroll_time = LEDMatrixUtils().process_scroll_period(scroll_time, len(string))
        ### 바이트 쓰기
        sending_bytes = self._GenerateProtocolInstance.ArduinoI2CLEDMatrixWriteString_bytes(cube_ID, scroll_time, string, discovery_group)
        self._write_copy(sending_bytes) 
        ### sleep
        time.sleep(0.2)

    def LED_matrix_clear(self, cube_ID, discovery_group=None):
        ### start 체크
        self._start_check_copy()
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        ### cube ID 처리
        cube_ID = LEDMatrixUtils().process_cube_ID(cube_ID, connection_number)
        ### 바이트 쓰기
        sending_bytes = self._GenerateProtocolInstance.ArduinoI2CLEDMatrixWriteString_bytes(cube_ID, 0, "", discovery_group)
        self._write_copy(sending_bytes)
        ### sleep
        time.sleep(0.2) 

    def LED_matrix_write_picture(self, cube_ID, picture, discovery_group=None):
        ### start 체크
        self._start_check_copy()
        ### 연결 개수
        connection_number = self._robot_status[discovery_group].controller_status.connection_number
        ### cube ID 처리
        cube_ID = LEDMatrixUtils().process_cube_ID(cube_ID, connection_number)
        ### picture 체크 & 처리 (8 * 8 matrix (list of list), elements는 0 or 1.)
        picture = LEDMatrixUtils().process_picture(picture)
        ### 바이트 쓰기
        sending_bytes = self._GenerateProtocolInstance.ArduinoI2CLEDMatrixWritePicture_bytes(cube_ID, picture, discovery_group)
        self._write_copy(sending_bytes)
        ### sleep
        time.sleep(0.2) 

    #def LED_matrix_set_display(self):
    #    pass

    #def LED_matrix_set_brightness(self):
    #    pass

    #def LED_matrix_set_blinkrate(self):
    #    pass