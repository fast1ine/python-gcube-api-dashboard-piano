# Environment: Windows x64, Python x64 3.6.6
# pyserial==3.4

from serialprotocol import ReaderThread
from utils import Utils
from rawprotocol import rawProtocol
from generateprotocol import GenerateProtocol
import sys
import time
import serial

class PingPongThread(GenerateProtocol, ReaderThread):
    _is_instance = False
    _is_start = False
    def __init__(self, number=1):
        self._set_connection_number(number)
        if not PingPongThread._is_instance:
            GenerateProtocol.__init__(self, self._connection_number) # generate protocol init
            self._set_connection_number(number) # 연결할 로봇 대수
            PingPongThread._is_instance = True # 인스턴스 생성 확인
            self.PORT = Utils().find_bluetooth_dongle(self.DongleInAction_bytes()) # 동글 포트 찾기
            self._play_once_flag = True
        else:
            raise ValueError("PingpongThread instance cannot be constructed above 1.")

    def __del__(self) -> None:
        PingPongThread.is_instance = False
        try:
            self.close()
        except:
            pass

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

    # 시작 체크
    def _start_check(self):
        if not PingPongThread._is_start:
            raise ValueError("Thread did not start! Please start() before do something, or end thread.")

    # 연결 숫자 정하기
    def _set_connection_number(self, number) -> None:
        Utils().integer_check(number)
        # no start check
        if 1 <= number and number <= 8: # 1개 이상 8개 이하 
            self._connection_number = number # 연결할 로봇 대수
        else:
            raise ValueError("PingPong robot can connect only with 1 to 8 robots.")

    # 로봇 연결
    def _connect_robot_thread(self) -> None:
        ser = None
        while True:
            ser = Utils().connect_serial_URL(self.PORT)
            if ser:
                break
            else:
                self.PORT = Utils().find_bluetooth_dongle(self.DongleInAction_bytes())
        ReaderThread.__init__(self, ser, rawProtocol)
        self.connection_number = self._connection_number
        self.write(self.PingPongGn_connect_bytes())

    # 쓰기
    def _write(self, protocol_bytes) -> None:
        try:
            self.write(protocol_bytes)
        except:
            print("Cannot write.")

    # 로봇 연결 해제
    def disconnect_master_robot(self) -> None:
        self._start_check()
        if self.connected_robots_number > 0:
            self.set_robot_disconnect_flag(True)
            self._write(self.PingPong_disconnect_bytes)
            print("Disconnect master robot.")
            # 1개는 해제 응답을 안 받음. 2개 이상은 해제 응답을 받음.
        else:
            print("Master robot is not connected.")

    def reconnect_robot(self) -> None:
        print("Reconnect with robots.")
        #self.ReaderThreadInstance.serial.close()
        #self.ReaderThreadInstance.reconnect()
        self._write(self.PingPongGn_connect_bytes())

    def get_is_start(self) -> bool:
        return PingPongThread._is_start

    # 완전 연결 체크
    def get_is_full_connect(self) -> bool:
        self._start_check()
        is_full_connect_flag = self.is_full_connect
        if not is_full_connect_flag:
            self._play_once_flag = True # play_once용
        return is_full_connect_flag

    # 완전 연결까지 기다림
    def wait_until_full_connect(self) -> None:
        self._start_check()
        while not self.get_is_full_connect():
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
        self._start_check()
        if not isinstance(option, str):
            raise ValueError("option must be str.")
        if not isinstance(pause, bool):
            raise ValueError("pause must be bool.")
        if option.lower() == "schedule" and self.connection_number > 1: # 1이면 반응이 안 옴
            if not pause:
                self._write(self.run_motor_bytes(cube_ID, speed, step_cycle, True, discovery_group, option)) # pause
                while not self.is_schedule_set: # 스케줄 완료가 되면 실행
                    pass
                time.sleep(0.2)
                self._write(self.pause_motor_bytes(False, cube_ID, discovery_group, False)) # play motor
            else:
                self._write(self.run_motor_bytes(cube_ID, speed, step_cycle, pause, discovery_group, option))
        else:
            self._write(self.run_motor_bytes(cube_ID, speed, step_cycle, pause, discovery_group, option))
        time.sleep(0.2)

    # 스케줄 설정
    def set_motor_schedule(self, cube_ID, speed_list, step_cycle_list, pause=True, discovery_group=None) -> None:
        self._start_check()
        if not isinstance(pause, bool):
            raise ValueError("pause must be bool.")
        if self.connection_number > 1: # 1이면 반응이 안 옴
            if not pause:
                self._write(self.run_motor_bytes(cube_ID, speed_list, step_cycle_list, True, discovery_group, "schedule")) # pause
                while not self.is_schedule_set: # 스케줄 완료가 되면 실행
                    pass
                time.sleep(0.2)
                self._write(self.pause_motor_bytes(False, cube_ID, discovery_group, False)) # play motor
            else:
                self._write(self.run_motor_bytes(cube_ID, speed_list, step_cycle_list, pause, discovery_group, "schedule"))
        else:
            self._write(self.run_motor_bytes(cube_ID, speed_list, step_cycle_list, pause, discovery_group, "schedule"))
        time.sleep(0.2)

    # 스케줄 실행
    def play_motor_schedule(self, cube_ID, repeat_list=1, start_point_list=0, stop_point_list="end", 
        start_and_stop_list=None, discovery_group=None, pause=False) -> None:
        self._start_check()
        if not isinstance(pause, bool):
            raise ValueError("pause must be bool.")
        if start_and_stop_list:
            if not isinstance(pause, list): #####만드는중
                pass



        if self.connection_number > 1: # 1이면 반응이 안 옴
            if not pause:
                self._write(self.play_motor_schedule_bytes(cube_ID, start_point_list, stop_point_list, repeat_list, \
                    discovery_group, True)) # pause
                while not self.is_point_set: # 포인트 완료가 되면 실행
                    pass
                time.sleep(0.2)
                self._write(self.pause_motor_bytes(False, cube_ID, discovery_group, False)) # play motor
            else:
                self._write(self.play_motor_schedule_bytes(cube_ID, start_point_list, stop_point_list, repeat_list, \
                    discovery_group, pause)) 
        else:
            self._write(self.play_motor_schedule_bytes(cube_ID, start_point_list, stop_point_list, repeat_list, \
                discovery_group, pause)) 
        time.sleep(0.2)

    # 모터 일시정지
    def pause_motor(self, cube_ID=None, discovery_group=None, group_mode=False) -> None:
        self._start_check()
        self._write(self.pause_motor_bytes(True, cube_ID, discovery_group, group_mode))
        time.sleep(0.2)

    # 모터 재생
    def play_motor(self, cube_ID=None, discovery_group=None, group_mode=False) -> None:
        self._start_check()
        self._write(self.pause_motor_bytes(False, cube_ID, discovery_group, group_mode))
        time.sleep(0.2)

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



