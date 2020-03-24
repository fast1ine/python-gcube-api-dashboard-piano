class AAA():
    def __init__(self):
        self.BBB = 3
        self.CCC = 8

    def __getitem__(self, key):
        key, x = key
        if key == "BBB":
            return self.BBB*x

AInstance = AAA()

print(AInstance["BBB",3])
