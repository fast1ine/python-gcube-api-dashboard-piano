# Environment: Windows x64, Python x64 3.6.6
# pyserial==3.4

from serialprotocol import ReaderThread
from utils import Utils
from rawprotocol import rawProtocol
from generateprotocol import GenerateProtocol
from motoroperation import MotorOperation
import sys
import time
import serial

class PingPongThread(ReaderThread, MotorOperation):
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
            MotorOperation.__init__(self, self.GenerateProtocolInstance, self._robot_status, self._start_check, self._write) # MotorOperation 초기화
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
        self._init_robot_status()
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

    # time_seconds 초 동안 기다림
    def wait(self, time_seconds):
        if not isinstance(time_seconds, int) and not isinstance(time_seconds, float):
            raise ValueError("time_seconds must be int or float.")
        elif time_seconds < 0:
            raise ValueError("time_seconds must positive value.")
        time.sleep(time_seconds)



### 상태 저장용 구조체
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
        self.stepper_schedule_sync_on = [None]*connection_number
        self.stepper_schedule_point_start = [[]]*connection_number
        self.stepper_schedule_point_end = [[]]*connection_number
        self.stepper_schedule_point_repeat = [[]]*connection_number
class ProcessedStatus():
    def __init__(self, connection_number):
        ### connection status
        self.connected_number = 0
        self.MAC_address = [None]*2
        ### stepper status
        self.stepper_agg_set = None
        self.stepper_schedule_set = [None]*connection_number
        self.stepper_point_set = [None]*connection_number
        self.stepper_played_pause = [None]*connection_number
        self.stepper_played_schedule_idx = [None]*connection_number
        self.stepper_played_point_idx = [None]*connection_number
        self.stepper_played_repeat_idx = [None]*connection_number


"""
def main():
    pass

if __name__ == "__main__":
    main()
"""
