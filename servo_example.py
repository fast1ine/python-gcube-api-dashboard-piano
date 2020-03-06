from pingpongthread import PingPongThread
import time

PingPongThreadInstance = PingPongThread(number=1)   # 1개 로봇 연결
PingPongThreadInstance.start()                      # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect()    # 전부 연결될 때까지 기다림

# ARDUINO PIN: 1번 갈색, 2번 빨간색, 3번 주황색, 4번 없음.
# SingleServo
PingPongThreadInstance.write( \
    PingPongThreadInstance._GenerateProtocolInstance.SetSingleServo(1, 0, 1))
time.sleep(5)

# Schedule
PingPongThreadInstance.write( \
    PingPongThreadInstance._GenerateProtocolInstance.SetScheduledSteps_bytes(1, [1000, -1000, 500], [1000, 1000, 1000], discovery_group=None, pause=False, \
        step_type=4, servo_angle_list=[0, 90, 180], servo_angle_timeout_list=[1, 1, 1]))
time.sleep(10)

# Point
PingPongThreadInstance.write( \
    PingPongThreadInstance._GenerateProtocolInstance.SetScheduledPoints_bytes(1, [0, 1], [1, 2], [2, 2], discovery_group=None, \
        pause=False, step_type=4))
time.sleep(10)