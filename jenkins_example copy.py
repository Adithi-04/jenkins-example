"""
#calc app
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

"""
#CODE MODIFICATION

#calc app

def add(n1, n2):
    """
    Function to add two numbers.
        n1 (int): First number.
        n2 (int): Second number.
    Returns:  Sum of n1 and n2.
    """
    return n1 + n2

def sub(n1, n2):
    """
    Function to subtract two numbers.

        n1 (int): First number.
        n2 (int): Second number.

    Returns:  Difference of n1 and n2.
    """
    return n1 - n2

def mul(n1, n2):
    """
    Function to multiply two numbers.
    
        n1 (int): First number.
        n2 (int): Second number.

    Returns: Product of n1 and n2.
    """
    return n1 * n2

def div(n1, n2):
    """
    Function to divide two numbers.

        n1 (int): Numerator.
        n2 (int): Denominator.

    Returns: Result of n1 divided by n2. Returns error message
                      if division by zero occurs.
    """
    if n2 == 0:
        return "Error: Division by zero"
    return n1 / n2

# Test cases
print(add(1, 2))   # Output: 3
print(sub(20, 10)) # Output: 10
print(mul(10, 20)) # Output: 200
print(div(30, 10)) # Output: 3.0
