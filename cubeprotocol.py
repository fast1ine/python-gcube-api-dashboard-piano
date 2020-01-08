import serial
from utils import Utils

class CubeProtocol():
    def __init__(self):
        pass

    def SetMultiroleAggregator_bytes(self):
        SetMultiroleAggregator_hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x00, 0xAA, 0xAF]
        pass