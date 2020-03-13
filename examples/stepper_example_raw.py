from pingpongthread import PingPongThread
import time

PingPongThreadInstance = PingPongThread(number=2)   # 1개 로봇 연결
PingPongThreadInstance.start()                      # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect()    # 전부 연결될 때까지 기다림

### continuous
PingPongThreadInstance.write( \
    PingPongThreadInstance._GenerateProtocolInstance.SetContinuousSteps_bytes(0, 1000, discovery_group=None, pause=False))
time.sleep(0.2)
PingPongThreadInstance.write( \
    PingPongThreadInstance._GenerateProtocolInstance.SetContinuousSteps_bytes(1, -500, discovery_group=None, pause=False))
time.sleep(5)

# Schedule
PingPongThreadInstance.write( \
    PingPongThreadInstance._GenerateProtocolInstance.SetScheduledSteps_bytes(0, [1000, -1000, 500], [1000, 1000, 1000], discovery_group=None, pause=False))
time.sleep(0.2)
PingPongThreadInstance.write( \
    PingPongThreadInstance._GenerateProtocolInstance.SetScheduledSteps_bytes(1, [500, -500, 250], [1000, 1000, 1000], discovery_group=None, pause=False))
time.sleep(10)