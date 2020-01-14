class Person(object):
    def __init__(self):
        self.name = "{} {}".format("First","Last")
        self.A = "bbbbb"
        self.D = ""

    def B(self):
        return self.A
    
    def G(self):
        return self.D
    
    def E(self):
        self.A = "fffff"
        return "EEEEEEEEE"

class Employee(Person):
    def __init__(self):
        Person.__init__(self)
        self.A = "eeee"

    def E(self):
        Person.E(self)
        return "HHHHHHH"

    def introduce(self):
        print("Hi! My name is {}".format(self.name))
        print(self.A)
        print(Person.B(self))
        self.A = "ccccc"
        print(self.A)
        print(Person.B(self))
        self.D = "ddddd"
        print(self.D)
        print(Person.G(self))
        self.E()
        print(self.A)
        print(Person.E(self))
        print(self.E())
        #Person.E = self.E
        #print(Person.E())


e = Employee()
e.introduce()