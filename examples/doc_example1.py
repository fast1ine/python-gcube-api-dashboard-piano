from pingpongthread import PingPongThread

PingPongThreadInstance = PingPongThread(number=1)   # 1개 로봇 연결
PingPongThreadInstance.start()                      # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect()    # 전부 연결될 때까지 기다림

PingPongThreadInstance.run_motor()  # 모터 회전
PingPongThreadInstance.wait(5)      # 5초 동안 기다림

PingPongThreadInstance.stop_motor() # 모터 끔
PingPongThreadInstance.end()        # 쓰레드 종료

