from pingpongthread import PingPongThread
import time
import keyboard # keyboard==0.13.4

PingPongThreadInstance = PingPongThread(number=2) # n개 로봇 연결
PingPongThreadInstance.start() # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect() # 전부 연결될 때까지 기다림

while not keyboard.is_pressed("q"): # q가 눌리기 전까지 쓰레드 유지
    pass

PingPongThreadInstance.end() # 쓰레드 종료