import time
from utils import Utils

class ProcessProtocol():
    def __init__(self):
        self.buffer = b""
        self.buffer_size = 0
        self.connected_robots_number = 0
        self.is_full_connect = False
        self.robot_disconnect_flag = False
        self.transport = None

    # 연결 평가
    def evaluate_connection(self) -> (bool, int, bool): # is_full_connect, connected_robots_number, robot_disconnect_flag
        if not self.is_full_connect and self.connected_robots_number == self.transport.connection_number: # 모두 연결
            print("Fully connected.") 
            return True, self.connected_robots_number, self.robot_disconnect_flag
        elif self.connected_robots_number != self.transport.connection_number and not self.robot_disconnect_flag: # 전부 연결되지 않았을 때 & disconnect가 아닐 때
            #print(self.connected_robots_number)
            #print(self.transport.connection_number)
            if self.is_full_connect and self.connected_robots_number != 0: # 이전에 전부 연결되었다면 & 마스터가 끊어진 것이 아니라면
                print("Robot disconnected after full connection. Close all connection.") # 모두 연결 이후에 슬레이브 로봇 연결이 끊어지면 다시 연결이 안됨.
                self.transport.serial.close() # 시리얼 닫음 (transport의 close 함수를 사용하면 작동이 안 됨.)
                self.transport.reconnect()
                return False, 0, self.robot_disconnect_flag
            else:
                return False, self.connected_robots_number, self.robot_disconnect_flag
        elif self.connected_robots_number != self.transport.connection_number and self.robot_disconnect_flag: # 전부 연결되지 않았을 때 & disconnect일 때
            # 시리얼 안 닫음.
            print("Disconnect master robot.")
            return False, 0, False
        else: # 아무것도 아니면 그대로 내보냄
            return self.is_full_connect, self.connected_robots_number, self.robot_disconnect_flag

    # OP 코드 처리
    def process_data(self) -> dict:
        OP_code = self.buffer[6]
        if OP_code == 0xDA: # 1개 연결
            return self._robot_connection_1()
        elif OP_code == 0xAD: # 2개 이상 연결
            return self._robot_connection_1up()
        elif OP_code == 0xCA: # 스케줄 설정
            return self._stepper_schedule()
        elif OP_code == 0xCB: # 포인트 설정
            return self._stepper_point()
        else:
            return self._unregistered()

    def _unregistered(self) -> int:
        #print("Operation is not registered.")
        return {}

    def _robot_connection_1(self, up=False) -> int:
        if len(self.buffer) == 11:
            if self.transport.connection_number == 1 and self.buffer[9] != 0xC0:
                print("Connected with a master robot.") # 로봇 연결
                return {"robot_number": 1}
            elif self.buffer[9] == 0xC0: # 연결 해제
                if self.connected_robots_number > 0: # 이미 연결된 로봇이 있음
                    print("Disconnected with a master robot.") 
                else: # 연결된 로봇이 없음
                    print("Disconnected with previous connection.")
                print("Reconnecting with serial...")
                self.transport.serial.close() # 시리얼 닫음 (transport의 close 함수는 사용하면 작동이 안 됨.)
                time.sleep(2) # sleep 2 seconds
                self.transport.reconnect() # 재연결
                return {"robot_number": 0}
            else:
                return self._unregistered()
        else:
            return self._unregistered()
            
    def _robot_connection_1up(self) -> int:
        if self.transport.connection_number > 1:
            if len(self.buffer) == 11: # 마스터 로봇
                print("Connected with a master robot.") # 로봇 연결
                return {"robot_number": 1}
            elif len(self.buffer) == 18: # 슬레이브 로봇
                for i in range(8):
                    if self.buffer[10+i] == 0x0F:
                        print("Connected robots:", i) # (i-1)대 slave 로봇 연결
                        return {"robot_number": i}
                print("Connected robots: 8")# 7대 slave 로봇 연결
                return {"robot_number": 8}
            else:
                return self._unregistered()
        else:
            return self._unregistered()

    def _stepper_schedule(self) -> None:
        if len(self.buffer) == 15:
            print("Schedule set.")
            return {"schedule_set": True}
        elif len(self.buffer) == 17:
            schedule_idx = Utils().twobyte_hexlist_to_int(self.buffer[13], self.buffer[14])
            play_idx = self.buffer[15]
            repeat_number = self.buffer[16]
            print("Schedule index:", schedule_idx)
            print("Schedule play index:", play_idx)
            print("Schedule repeat number:", repeat_number)
            return {}
        else:
            return self._unregistered
        
    def _stepper_point(self) -> None:
        if len(self.buffer) == 15:
            print("Point set.")
            return {"point_set": True}
        else:
            return self._unregistered
        