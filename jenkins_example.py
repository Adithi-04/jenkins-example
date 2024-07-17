
def add(n1, n2):
    return n1 + n2

def sub(n1, n2):
    return n1 - n2

def mul(n1, n2):
    return n1 * n2

def div(n1, n2):
    if n2 == 0:
        return "Error: Division by zero"
    return n1 / n2

# Test cases
print(add(1, 2))  #--3
print(sub(20, 10)) #--10
print(mul(10, 20)) #--200
print(div(30, 10)) #--3.0
print(div(30, 0))  #--Error: Division by zero
