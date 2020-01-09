import time

class ProcessProtocol():
    def __init__(self):
        pass

    def process_data(self, 
            buffer, 
            buffer_size, 
            transport, 
            connected_robots_number,
            connection_number) -> (bool, int):
        """return: robot connection, connected robots number"""

        self.buffer = buffer
        self.buffer_size = buffer_size
        self.transport = transport
        self.connected_robots_number = connected_robots_number
        self.connection_number = connection_number

        if self.buffer_size == 11:
            return self._master_robot()
        if self.buffer_size == 18:
            return self._slave_robot()
        else:
            return self._unregistered()

    def _unregistered(self) -> int:
        #print("buffer_size:", self.buffer_size)
        #print("Operation is not registered.")
        return self.connected_robots_number

    def _master_robot(self) -> int: # master 로봇
        if (self.connection_number == 1 and self.buffer[6] == int(0xDA) and self.buffer[9] != int(0xC0))\
            or (self.connection_number > 1 and self.buffer[6] == int(0xAD) and self.buffer[9] != int(0xC0)):
            print("Connected with a master robot.") # 로봇 연결
            return 1
        elif self.buffer[9] == int(0xC0):
            if self.connected_robots_number > 0:
                print("Disconnected with a master robot.") # 로봇 연결 해제    
            else:
                print("Disconnected with previous connection.")
                self.transport.serial.close() # 시리얼 닫음 (transport의 close 함수는 사용하면 작동이 안 됨.)
                time.sleep(2) # sleep 2 seconds
                self.transport.reconnect() # 재연결
            return 0
        else:
            return self._unregistered()
    
    def _slave_robot(self) -> (bool, int): # slave 로봇
        if self.buffer[6] == int(0xAD) and self.buffer[10] == int(0x00):
            for i in range(8):
                if self.buffer[10+i] == 15:
                    print("Connected robots:", i) # (i-1)대 slave 로봇 연결
                    return i
                if i == 7:
                    print("Connected robots: 8")# 7대 slave 로봇 연결
                    return 8
        else:
            return self._unregistered()

    