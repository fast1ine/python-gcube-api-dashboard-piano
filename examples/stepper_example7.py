import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))) # 상위 폴더 경로 가져오기

from pingpongthread import PingPongThread
import keyboard # keyboard==0.13.4

PingPongThreadInstance = PingPongThread(number=2) # n개 로봇 연결
PingPongThreadInstance.start() # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect() # 전부 연결될 때까지 기다림

cube_ID = "all" # 큐브 번호
motor_speed = 30 # 모터 속도 RPM

while not keyboard.is_pressed("q"):
    if keyboard.is_pressed("up"):
        PingPongThreadInstance.run_motor(cube_ID, [30, 30]) # 모터 돌림 (컨티뉴 모드)
    elif keyboard.is_pressed("down"):
        PingPongThreadInstance.run_motor(cube_ID, [-30, -30]) # 모터 돌림 (컨티뉴 모드)
    elif keyboard.is_pressed("space"):
        PingPongThreadInstance.run_motor(cube_ID, [0, 0]) # 모터 돌림 (컨티뉴 모드)

motor_speed = "stop"
PingPongThreadInstance.run_motor(cube_ID, motor_speed) # 모터 끔
PingPongThreadInstance.end() # 쓰레드 종료

