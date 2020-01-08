from pingpongthread import PingPongThread
import time

PingPongThreadInstance = PingPongThread(number=2)
PingPongThreadInstance.start()
PingPongThreadInstance.wait_until_full_connect()

while True:
    while PingPongThreadInstance.play_once():
        print("runrunrunrunrunrunrunrunrunrunrunrunrunrunrunrunrunrunrunrunrunrunrunrunrun")
        PingPongThreadInstance.run_motor('all', 30)