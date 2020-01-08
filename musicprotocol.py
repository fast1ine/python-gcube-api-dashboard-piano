import serial
from utils import Utils

class MusicProtocol():
    def __init__(self, connection_number):
        self.connection_number = connection_number    

    def _set_discovery_group(self, hexlist, discovery_group):
        ### set discovery group ID (1 to 8)
        if discovery_group == None:
            hexlist[2] = 0xFF
        else:
            hexlist[2] = discovery_group
        return hexlist
    
    def _set_cube_ID(self, hexlist, cube_ID):
        ### set cube ID (1 to 8 -> 0 to 7)
        if str(cube_ID).lower() == 'all':
            hexlist[3] = 0xFF
        else:
            hexlist[3] = int(cube_ID - 1) 
        return hexlist

    def _set_connection_number_music(self, hexlist):
        ### set connection number
        hexlist[4] = self.connection_number*16 
        return hexlist

    def _set_pause(self, hexlist, pause, pause_location):
        ### set pause
        if pause:
            ### pause protocol
            hexlist[pause_location] = 1 
        else:
            ### resume protocol
            hexlist[pause_location] = 2 
        return hexlist

    def SetMusicNotesInAction_SetMusicNotes_bytes(self, cube_ID, pianokey_list, duration_list, rest_list, \
            discovery_group=None, pause=False) -> bytes:
        hexlist = [0xFF, 0xFF, 0x01, 0x00, 0x00, 0xA1, 0xE8, 0x00, 0x0B, 0x00, 0x00]
        ### set discovery group
        hexlist = self._set_discovery_group(hexlist, discovery_group)
        ### set cube ID (1 to 8 -> 0 to 7)
        hexlist = self._set_cube_ID(hexlist, cube_ID)
        ### set pause
        if pause:
            ### pause protocol
            hexlist[10] = 1 
        else:
            ### play protocol
            hexlist[10] = 0
        ### set data size (stepper)
        hexlist[7:9] = Utils().int_to_hexlist(11 + 3*len(pianokey_list), 2)
        ### PianoKeyInEqualTemperedScaleE ?
        #hexlist[9] = 0 
        ### set pianokey, duration, rest
        for i in range(len(pianokey_list)):
            hexlist.append(pianokey_list[i])
            hexlist.append(duration_list[i])
            hexlist.append(rest_list[i])
        return serial.to_bytes(hexlist)

    def SetMusicNotesInAction_AggregateSetMusicNotes_bytes(self, discovery_group, *in_bytes) -> bytes:
        hexlist = [0xAA, 0xAA, 0x01, 0xAA, 0x10, 0xA2, 0xE8, 0x00, 0x0B, 0x00, 0x00]
        ### set discovery group
        hexlist = self._set_discovery_group(hexlist, discovery_group)
        ### set connection number
        hexlist = self._set_connection_number_music(hexlist)
        ### get total data size
        total_length = 0
        for i in range(len(in_bytes)):
            total_length = total_length + len(in_bytes[i])
        ### set total data size
        hexlist[7:9] = Utils().int_to_hexlist(11 + total_length, 2) 
        ### attatch in_bytes
        for i in range(len(in_bytes)):
            hexlist.extend(list(in_bytes[i]))
        return serial.to_bytes(hexlist)
        

    def SetMusicNotesInAction_PlayMusicNotes_bytes(self, cube_ID, play, discovery_group=None) -> bytes:
        hexlist = [0xFF, 0xFF, 0x01, 0x00, 0x00, 0xE8, 0xE8, 0x00, 0x0A, 0x02]
        ### set discovery group
        hexlist = self._set_discovery_group(hexlist, discovery_group)
        ### set cube ID (1 to 8 -> 0 to 7)
        hexlist = self._set_cube_ID(hexlist, cube_ID)
        ### set plat
        if play:
            ### resume (play: 0, resuem: 2 [차이점?])
            hexlist[9] = 2 
        else:
            ### pause
            hexlist[9] = 1
        return serial.to_bytes(hexlist)