from example_base import GetParentPath # 상위 폴더 경로 가져오기
from pingpongthread import PingPongThread
import keyboard # keyboard==0.13.4

PingPongThreadInstance = PingPongThread(number=1) # n개 로봇 연결
PingPongThreadInstance.start() # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect() # 전부 연결될 때까지 기다림

cube_ID = 1 # 큐브 번호
motor_speed = 30 # 모터 속도 RPM

while not keyboard.is_pressed("q"): # q가 눌리기 전까지 쓰레드 유지
    while PingPongThreadInstance.play_once_full_connect(): # 연결 되어있는 동안, 한 번만 실행
        PingPongThreadInstance.run_motor(cube_ID, motor_speed) # 모터 돌림 (컨티뉴 모드)
        print(PingPongThreadInstance.get_robot_status()) # 상태 확인

motor_speed = "stop"
PingPongThreadInstance.run_motor(cube_ID, motor_speed) # 모터 끔
PingPongThreadInstance.end() # 쓰레드 종료

