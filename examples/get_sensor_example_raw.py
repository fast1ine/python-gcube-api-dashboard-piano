from example_base import GetParentPath
from pingpongthread import PingPongThread
import time

PingPongThreadInstance = PingPongThread(number=1)   # 1개 로봇 연결
PingPongThreadInstance.start()                      # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect()    # 전부 연결될 때까지 기다림

time.sleep(2)

if True:
    ### write a pixel
    PingPongThreadInstance.write(
        PingPongThreadInstance._GenerateProtocolInstance.GetSensors_bytes(0, action_method=100, discovery_group=None))
    while True:
        time.sleep(360) # pass하면 오류나서 밀림.

