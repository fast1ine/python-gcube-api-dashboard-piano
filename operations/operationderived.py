from protocols.generateprotocol import GenerateProtocol
from operations.stepper.stepperoperation import StepperOperation
from operations.servo.servooperation import ServoOperation
from operations.ledmatrix.ledmatrixoperation import LEDMatrixOperation

class OperationDerived(StepperOperation, ServoOperation, LEDMatrixOperation):
    def __init__(self, number, robot_status, start_check, write):
        self._GenerateProtocolInstance = GenerateProtocol(number)
        self._robot_status = robot_status
        self._start_check_copy = start_check
        self._write_copy = write
        StepperOperation.__init__(self, number, robot_status, start_check, write)
        ServoOperation.__init__(self, number, robot_status, start_check, write)
        LEDMatrixOperation.__init__(self, number, robot_status, start_check, write)