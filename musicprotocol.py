import serial
from utils import Utils

class MusicProtocol():
    def __init__(self):
        pass

    def SetMusicNotesInAction_set_bytes(self):
        SetMusicNotesInAction_set_hexlist = [0xAA, 0xAA, 0x00, 0xAA, 0x10, 0xA2, 0xE8, 0x00, 0x0B, 0x00, 0x00]
        pass

    def SetMusicNotesInAction_play_bytes(self):
        pass