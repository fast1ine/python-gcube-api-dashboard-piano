from pingpongthread import PingPongThread

PingPongThreadInstance = PingPongThread(number=2)   # 2개 로봇 연결
PingPongThreadInstance.start()                      # 쓰레드 시작
PingPongThreadInstance.wait_until_full_connect()    # 전부 연결될 때까지 기다림

cube_ID = "all"                 # 모든 모터 선택
speed = [[30, -20], [30, -20]]  # 속도 스케줄. 1번 큐브 30RPM, -20RPM, 2번 큐브 30RPM, 20RPM
cycle = [[2, 1], [1, 2]]        # 회전 스케줄. 1번 큐브 2바퀴, 1바퀴, 2번 큐브 1바퀴, 2바퀴

PingPongThreadInstance.run_motor(cube_ID, 
    speed, 
    cycle, 
    run_option="schedule", 
    wait="schedule")    # 모터 회전, 스케줄이 끝날 때까지 기다림

PingPongThreadInstance.stop_motor() # 모터 끔
PingPongThreadInstance.end()        # 쓰레드 종료

