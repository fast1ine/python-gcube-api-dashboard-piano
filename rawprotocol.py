from serialprotocol import Protocol
from utils import Utils
from processprotocol import ProcessProtocol
import time

# 프로토콜
class rawProtocol(Protocol, ProcessProtocol):
    def __init__(self):
        self.init_buffer()
        self.set_timeout()
        self.is_robot_connect = False
        self.connected_robots_number = 0 # 연결된 로봇 개수

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
            self.is_robot_connect, self.connected_robots_number = \
                self.process_data(self.buffer, \
                    self.buffer_size, \
                    self.transport, \
                    self.is_robot_connect, \
                    self.connected_robots_number) # 데이터 처리 및 명령
            self.init_buffer() # 버퍼 초기화

            if self.connected_robots_number == self.transport.connection_number:
                print("Fully connected.")
            
    # 데이터 보낼 때 함수
    def write(self, data):
        if self.running:
            self.transport.write(data)
            #print("Write data:", Utils().bytes_to_hex_str(data))
        else:
            print("Not running.")
        
    # 종료 체크
    def is_done(self):
        return self.running