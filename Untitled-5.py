class A():
    def __init__(self, b):
        self.a = 3
        self.b = b

    def change_ba(self):
        self.b = 7    

    def return_b(self):
        return self.b

class B(A):
    def __init__(self):
        self.b = 4
        A.__init__(self, self.b)


BInstance = B()
print(BInstance.b)
BInstance.change_ba()
print(BInstance.return_b())
print(BInstance.b)