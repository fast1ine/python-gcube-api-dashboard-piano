# Environment: Windows x64, Python x64 3.6.6
# pyserial==3.4

from serialprotocol import Protocol, ReaderThread
from utils import bytes_to_hex_str
import sys
import time
import serial.tools.list_ports

# 프로토콜
class rawProtocol(Protocol):
    def __init__(self):
        self.init_buffer()
        self.set_timeout()

    # 버퍼 초기화
    def init_buffer(self):
        self.buffer = b""
        self.buffer_size = 8096
    
    def set_timeout(self, sec=1):
        self.timeout = sec

    # 연결 시작시 발생
    def connection_made(self, transport):
        self.transport = transport
        self.running = True
        print("Serial connected.")

    # 연결 종료시 발생
    def connection_lost(self, exc):
        self.transport = None
        print("Exception occured. Serial disconnected.")

    #데이터가 들어오면 이곳에서 처리함.
    def data_received(self, data):
        if self.buffer == b"":
            self.previous_time = time.time()
        else:
            if time.time()-self.previous_time > self.timeout: # 타임아웃
                self.init_buffer()
                print("Timeout. Initialize buffer.")

        self.buffer += data
        #print("Buffer:", bytes_to_hex_str(self.buffer))
        if len(self.buffer) == 9 and self.buffer[7] == 0: # 버퍼 사이즈 계산
            self.buffer_size = self.buffer[8]
            #print("Get buffer size:", self.buffer[8])
        elif len(self.buffer) == 9 and self.buffer[7] != 0:
            print("Error. buffer[7]:", self.buffer[7])
        if len(self.buffer) == self.buffer_size: # 버퍼 얻음
            print("Buffer:", bytes_to_hex_str(self.buffer))  
            #print(self.buffer)
            #print("Buffer size:", self.buffer_size)  
            if self.buffer_size == 11: # master 로봇
                if self.buffer[6] == int(0xAD):
                    print("Connected with a master robot") # 로봇 연결
                elif self.buffer[9] == int(0xC0):
                    print("Disconnected with a master robot") # 로봇 연결 해제
            elif self.buffer_size == 18: # slave 로봇
                if self.buffer[6] == int(0xAD) and self.buffer[10] == 0:
                    for i in range(8):
                        if self.buffer[10+i] == 15:
                            print("Connected robots:", i) # (i-1)대 slave 로봇 연결
                            break
                        if i == 7:
                            print("Connected robots: 8")# 7대 slave 로봇 연결
            self.init_buffer() # 버퍼 초기화



    # 데이터 보낼 때 함수
    def write(self,data):
        self.transport.write(data)
        print("Write data:", bytes_to_hex_str(data))
        
    # 종료 체크
    def isDone(self):
        return self.running

class pingpong():
    # 포트 찾기
    def connectBluetoothUSB(self):
        self.port_flag = False
        self.PORT = ""
        while not self.PORT:
            ports = list(serial.tools.list_ports.comports())
            port_len = len(ports)
            for i in range(port_len):
                p = ports[i]
                if "Silicon Labs CP210x USB to UART Bridge" in p.description:
                    print("Found device: " + str(p.description))
                    self.PORT = str(p.device)
                    self.port_flag = True
                    break
                if i == port_len-1 and self.port_flag == False:
                    print("Device not found. Please connect the serial port.")
                    self.port_flag = "NotFound"
    
    # 로봇 연결
    def connectRobotThread(self, number):
        self.ser = serial.serial_for_url(self.PORT, baudrate=115200, timeout=None) # baurate 9600 does not work.
        byteslist = [0xFF, 0xFF, 0x00, 0xFF, 0x20, 0x00, 0xAD, 0x00, 0x0B, 0x0A, 0x00]
        self.serial_input = serial.to_bytes(byteslist)

        ReaderThreadInstance = ReaderThread(self.ser, rawProtocol)
        ReaderThreadInstance.write(self.serial_input)
        return ReaderThreadInstance

pingpongInstance = pingpong()
pingpongInstance.connectBluetoothUSB()

# 쓰레드 시작
with pingpongInstance.connectRobotThread(2) as pingpong_thread:
    while pingpong_thread.isDone():
        #if p.serial.timeout:
        #    #p.protocol_factory...
        #    pass

        time.sleep(1)
        #print("Thread waiting...")


        