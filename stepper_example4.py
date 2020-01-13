from pingpongthread import PingPongThread
import keyboard # keyboard==0.13.4
import time

PingPongThreadInstance = PingPongThread(number=1) # n개 로봇 연결
PingPongThreadInstance.start() # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect() # 전부 연결될 때까지 기다림

cube_ID = 1 # 큐브 번호
speed_schedule = [-30, 30, "sleep", 15, -15] # 속도 스케줄
cycle_schedule = [1, 1, 1, 0.5, 0.5] # 회전 스케줄

repeat = 2 # 반복 횟수
start_point = 0 # 시작 인덱스
stop_point = 1 # 멈춤 인덱스

while not keyboard.is_pressed("q"): # q가 눌리기 전까지 쓰레드 유지
    while PingPongThreadInstance.is_full_connect() and PingPongThreadInstance.play_once(): # 연결 되어있는 동안, 한 번만 실행
        PingPongThreadInstance.set_motor_schedule(cube_ID, speed_schedule, cycle_schedule) # 모터 스케줄 설정
        time.sleep(1)
        PingPongThreadInstance.play_motor_schedule(cube_ID, repeat, start_point, stop_point, pause=True) # 모터 스케줄 실행
        time.sleep(1)
        PingPongThreadInstance.play_motor(cube_ID) # 모터 스케줄 실행

PingPongThreadInstance.run_motor("all", "stop") # 모터 끔
PingPongThreadInstance.end() # 쓰레드 종료

