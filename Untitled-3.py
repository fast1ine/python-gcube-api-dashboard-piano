a = 3

def x():
    z = 7
    def y():
        nonlocal z
        z = 8
    y()
    print(z)

x()