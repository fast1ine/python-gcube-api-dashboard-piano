from pingpongthread import PingPongThread
import time

PingPongThreadInstance = PingPongThread(number=1)
PingPongThreadInstance.start()
PingPongThreadInstance.wait_until_full_connect()


PingPongThreadInstance.write( \
    PingPongThreadInstance._GenerateProtocolInstance.SetMusicNotesInAction_SetMusicNotes_bytes(1, \
        [56, 54, 52, 54, 56, 56, 56, 54, 54, 54, 56, 59, 59], [25]*13, [0]*13))


while True:
    #print("Thread working... (5 sec.)")
    time.sleep(10)