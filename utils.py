import serial.tools.list_ports

class Utils():
    byteslist = [0xFF, 0xFF, 0x00, 0xFF, 0x20, 0x00, 0xAD, 0x00, 0x0B, 0x0A, 0x00]
    serial_input = serial.to_bytes(byteslist)

    # insert bewtween string
    def insert_str(self, string, str_to_insert, index):
        return string[:index] + str_to_insert + string[index:]

    # hex into spaced & upper string
    def bytes_to_hex_str(self, byteinput):
        stroutput = byteinput.hex()
        for i in range(int(len(str(byteinput.hex()))/2-1)):
            stroutput = self.insert_str(stroutput, " ", 3*i+2)
        stroutput = stroutput.upper()
        return stroutput

    # 포트 찾기
    def findBluetoothUSB(self):
        port_flag = False
        #is_serial_connect = False
        PORT = ""
        while not PORT:
            ports = list(serial.tools.list_ports.comports())
            port_len = len(ports)
            for i in range(port_len):
                p = ports[i]
                if "Silicon Labs CP210x USB to UART Bridge" in p.description:
                    print("Found device: " + str(p.description))
                    PORT = str(p.device)
                    port_flag = True
                    return PORT
                if i == port_len-1 and port_flag == False:
                    print("Device not found. Please connect the serial port.")
                    port_flag = "NotFound"
            #is_serial_connect = port_flag == True

    def connectSerialURL(self, port):
        try:
            ser = serial.serial_for_url(port, baudrate=115200, timeout=None) # baurate 9600 does not work.
            return ser
        except:
            return None
        

    
