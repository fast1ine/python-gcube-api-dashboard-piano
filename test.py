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
            self.set_connection_number(number) # 연결할 로봇 대수
            PingPongThread.is_instance = True # 인스턴스 생성 확인
            super().__init__(self.connection_number) # generate protocol init
            self.PORT = Utils().find_bluetooth_dongle(GenerateProtocol.DongleInAction_bytes) # 동글 포트 찾기
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

    # 로봇 연결
    def _connect_robot_thread(self, port) -> None:
        if PingPongThread.is_instance:
            ser = None
            while True:
                ser = Utils().connect_serial_URL(self.PORT)
                if ser:
                    break
                else:
                    self.PORT = Utils().find_bluetooth_dongle(super().DongleInAction_bytes)
            self.ReaderThreadInstance = ReaderThread(ser, rawProtocol)
            self.ReaderThreadInstance.connection_number = self.connection_number
            self.ReaderThreadInstance.write(super().PingPongGn_connect_bytes(self.connection_number))
        else:
            #raise ValueError("No instance of PingpongThread! Please construct instance first.")
            # cannot reach
            print("?")
            pass

    def _write(self, protocol_bytes) -> None:
        try:
            self.ReaderThreadInstance.write(protocol_bytes)
        except:
            print("Cannot write.")
            
    # 로봇 연결 해제
    def disconnect_master_robot(self) -> None:
        self.start_check()
        if self.is_robot_connect():
            self.ReaderThreadInstance.write(super(GenerateProtocol).PingPong_disconnect_bytes)
            print("Disconnect master robot.")
        else:
            print("Master robot is not connected.")
            
    # 로봇 연결 체크
    def is_robot_connect(self) -> bool:
        self.start_check()
        return self.ReaderThreadInstance.is_robot_connect()

    # 로봇 연결 대수 체크
    def get_connected_robots_number(self) -> int:
        self.start_check()
        return self.ReaderThreadInstance.get_connected_robots_number()

    # 완전 연결 체크
    def is_full_connect(self) -> bool:
        self.start_check()
        return self.ReaderThreadInstance.is_full_connect()

    # 완전 연결까지 기다림
    def wait_until_full_connect(self) -> None:
        self.start_check()
        while not self.is_full_connect():
            pass
        time.sleep(1)

    # 연결 숫자
    def set_connection_number(self, number) -> None:
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

    def run_motor(self, cube_ID, speed) -> None:
        self.start_check()

        if cube_ID != 'all':
            Utils().integer_check(cube_ID, 'all')
            cube_ID = float(cube_ID) # float으로 변환
            if not (1 <= cube_ID and cube_ID <= 8):
                raise ValueError("Cube ID must be between 1 to 8.")
        elif cube_ID > self.connection_number:
            raise ValueError("Cube ID must be less or equal to connection number.")

        Utils().float_check(speed)
        speed = super().truncate_speed(speed) # truncate speed into -60 to 60 RPM
        
        self._write(super().SetContinuousSteps_bytes(cube_ID, speed))

    def run_motor_aggregate(self, speed_list) -> None:
        self.start_check()

        if len(speed_list) != self.connection_number:
            raise ValueError("Speed list must be equal to connection number.")

        Utils().float_check(speed_list)
        for i in range(len(speed_list)):
            speed_list[i] = super().truncate_speed(speed_list[i]) # truncate speed into -60 to 60 RPM
        self._write(super().SetAggregateSteps_bytes(1, speed_list))


def main():
    PingPongThreadInstance = PingPongThread(3)
    PingPongThreadInstance.start()
    PingPongThreadInstance.wait_until_full_connect()

    #PingPongThreadInstance.run_motor(1, 20)
    PingPongThreadInstance.run_motor_aggregate([20, 40, 60])

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



