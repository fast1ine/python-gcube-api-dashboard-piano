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


e = Employee()
e.introduce()
print(e.PersonInsctance.A) # bbbb
print(e.PersonInsctance.transport.A) # eeee
e.PersonInsctance.change()
print(e.__dict__) # XXXX