from serialprotocol import Protocol
from utils import Utils
from processprotocol import ProcessProtocol
from generateprotocol import GenerateProtocol
import time

# 프로토콜
class rawProtocol(Protocol, ProcessProtocol):
    def __init__(self):
        self.init_buffer()
        self.set_timeout()
        self.connected_robots_number = 0 # 연결된 로봇 개수
        self.is_full_connect = False
        self.robot_disconnect_flag = False
        ProcessProtocol.__init__(self)

    # 버퍼 초기화
    def init_buffer(self) -> None:
        self.buffer = b""
        self.buffer_size = 0
        ProcessProtocol.set_buffer(self, b"")

    def add_buffer(self, data):
        self.buffer += data
        ProcessProtocol.set_buffer(self, self.buffer)
    
    # 타임아웃 시간 정하기
    def set_timeout(self, sec=1) -> None:
        self.timeout = sec

    # 로봇 연결 수 설정
    def set_connected_robots_number(self, number: int) -> None:
        self.transport.connected_robots_number = self.connected_robots_number = number # transport에도 설정
        ProcessProtocol.set_connected_robots_number(self, number)
        
    # 모두 연결 설정
    def set_is_full_connect(self, TF: bool) -> None:
        self.transport.is_full_connect = self.is_full_connect = TF # transport에도 설정
        ProcessProtocol.set_is_full_connect(self, TF)

    # 로봇 연결 해제 설정
    def set_robot_disconnect_flag(self, TF: bool) -> None:
        self.robot_disconnect_flag = TF
        ProcessProtocol.set_robot_disconnect_flag(self, TF)

    # 연결 시작시 발생
    def connection_made(self, transport) -> None:
        self.transport = transport
        ProcessProtocol.set_transport(self, transport)
        self.running = True
        print("Serial connected.")

    # 연결 종료시 발생
    def connection_lost(self, exc) -> None:
        self.set_connected_robots_number(0)
        self.set_is_full_connect(False)
        try:
            self.transport.serial.close() # serial 연결 종료
        except:
            pass
        print("Serial disconnected. Sleep 3 seconds.")
        #raise exc
        time.sleep(3)

    #데이터가 들어오면 이곳에서 처리함.
    def data_received(self, data) -> None:
        if self.buffer == b"":
            self.previous_time = time.time()
        elif time.time()-self.previous_time > self.timeout: # 타임아웃
            print("Timeout. Initialize buffer.")
            print("Timeout buffer:", Utils().bytes_to_hex_str(self.buffer))
            self.init_buffer()
            self.previous_time = time.time()
            
        self.add_buffer(data) # 버퍼 받기
        if len(self.buffer) == 9: # 버퍼 사이즈 계산
            self.buffer_size = int(hex(self.buffer[7])[2:] + hex(self.buffer[8])[2:], 16)
        
        if len(self.buffer) == self.buffer_size: # 버퍼 얻음
            print("Buffer:", Utils().bytes_to_hex_str(self.buffer))  
            self.set_connected_robots_number(self.process_data()) # 데이터 처리 및 명령
            self.init_buffer() # 버퍼 초기화
            fu, co, di = self.evaluate_connection() # 연결 평가
            self.set_is_full_connect(fu)
            self.set_connected_robots_number(co) 
            self.set_robot_disconnect_flag(di) 
            
    # 데이터 보낼 때 함수
    def write(self, data) -> None:
        if self.running:
            self.transport.write(data)
            #print("Write data:", Utils().bytes_to_hex_str(data))
        else:
            print("Not running.")
        
    # 종료 체크
    def is_done(self) -> bool:
        return self.running