import time
from utils import Utils

class ProcessProtocol():
    def __init__(self):
        self.buffer = b""
        self.buffer_size = 0
        self.is_full_connect = False
        self.robot_disconnect_flag = False
        self.transport = None

    # 연결 평가
    def evaluate_connection(self, discovery_group=None) -> None: # is_full_connect, connected_robots_number, robot_disconnect_flag
        connection_number = self.transport._robot_status[discovery_group].controller_status.connection_number
        connected_robots_number = self.transport._robot_status[discovery_group].processed_status.connected_number
        if not self.is_full_connect and connected_robots_number == connection_number: # 모두 연결
            print("Fully connected.") 
            ### 설정
            self.is_full_connect = True
        elif connected_robots_number != connection_number and not self.robot_disconnect_flag: # 전부 연결되지 않았을 때 & disconnect가 아닐 때
            #print(self.connected_robots_number)
            #print(self.transport.connection_number)
            if self.is_full_connect and connected_robots_number != 0: # 이전에 전부 연결되었다면 & 마스터가 끊어진 것이 아니라면
                print("Robot disconnected after full connection. Close all connection.") # 모두 연결 이후에 슬레이브 로봇 연결이 끊어지면 다시 연결이 안됨.
                self.transport.serial.close() # 시리얼 닫음 (transport의 close 함수를 사용하면 작동이 안 됨.)
                self.transport.reconnect()
                ### 설정
                self.is_full_connect = False
                self.transport._robot_status[discovery_group].controller_status.connection_number = 0
            else:
                ### 설정
                self.is_full_connect = False
        elif connected_robots_number != connection_number and self.robot_disconnect_flag: # 전부 연결되지 않았을 때 & disconnect일 때
            # 시리얼 안 닫음.
            print("Disconnect master robot.")
            ### 설정
            self.is_full_connect = False
            self.transport._robot_status[discovery_group].controller_status.connection_number = 0
            self.robot_disconnect_flag = False
        else: # 아무것도 아니면 그대로 내보냄
            pass

    # OP 코드 처리
    def process_data(self, discovery_group=None) -> dict:
        OP_code = self.buffer[6]
        if OP_code == 0xDA: # 1개 연결
            return self._robot_connection_1(discovery_group)
        elif OP_code == 0xAD: # 2개 이상 연결
            return self._robot_connection_1up(discovery_group)
        elif OP_code == 0xCA: # 스케줄 설정
            return self._stepper_schedule()
        elif OP_code == 0xCB: # 포인트 설정
            return self._stepper_point()
        else:
            return self._unregistered()

    def _unregistered(self) -> int:
        #print("Operation is not registered.")
        return {}

    def _robot_connection_1(self, discovery_group=None) -> int:
        connection_number = self.transport._robot_status[discovery_group].controller_status.connection_number
        connected_robots_number = self.transport._robot_status[discovery_group].processed_status.connected_number
        if len(self.buffer) == 11:
            if connection_number == 1 and self.buffer[9] != 0xC0:
                print("Connected with a master robot.") # 로봇 연결
                self.transport._robot_status.processed_status.MAC_address = self.buffer[0:2]
                return {"robot_number": 1}
            elif self.buffer[9] == 0xC0: # 연결 해제
                if connected_robots_number > 0: # 이미 연결된 로봇이 있음
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

    def _robot_connection_1up(self, discovery_group=None) -> int:
        connection_number = self.transport._robot_status[discovery_group].controller_status.connection_number
        if connection_number > 1:
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
            #cube_ID = self.buffer[3]
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
        