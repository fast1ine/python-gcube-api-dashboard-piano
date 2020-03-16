import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))) # 상위 폴더 경로 가져오기

from pingpongthread import PingPongThread
import keyboard # keyboard==0.13.4
import time

# ARDUINO PIN: 1번 갈색, 2번 빨간색, 3번 주황색, 4번 없음.

PingPongThreadInstance = PingPongThread(number=1) # n개 로봇 연결
PingPongThreadInstance.start() # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect() # 전부 연결될 때까지 기다림

cube_ID = 1 # 큐브 번호
servo_schedule = [[180, 0, 90, 180]] # 속도 스케줄
servo_duration = 1
start_and_stop_list = [[[0, 2], [1, 3]]]
repeat_list = [[1, 1]]

while not keyboard.is_pressed("q"): # q가 눌리기 전까지 쓰레드 유지
    while PingPongThreadInstance.play_once_full_connect(): # 연결 되어있는 동안, 한 번만 실행
        ### schedule
        PingPongThreadInstance.set_servo_schedule(cube_ID, servo_schedule, servo_duration)
        PingPongThreadInstance.play_servo_schedule(cube_ID, repeat_list, start_and_stop_list=start_and_stop_list)
        print(PingPongThreadInstance.get_robot_status()) # 상태 확인

PingPongThreadInstance.run_motor("all", "stop") # 모터 끔
PingPongThreadInstance.end() # 쓰레드 종료