from pingpongthread import PingPongThread

PingPongThreadInstance = PingPongThread(number=2)   # 2개 로봇 연결
PingPongThreadInstance.start()                      # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect()    # 전부 연결될 때까지 기다림

cube_ID = "all"     # 모든 모터 선택
speed = [30, -20]   # 1번 큐브 시계 방향 30RPM, 2번 큐브 반시계 방향 20RPM

PingPongThreadInstance.run_motor(cube_ID, speed)    # 모터 회전
PingPongThreadInstance.wait(5)                      # 5초 동안 기다림

PingPongThreadInstance.stop_motor() # 모터 끔
PingPongThreadInstance.end()        # 쓰레드 종료

