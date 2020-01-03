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
            self.PORT = Utils().find_bluetooth_dongle(GenerateProtocol.PingPongDongle_connect_bytes) # 동글 포트 찾기
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
                    self.PORT = Utils().find_bluetooth_dongle(super().PingPongDongle_connect_bytes)
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
        if PingPongThread.is_start and self.is_robot_connect():
            self.ReaderThreadInstance.write(super(GenerateProtocol).PingPong_disconnect_bytes)
            print("Disconnect master robot.")
        else:
            raise ValueError("PingpongThread is not started. Cannot operate the function.")
            
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
        if 1 <= number and number <= 8: # 1개 이상 8개 이하 
            self.connection_number = number # 연결할 로봇 대수
            try:
                self.ReaderThreadInstance.connection_number = self.connection_number
            except:
                pass
        else:
            raise ValueError("PingPong robot can connect only with 1 to 8 robots.")

    def run_motor(self, cube_ID, speed) -> None:
        self._write(super().PingPong_stepper_bytes(cube_ID, speed))



def main():
    PingPongThreadInstance = PingPongThread()
    PingPongThreadInstance.start()
    PingPongThreadInstance.wait_until_full_connect()

    PingPongThreadInstance.run_motor(1, 20)

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



