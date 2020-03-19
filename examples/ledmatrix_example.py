import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))) # 상위 폴더 경로 가져오기

from pingpongthread import PingPongThread
import keyboard # keyboard==0.13.4
import time

# ARDUINO PIN: 1번 갈색, 2번 빨간색, 3번 주황색, 4번 없음.

PingPongThreadInstance = PingPongThread(number=1) # n개 로봇 연결
PingPongThreadInstance.start() # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect() # 전부 연결될 때까지 기다림

그림 = [
[0, 0, 0, 0, 0, 0, 0, 0],
[0, 0, 0, 0, 0, 0, 1, 0],
[1, 1, 1, 1, 1, 0, 1, 0],
[0, 0, 0, 1, 0, 0, 1, 0],
[0, 0, 1, 1, 0, 0, 1, 1],
[0, 1, 1, 0, 0, 0, 1, 0],
[1, 1, 0, 0, 0, 0, 1, 0],
[0, 0, 0, 0, 0, 0, 1, 0]]

그림2 = [
[0, 0, 1, 0, 0, 0, 0, 0],
[0, 0, 1, 0, 0, 0, 1, 0],
[1, 1, 1, 1, 1, 0, 1, 0],
[0, 0, 1, 0, 0, 0, 1, 0],
[0, 0, 1, 1, 0, 0, 1, 1],
[0, 1, 0, 0, 1, 0, 1, 0],
[1, 0, 0, 0, 0, 0, 1, 0],
[0, 0, 0, 0, 0, 0, 1, 0]]

while not keyboard.is_pressed("q"): # q가 눌리기 전까지 쓰레드 유지
    while PingPongThreadInstance.play_once_full_connect(): # 연결 되어있는 동안, 한 번만 실행
        ### write a pixel
        PingPongThreadInstance.LED_matrix_clear(1)
        PingPongThreadInstance.LED_matrix_write_pixel(1, 5, 5, True)
        PingPongThreadInstance.LED_matrix_write_pixel(1, 5, 4, True)
        PingPongThreadInstance.LED_matrix_write_pixel(1, 5, 3, True)
        time.sleep(3)
        ### write a string
        PingPongThreadInstance.LED_matrix_clear(1)
        PingPongThreadInstance.LED_matrix_write_string(1, 4, "string string")
        time.sleep(3)
        ### write a picture
        PingPongThreadInstance.LED_matrix_clear(1)
        PingPongThreadInstance.LED_matrix_write_picture(1, 그림)
        time.sleep(3)

PingPongThreadInstance.LED_matrix_clear(1)
PingPongThreadInstance.end() # 쓰레드 종료