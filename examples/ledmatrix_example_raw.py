from example_base import GetParentPath # 상위 폴더 경로 가져오기
from pingpongthread import PingPongThread
import time

PingPongThreadInstance = PingPongThread(number=1)   # 1개 로봇 연결
PingPongThreadInstance.start()                      # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect()    # 전부 연결될 때까지 기다림

time.sleep(2)

if False:
    ### write a pixel
    PingPongThreadInstance.write( \
        PingPongThreadInstance._GenerateProtocolInstance.ArduinoI2CLEDMatrixWritePixel_bytes( \
            0, 0, 0, True, discovery_group=None))
    time.sleep(2)

if True:
    ### write a picture
    PingPongThreadInstance.write( \
        PingPongThreadInstance._GenerateProtocolInstance.ArduinoI2CLEDMatrixWritePicture_bytes( \
            0, [0, 0, 0, 0, 0, 0, 0, 1], discovery_group=None))
    time.sleep(2)

if False:
    ### write a string
    PingPongThreadInstance.write( \
        PingPongThreadInstance._GenerateProtocolInstance.ArduinoI2CLEDMatrixWriteString_bytes( \
            0, 1, "stringssstringss", discovery_group=None))
    time.sleep(10)

if False:
    ### set brightness (밝기 변경이 제대로 안 되는 듯.)
    PingPongThreadInstance.write( \
        PingPongThreadInstance._GenerateProtocolInstance.ArduinoI2CLEDMatrixSetBrightness_bytes( \
            0, 5, discovery_group=None))
    time.sleep(2)

if False:
    ### set blink rate
    PingPongThreadInstance.write( \
        PingPongThreadInstance._GenerateProtocolInstance.ArduinoI2CLEDMatrixSetBlinkRate_bytes( \
            0, 2, discovery_group=None))
    time.sleep(10)



### turn off the led matrix (SetDisplay not working well)
PingPongThreadInstance.write( \
    PingPongThreadInstance._GenerateProtocolInstance.ArduinoI2CLEDMatrixSetDisplay_bytes( \
        0, 0, discovery_group=None))
time.sleep(1)