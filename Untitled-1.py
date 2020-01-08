class AXAX():
    somebool = True

    def some_generator(self):
        yield AXAX.somebool
        AXAX.somebool = False

    def get_generator(self):
        for i in self.some_generator():
            j = i
        return j

A = AXAX()
print(A.get_generator())
print(A.get_generator())
print(A.get_generator())





#for i in A.some_generator():
#    print(i)
#for i in A.some_generator():
#    print(i)
#for i in A.some_generator():
#    print(i)