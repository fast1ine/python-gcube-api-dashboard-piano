import sys, os
class GetParentPath():
    def __init__(self):
        sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))) # 상위 폴더 경로 가져오기

GetParentPath()