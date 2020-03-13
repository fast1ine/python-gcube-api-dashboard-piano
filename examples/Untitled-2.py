class Person(object):
    def __init__(self):
        self.name = "{} {}".format("First","Last")
        self.A = "bbbbb"
        self.D = ""

    def transporting(self, transport): ## ???
        self.transport = transport

    def change(self):
        self.transport.B = "XXX"


class Employee():
    class Customer():
        name = ""
        age = 0

    def __init__(self):
        self.PersonInsctance = Person()
        self.A = "eeee"
        self.B = ""

    def introduce(self):
        self.PersonInsctance.transporting(self)

    def makeCustomer(self):
        customer1 = self.Customer()

class EElse():
    def __init__(self, BB):
        self.BB = BB
        self.CC = BB
        print("ParentBB:", id(self.BB))
        print("ParentCC:", id(self.CC))

    def printBBCC(self):
        self.BB = 333
        print("ParentBB:", self.BB)
        print("ParentCC:", self.CC)

    def printBBid(self):
        print("ParentBBid:", id(self.BB))

    def myfunction(self):
        print("Y")

class EElse2():
    def myfunction(self):
        print("X")

class Something(EElse, EElse2):
    def __init__(self):
        self.BB = "아무노래"
        print("Child:", id(self.BB))
        EElse.__init__(self, self.BB)
        self.BB = 777
        print("ChildBB:", self.BB)
        print("ChildBBid", id(self.BB))

    def printBB(self):
        print("ChildBB:", self.BB)





e = Employee()
e.introduce()
print(e.PersonInsctance.A) # bbbb
print(e.PersonInsctance.transport.A) # eeee
e.PersonInsctance.change()
print(e.__dict__) # XXXX



som = Something()
som.printBBCC()
som.printBB()
print(id(som.CC), id(som.BB))
som.printBBid()
som.myfunction()

XX = 44
def chageXX():
    YY = 77
    print(XX)

chageXX()
print(XX)