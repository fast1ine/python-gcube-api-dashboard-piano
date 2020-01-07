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
                not_found_flag = True

    def connect_serial_URL(self, port) -> serial:
        try:
            ser = serial.serial_for_url(port, baudrate=115200, timeout=None) # baurate 9600 does not work.
            return ser
        except:
            return None

    # 실수 체크
    def float_check(self, number) -> None:
        try:
            number = list(number)
        except:
            number = [number]

        for i in range(len(number)):
            try: 
                float(number[i])
            except:
                raise ValueError("Please enter float number!")

    #  정수 체크
    def integer_check(self, number, option=None) -> None:
        self.float_check(number)

        try:
            number = list(number)
        except:
            number = [number]

        for i in range(len(number)):
            if not float(number[i]).is_integer():
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
    def int_to_hex_n_bytes(self, number, n_bytes) -> list:
        hex_number = hex(number)[2:]
        if len(hex_number)%(2*n_bytes) == 0:
            pass
        else:
            hex_number = "0"*(2*n_bytes-len(hex_number)%(2*n_bytes)) + hex_number
        
        #print(hex_number)
        if len(hex_number) > 2*n_bytes:
            raise ValueError("n_bytes is smaller than integer to hex.")

        hex_list = [int(hex_number[-2:], 16)]
        #hex_list_str = [hex_number[-2:]]
        for i in range(1, n_bytes):
            hex_list =  [int(hex_number[-2*(i+1):-2*i], 16)] + hex_list
            #hex_list_str =  [hex_number[-2*(i+1):-2*i]] + hex_list_str
        #print(hex_list_str)
        return hex_list

    def RPM_to_SPS(self, RPM) -> float:
        if 3 <= RPM and RPM <= 30:
            SPS = 50*(-60/RPM+22)
        elif -30 <= RPM and RPM <= -3:
            SPS = 50*(-60/RPM-22)
        elif RPM == 0:
            SPS = 0
        else:
            SPS = None
        #RPM = SPS
        return SPS # -30 to 30, -3 to 3?
        




    input_flag = False

    def input(self, string):
        Utils.input_flag = True

    def print(self, string):
        pass
        

    
