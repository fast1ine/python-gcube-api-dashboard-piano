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
                        print("PingPongDongle_connect_bytes timeout. (1 secs.)")
                        print('data = b""')
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
                not_found_flag = True

    def connect_serial_URL(self, port) -> serial:
        try:
            ser = serial.serial_for_url(port, baudrate=115200, timeout=None) # baurate 9600 does not work.
            return ser
        except:
            return None

    #  정수 체크
    def integer_check(self, number, option=None) -> None:
        try: 
            if not float(number).is_integer():
                is_integer = False
            else:
                is_integer = True
        except:
            is_integer = False

        if not is_integer:
            if option:
                raise ValueError("Please enter integer number, or '" + str(option) + "'!")
            else:
                raise ValueError("Please enter integer number!")

    # 실수 체크
    def float_check(self, number) -> None:
        try: 
            float(number)
        except:
            raise ValueError("Please enter float number!")
    
    # unsigned16 으로 변환
    def unsigned16(self, n):
        return n & 0xFFFF # "bitwise and" 연산자




    input_flag = False

    def input(self, string):
        Utils.input_flag = True

    def print(self, string):
        pass
        

    
