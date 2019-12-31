# Environment: Windows x64, Python x64 3.6.6
# pyserial==3.4

from serialprotocol import Protocol, ReaderThread
from utils import Utils
from processprotocol import ProcessProtocol
import sys
import time
import serial

# 프로토콜
class rawProtocol(Protocol, ProcessProtocol):
    def __init__(self):
        self.init_buffer()
        self.set_timeout()
        self.is_robot_connect = False

    # 버퍼 초기화
    def init_buffer(self):
        self.buffer = b""
        self.buffer_size = 8096
    
    # 타임아웃 시간 정하기
    def set_timeout(self, sec=1):
        self.timeout = sec
            
    # 연결 시작시 발생
    def connection_made(self, transport):
        self.transport = transport
        self.running = True
        print("Serial connected.")

    # 연결 종료시 발생
    def connection_lost(self, exc):
        try:
            self.transport.serial.close() # serial 연결 종료
        except:
            pass
        print("Serial disconnected. Sleep 3 seconds.")
        time.sleep(3)

    #데이터가 들어오면 이곳에서 처리함.
    def data_received(self, data):
        if self.buffer == b"":
            self.previous_time = time.time()
        else:
            if time.time()-self.previous_time > self.timeout: # 타임아웃
                print("p",self.previous_time)
                print("t",time.time())
                self.init_buffer()
                print("Timeout. Initialize buffer.")

        self.buffer += data
        if len(self.buffer) == 9 and self.buffer[7] == 0: # 버퍼 사이즈 계산
            self.buffer_size = self.buffer[8]
        elif len(self.buffer) == 9 and self.buffer[7] != 0:
            print("Error. buffer[7]:", self.buffer[7])
        
        if len(self.buffer) == self.buffer_size: # 버퍼 얻음
            print("Buffer:", Utils().bytes_to_hex_str(self.buffer))  
            self.is_robot_connect = self.process_data(self.buffer, self.buffer_size, self.transport, self.is_robot_connect) # 데이터 처리 및 명령
            self.init_buffer() # 버퍼 초기화
            
    # 데이터 보낼 때 함수
    def write(self, data):
        if self.running:
            self.transport.write(data)
            #print("Write data:", Utils().bytes_to_hex_str(data))
        else:
            print("Not running.")
        
    # 종료 체크
    def isDone(self):
        return self.running

class PingpongThread():
    is_instance = False
    is_start = False
    def __init__(self, number):
        if PingpongThread.is_instance:
            print("PingpongThread instance cannot be constructed above 1.")
            print("Exit program.")
            sys.exit()
        self.PORT = Utils().findBluetoothDongle()
        PingpongThread.is_instance = True

    def __del__(self):
        self.end()

    # 쓰레드 시작
    def start(self):
        if PingpongThread.is_start:
            print("PingpongThread instance cannot start above 1.")
            print("Exit program.")
            sys.exit()
        self.connectRobotThread_instance = self.connectRobotThread(self.PORT, 2)
        self.connectRobotThread_instance.start()
        PingpongThread.is_start = True
    
    # 쓰레드 종료
    def end(self):
        if self.connectRobotThread_instance:
            self.connectRobotThread_instance.close()
            print("End thread.")
            self.connectRobotThread_instance = None
        else:
            print("No instance of connectRobotThread! Please start() before end the thread.")
        PingpongThread.is_instance = False
        PingpongThread.is_start = False

    # 로봇 연결
    def connectRobotThread(self, port, number):
        ser = None
        while True:
            ser = Utils().connectSerialURL(self.PORT)
            if ser:
                break
            else:
                print("Connection Error. Please connect the Bluetooth USB, or shut down other port connected program.")
                print("Sleep 3 seconds.")
                time.sleep(3)

        self.serial_input = Utils().PingPongG2_connect_bytes
        ReaderThreadInstance = ReaderThread(ser, rawProtocol)
        ReaderThreadInstance.write(self.serial_input)
        return ReaderThreadInstance


PingpongThreadInstance = PingpongThread(2)
PingpongThreadInstance.start()

time.sleep(2)

#PingpongThreadInstance.start()
#pingpongThreadInstance.end()

#pingpongThreadInstance = pingpongThread(2)
#pingpongThreadInstance.start()

while True:
    #print("Thread working... (5 sec.)")
    time.sleep(5)



