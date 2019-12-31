import serial.tools.list_ports

class Utils():
    #DD DD DD DD 00 01 DA 00 0B 00 0D
    PingPongDongle_connect_hexlist = [0xDD, 0xDD, 0xDD, 0xDD, 0x00, 0x01, 0xDA, 0x00, 0x0B, 0x00, 0x0D]
    PingPongDongle_connect_bytes = serial.to_bytes(PingPongDongle_connect_hexlist)

    #FF FF 00 FF 20 00 AD 00 0B 0A 00
    PingPongG2_connect_hexlist = [0xFF, 0xFF, 0x00, 0xFF, 0x20, 0x00, 0xAD, 0x00, 0x0B, 0x0A, 0x00]
    PingPongG2_connect_bytes = serial.to_bytes(PingPongG2_connect_hexlist)

    # insert bewtween string
    def insert_str(self, string, str_to_insert, index):
        return string[:index] + str_to_insert + string[index:]

    # hex into spaced & upper string
    def bytes_to_hex_str(self, bytesinput):
        stroutput = bytesinput.hex()
        for i in range(int(len(str(bytesinput.hex()))/2-1)):
            stroutput = self.insert_str(stroutput, " ", 3*i+2)
        stroutput = stroutput.upper()
        return stroutput

    # 포트 찾기
    def findBluetoothDongle(self):
        not_found_flag = False
        PORT = ""
        while not PORT:
            ports = list(serial.tools.list_ports.comports())
            port_len = len(ports)
            for i in range(port_len):
                p = ports[i]
                try:
                    ser = serial.serial_for_url(str(p.device), baudrate=9600, timeout=0, write_timeout=0.5) # 9600으로 한 번 보내기
                    ser.write(self.PingPongDongle_connect_bytes)
                    ser.close()
                    ser = serial.serial_for_url(str(p.device), baudrate=115200, timeout=2, write_timeout=0.5)
                    ser.write(self.PingPongDongle_connect_bytes)
                    data = ser.read(11)
                    #print(data)
                    ser.close()
                    if data == self.PingPongDongle_connect_bytes:
                        print("Found device: " + str(p.description))
                        PORT = str(p.device)
                        return PORT
                    elif data == b"":
                        print("PingPongDongle_connect_bytes timeout.")
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

    def connectSerialURL(self, port):
        try:
            ser = serial.serial_for_url(port, baudrate=115200, timeout=None) # baurate 9600 does not work.
            return ser
        except:
            return None
        

    
