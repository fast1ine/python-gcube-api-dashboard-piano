#################agg
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))) # 상위 폴더 경로 가져오기

from pingpongthread import PingPongThread
import keyboard # keyboard==0.13.4
import time

PingPongThreadInstance = PingPongThread(number=2) # n개 로봇 연결
PingPongThreadInstance.start() # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect() # 전부 연결될 때까지 기다림

cube_ID = [1, 2, 3] # 큐브 번호
speed_schedule_1 = [-1000, 1000, 0, 800, -800] # 속도 스케줄
step_schedule_1 = [2000, 2000, 2000, -500, 500] # 회전 스케줄
speed_schedule_2 = [-1000, 1000, 0, 800, -800]
step_schedule_2 = [2000, 2000, 2000, -500, 500] 
speed_schedule_3 = [-1000, 1000, 0, 800, -800] 
step_schedule_3 = [2000, 2000, 2000, -500, 500] 




while not keyboard.is_pressed("q"): # q가 눌리기 전까지 쓰레드 유지
    while  PingPongThreadInstance.play_once_full_connect(): # 연결 되어있는 동안, 한 번만 실행
        PingPongThreadInstance.set_motor_schedule(cube_ID, speed_schedule, cycle_schedule) # 모터 스케줄 설정
        PingPongThreadInstance.play_motor_schedule(cube_ID, repeat, start_and_stop_list=start_and_stop_points) # 모터 스케줄 실행

PingPongThreadInstance.run_motor("all", "stop") # 모터 끔
PingPongThreadInstance.end() # 쓰레드 종료

