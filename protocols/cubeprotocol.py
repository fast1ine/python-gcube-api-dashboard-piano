import serial

class CubeProtocol():
    def __init__(self, number):
        self.connection_number = number

    def _set_discovery_group(self, hexlist, discovery_group):
        ### set discovery group ID (1 to 8?)
        if discovery_group == None:
            hexlist[2] = 0xFF
        else:
            hexlist[2] = discovery_group
        return hexlist
    
    def _set_cube_ID(self, hexlist, cube_ID):
        ### set cube ID 
        hexlist[3] = cube_ID
        return hexlist

    def _set_connection_number_motor(self, hexlist):
        ### set connection number
        hexlist[4] = self.connection_number*16 
        return hexlist

    def SetMultiroleAggregator_bytes(self):
        SetMultiroleAggregator_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x00, 0xAA, 0xAF]
        pass

    def GetSensors_bytes(self, cube_ID, action_method, get_method, discovery_group):
        hexlist = [0xFF, 0xFF, 0xFF, 0x00, 0x00, 0xC8, 0xB8, 0x00, 0x0B, 0x00, 0x00]
        ### set discovery group
        hexlist = self._set_discovery_group(hexlist, discovery_group)
        ### set cube ID
        hexlist = self._set_cube_ID(hexlist, cube_ID)
        ### set action method (0 -> single or stop sampling, 2 to 10 -> sample period 0.2s to 1.0s)
        hexlist[9] = action_method
        ### set get method (0 -> default, 1 -> 8bit real)
        hexlist[10] = get_method
        return bytes(hexlist)