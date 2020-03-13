from protocols.generateprotocol import GenerateProtocol

class ServoOperation():
    def __init__(self, number, robot_status, start_check, write):
        self._GenerateProtocolInstance = GenerateProtocol(number)
        self._robot_status = robot_status
        self._start_check_copy = start_check
        self._write_copy = write
        
    