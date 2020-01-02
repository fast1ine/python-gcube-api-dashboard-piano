# Environment: Windows x64, Python x64 3.6.6
# pyserial==3.4

from serialprotocol import ReaderThread
from utils import Utils
from rawprotocol import rawProtocol
import sys
import time
import serial

class PingPongThread():
    is_instance = False
    is_start = False
    def __init__(self, number=2):
        if not PingPongThread.is_instance:
            self.connection_number = number # 연결할 로봇 대수
            PingPongThread.is_instance = True
            self.PORT = Utils().find_bluetooth_dongle()
        else:
            raise ValueError("PingpongThread instance cannot be constructed above 1.")

    def __del__(self):
        try:
            self.ReaderThreadInstance.close()
            print("End thread.")
        except:
            pass

    # 쓰레드 시작
    def start(self):
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
    def end(self):
        if PingPongThread.is_start:
            self.ReaderThreadInstance.close()
            print("End thread.")
            self.ReaderThreadInstance = None
            PingPongThread.is_instance = False
            PingPongThread.is_start = False
        else:
            raise ValueError("Thread did not start! Please start() before end the thread.")
        
    # 로봇 연결 체크
    def is_robot_connect(self):
        return self.ReaderThreadInstance.is_robot_connect()

    # 로봇 연결 대수 체크
    def get_connected_robots_number(self):
        return self.ReaderThreadInstance.get_connected_robots_number()

    # 로봇 연결
    def _connect_robot_thread(self, port):
        if PingPongThread.is_instance:
            ser = None
            while True:
                ser = Utils().connect_serial_URL(self.PORT)
                if ser:
                    break
                else:
                    self.PORT = Utils().find_bluetooth_dongle()
            self.ReaderThreadInstance = ReaderThread(ser, rawProtocol)
            self.ReaderThreadInstance.connection_number = self.connection_number
            self.ReaderThreadInstance.write(Utils().PingPongGn_connect_bytes(self.connection_number))
        else:
            #raise ValueError("No instance of PingpongThread! Please construct instance first.")
            # cannot reach
            print("?")
            pass
    
    # 로봇 연결 해제
    def disconnectMasterRobot(self):
        if PingPongThread.is_start and self.is_robot_connect():
            self.ReaderThreadInstance.write(Utils().PingPong_disconnect_bytes)
            print("Disconnect master robot.")
        else:
            raise ValueError("PingpongThread is not started. Cannot operate the function.")


PingPongThreadInstance = PingPongThread()
PingPongThreadInstance.start()

#PingpongThreadInstance.start()

#PingpongThreadInstance.end()
#PingpongThreadInstance.end()

#pingpongThreadInstance = pingpongThread(2)
#pingpongThreadInstance.start()

while True:
    #print("Thread working... (5 sec.)")
    time.sleep(10)
    #PingpongThreadInstance.disconnectMasterRobot()




