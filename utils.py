import serial.tools.list_ports

class Utils():
    # insert bewtween string
    def insert_str(self, string, str_to_insert, index) -> str:
        return string[:index] + str_to_insert + string[index:]

    # hex into spaced & upper string
    def bytes_to_hex_str(self, bytesinput) -> str:
        stroutput = bytesinput.hex()
        for i in range(int(len(str(bytesinput.hex()))/2-1)):
            stroutput = self.insert_str(stroutput, " ", 3*i+2)
        stroutput = stroutput.upper()
        return stroutput

    # 포트 찾기
    def find_bluetooth_dongle(self, connect_bytes) -> str:
        not_found_flag = False
        PORT = ""
        while not PORT:
            ports = list(serial.tools.list_ports.comports())
            port_len = len(ports)
            for i in range(port_len):
                p = ports[i]
                try:
                    # 9600으로 한 번 보내기 (이전에 연결 했었다가 다시 115200으로 PingPongDongle_connect_bytes를 보내면 응답을 안 받음.)
                    ser = serial.serial_for_url(str(p.device), baudrate=9600, timeout=0, write_timeout=0.5) 
                    ser.write(connect_bytes)
                    ser.close()
                    ser = serial.serial_for_url(str(p.device), baudrate=115200, timeout=1, write_timeout=0.5)
                    ser.write(connect_bytes)
                    data = ser.read(11)
                    #print(data)
                    ser.close()
                    if data == connect_bytes:
                        print("Found device: " + str(p.description))
                        PORT = str(p.device)
                        return PORT
                    elif data == b"":
                        #print("PingPongDongle_connect_bytes timeout. (1 secs.)")
                        #print('data = b""')
                        pass
                    else:
                        print("What device is this?")
                except:
                    try:
                        ser.close()
                    except:
                        pass
                    #print("something wrong")
            if not_found_flag == False:
                print("Device not found. Please connect the BluetoothUSB, or shut down other port connected program.")
                print("Reconnecting serial...")
                not_found_flag = True

    # 시리얼 연결
    def connect_serial_URL(self, port) -> serial:
        try:
            ser = serial.serial_for_url(port, baudrate=115200, timeout=None) # baurate 9600 does not work. baudrate is 115200.
            return ser
        except:
            return None

    # 실수 체크
    def float_check(self, number, option=None) -> None:
        if not (isinstance(number, int) or isinstance(number, float)):
            is_float = False
        else:
            is_float = True
        if not is_float:
            if option:
                raise ValueError("Please enter float number, or '" + str(option) + "'!")
            else:
                raise ValueError("Please enter float number!")

    #  정수 체크
    def integer_check(self, number, option=None) -> None:
        if not isinstance(number, int):
            is_integer = False
        else:
            is_integer = True
        if not is_integer:
            if option:
                raise ValueError("Please enter integer number, or '" + str(option) + "'!")
            else:
                raise ValueError("Please enter integer number!")

    # unsigned16 으로 변환
    def unsigned16(self, n) -> int:
        return n & 0xFFFF # "bitwise &(and)" 연산자

    # integer를 n 바이트 헥스 리스트로 변환
    def int_to_hexlist(self, number, n_bytes) -> list:
        hex_number = hex(number)[2:] # str
        if len(hex_number)%(2*n_bytes) != 0:
            hex_number = "0"*(2*n_bytes-len(hex_number)%(2*n_bytes)) + hex_number 
        if len(hex_number) > 2*n_bytes:
            raise ValueError("n_bytes is smaller than integer to hex.")
        hex_list = [int(hex_number[-2:], 16)]
        for i in range(1, n_bytes):
            hex_list =  [int(hex_number[-2*(i+1):-2*i], 16)] + hex_list
        return hex_list

    # 2바이트 헥스 리스트를 integer로 변환
    def twobyte_hexlist_to_int(self, byte1, byte2) -> int:
        return int(hex(byte1)[2:] + hex(byte2)[2:], 16)
    
    # 리스트로 변환
    def to_list(self, input_data) -> list:
        if isinstance(input_data, list) or isinstance(input_data, tuple):
            return list(input_data)
        elif isinstance(input_data, int) or isinstance(input_data, float) \
        or isinstance(input_data, str) or isinstance(input_data, bool) or input_data == None:
            return [input_data]
        else:
            raise ValueError("Error. Enter list, or tuple, or int, or float, or str, or bool, or None.")

    # 같은 원소가 있는지 확인
    def check_same_element(self, input_list) -> None:
        for i in range(len(input_list)-1):
            if input_list[i] in input_list[i+1:]:
                raise ValueError("All elements must be different each other in list.")

    # 모든 cube id가 있는지 확인
    def all_cube_in_check(self, input_list, connection_number) -> bool:
        for i in range(connection_number):
            check = (i in input_list) and True
        return check

    input_flag = False

    def input(self, string):
        Utils.input_flag = True

    def print(self, string, option=None):
        print(string)
        

    
