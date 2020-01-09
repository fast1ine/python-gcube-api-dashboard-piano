# Environment: Windows x64, Python x64 3.6.6
# pyserial==3.4

from serialprotocol import ReaderThread
from utils import Utils
from rawprotocol import rawProtocol
from generateprotocol import GenerateProtocol
import sys
import time
import serial

class PingPongThread(GenerateProtocol):
    is_instance = False
    is_start = False
    def __init__(self, number=1):
        if not PingPongThread.is_instance:
            self._set_connection_number(number) # 연결할 로봇 대수
            PingPongThread.is_instance = True # 인스턴스 생성 확인
            GenerateProtocol.__init__(self, self.connection_number) # generate protocol init
            self.PORT = Utils().find_bluetooth_dongle(GenerateProtocol.DongleInAction_bytes(self)) # 동글 포트 찾기
        else:
            raise ValueError("PingpongThread instance cannot be constructed above 1.")

    def __del__(self) -> None:
        PingPongThread.is_instance = False
        try:
            self.ReaderThreadInstance.close()
            print("End thread.")
        except:
            pass

    # 쓰레드 시작
    def start(self) -> None:
        if not PingPongThread.is_start and PingPongThread.is_instance:
            PingPongThread.is_start = True
            self._connect_robot_thread(self.PORT)
            self.ReaderThreadInstance.start()
        elif PingPongThread.is_start:
            raise ValueError("PingPongThread instance cannot start above 1.")
        elif not PingPongThread.is_instance:
            #raise ValueError("No instance of PingpongThread! Please construct instance first.")
            # cannot reach
            print("?")
            pass
            
    # 쓰레드 종료
    def end(self) -> None:
        self.start_check()
        self.ReaderThreadInstance.close()
        print("End thread.")
        self.ReaderThreadInstance = None
        PingPongThread.is_start = False

    # 시작 체크
    def start_check(self):
        if not PingPongThread.is_start:
            raise ValueError("Thread did not start! Please start() before end the thread.")

    # 연결 숫자 정하기
    def _set_connection_number(self, number) -> None:
        Utils().integer_check(number)
        # no start check
        if 1 <= number and number <= 8: # 1개 이상 8개 이하 
            self.connection_number = number # 연결할 로봇 대수
            try:
                self.ReaderThreadInstance.connection_number = self.connection_number
            except:
                pass
        else:
            raise ValueError("PingPong robot can connect only with 1 to 8 robots.")

    # 로봇 연결
    def _connect_robot_thread(self, port) -> None:
        if PingPongThread.is_instance:
            ser = None
            while True:
                ser = Utils().connect_serial_URL(self.PORT)
                if ser:
                    break
                else:
                    self.PORT = Utils().find_bluetooth_dongle(GenerateProtocol.DongleInAction_bytes(self))
            self.ReaderThreadInstance = ReaderThread(ser, rawProtocol)
            self.ReaderThreadInstance.connection_number = self.connection_number
            self.ReaderThreadInstance.write(GenerateProtocol.PingPongGn_connect_bytes(self))
        else:
            #raise ValueError("No instance of PingpongThread! Please construct instance first.")
            # cannot reach
            print("?")
            pass

    # 쓰기
    def write(self, protocol_bytes) -> None:
        try:
            self.ReaderThreadInstance.write(protocol_bytes)
        except:
            print("Cannot write.")
            
    # 로봇 연결 해제
    def disconnect_master_robot(self) -> None:
        self.start_check()
        if self.get_connected_robots_number() > 0:
            self.write(GenerateProtocol.PingPong_disconnect_bytes)
            print("Disconnect master robot.")
        else:
            print("Master robot is not connected.")

    # 로봇 연결 대수 체크
    def get_connected_robots_number(self) -> int:
        self.start_check()
        return self.ReaderThreadInstance.connected_robots_number

    # 완전 연결 체크
    def is_full_connect(self) -> bool:
        self.start_check()
        is_full_connect_flag = self.ReaderThreadInstance.is_full_connect
        if not is_full_connect_flag:
            PingPongThread._play_once_flag = True # play_once용
        return is_full_connect_flag

    # 완전 연결까지 기다림
    def wait_until_full_connect(self) -> None:
        self.start_check()
        while not self.is_full_connect():
            pass
        time.sleep(1)

    # 한 번만 동작
    _play_once_flag = True
    def play_once(self):
        if not self.is_full_connect():
            #print("full")
            #PingPongThread._play_once_flag = True
            return False
        else:
            if PingPongThread._play_once_flag:
                #print("flag1")
                PingPongThread._play_once_flag = False
                time.sleep(1)
                return True
            else:
                return False

    # 모터 동작
    def run_motor(self, cube_ID: int, speed: float or int) -> None:
        self.start_check()

        if cube_ID != 'all':
            Utils().integer_check(cube_ID, 'all')
            cube_ID = float(cube_ID) # float으로 변환
            if not (1 <= cube_ID and cube_ID <= 8):
                raise ValueError("Cube ID must be between 1 to 8.")
            elif cube_ID > self.connection_number:
                raise ValueError("Cube ID must be less or equal to connection number.")

        Utils().float_check(speed)
        speed = GenerateProtocol.truncate_speed(self, speed) # truncate speed into -30 to 30 RPM
        
        self.write(GenerateProtocol.SetContinuousSteps_bytes(self, cube_ID, speed))

    '''
    def run_motor_aggregate(self, speed_list) -> None:
        self.start_check()

        if len(speed_list) != self.connection_number:
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

    input1 = PingPongThreadInstance.SetContinuousSteps_bytes(1, 20, pause=True)
    input2 = PingPongThreadInstance.SetContinuousSteps_bytes(2, 30, pause=True)
    input3 = PingPongThreadInstance.SetContinuousSteps_bytes(3, -30, pause=True)

    PingPongThreadInstance.write(PingPongThreadInstance.SetAggregateSteps_bytes(1, input1, input2, input3))
    time.sleep(5)
    PingPongThreadInstance.write(PingPongThreadInstance.SetPauseSteps_bytes(False, 'all'))

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



