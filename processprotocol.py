import time

class ProcessProtocol():
    def __init__(self):
        pass

    def process_data(self, buffer, buffer_size, transport, is_robot_connect):
        if buffer_size == 11: # master 로봇
            if buffer[6] == int(0xAD):
                print("Connected with a master robot.") # 로봇 연결
                return True
            elif buffer[9] == int(0xC0):
                if is_robot_connect:
                    print("Disconnected with a master robot. Sleep 2 seconds.") # 로봇 연결 해제    
                    transport.serial.close() # 시리얼 닫음
                    time.sleep(2) # sleep 2 seconds
                    transport.reconnect() # 재연결
                return False
        elif buffer_size == 18: # slave 로봇
            if buffer[6] == int(0xAD) and buffer[10] == 0:
                for i in range(8):
                    if buffer[10+i] == 15:
                        print("Connected robots:", i) # (i-1)대 slave 로봇 연결
                        return True
                    if i == 7:
                        print("Connected robots: 8")# 7대 slave 로봇 연결
                        return True
        else:
            print("buffer_size:", buffer_size)
            return is_robot_connect