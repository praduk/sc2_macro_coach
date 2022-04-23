# Build order generation
# Automatic SCV production until 4-base saturation
# Three Orbitals then PFs
# Automatic Depot production
# Automatic Mules

class Resources(tuple):
    def __add__(self, other):
        return Resources(x + y for x,y in zip(self, other))
    def __sub__(self, other):
        return Resources(x - y for x,y in zip(self, other))

class Base:
    def __init__():
        Base.


#class GameState:
#    def __init__():
#