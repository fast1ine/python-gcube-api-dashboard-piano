class A():
    def __init__(self):
        self.a = 3

class B(A):
    def __init__(self):
        A.__init__(self)
        self.b = 4

class C(B):
    def __init__(self):
        B.__init__(self)
        self.c = 6
    
    def return_a(self):
        return self.a

CInstance = C()
print(CInstance.a)
CInstance.a = 7
print(CInstance.return_a())