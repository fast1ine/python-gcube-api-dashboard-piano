import time

import serial
import serial.tools.list_ports


class ConnectionUtils:
    DONGLE_PNP_ID = "VID_1915&PID_C00A&MI_01"

    def find_bluetooth_dongle(self, connect_bytes) -> str:
        warned = False
        while True:
            ports = [
                port for port in serial.tools.list_ports.comports()
                if self.DONGLE_PNP_ID in str(port.hwid).upper()
            ]
            for port in ports:
                ser = None
                try:
                    ser = serial.serial_for_url(
                        str(port.device),
                        baudrate=115200,
                        timeout=1,
                        write_timeout=1,
                        rtscts=True,
                    )
                    ser.write(connect_bytes)
                    data = ser.read(11)
                    if len(data) >= 11 and data[6] == 0xDA and data[10] == 0x0D:
                        print("Found device: " + str(port.description))
                        return str(port.device)
                except Exception:
                    pass
                finally:
                    try:
                        if ser is not None:
                            ser.close()
                    except Exception:
                        pass

            if not warned:
                print("PingPong USB dongle not found or already in use.")
                print("Reconnecting serial...")
                warned = True
            time.sleep(0.5)

    def connect_serial_URL(self, port):
        try:
            return serial.serial_for_url(
                port,
                baudrate=115200,
                timeout=None,
                rtscts=True,
            )
        except Exception:
            return None
