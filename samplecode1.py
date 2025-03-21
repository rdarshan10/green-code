def inefficient_function(data):
    """
    This function is intentionally inefficient for demonstration.
    It calculates squares of numbers and filters even squares.
    """
    squares = []
    for x in data:
        squares.append(x * x)

    even_squares = []
    for square in squares:
        if square % 2 == 0:
            even_squares.append(square)
    return even_squares
def efficient_function(data):
    """
    This function calculates squares of numbers and filters even squares efficiently.
    """
    return [x * x for x in data if (x * x) % 2 == 0]

def main():
    numbers = range(1000)  # Create a generator for numbers
    result = efficient_function(numbers)
    print(f"Number of even squares: {len(list(result))}")

if __name__ == "__main__":
    main()
def main():
    numbers = list(range(1000))  # Create a list of numbers
    result = inefficient_function(numbers)
    print(f"Number of even squares: {len(result)}")

if __name__ == "__main__":
    main()
    def inefficient_function(data):
    """
    This function is intentionally inefficient for demonstration.
    It calculates squares of numbers and filters even squares.
    """
    squares = []
    for x in data:
        squares.append(x * x)

    even_squares = []
    for square in squares:
        if square % 2 == 0:
            even_squares.append(square)
    return even_squares

def main():
    numbers = list(range(1000))  # Create a list of numbers
    result = inefficient_function(numbers)
    print(f"Number of even squares: {len(result)}")

if __name__ == "__main__":
    main()def inefficient_function(data):
    """
    This function is intentionally inefficient for demonstration.
    It calculates squares of numbers and filters even squares.
    """
    squares = []
    for x in data:
        squares.append(x * x)

    even_squares = []
    for square in squares:
        if square % 2 == 0:
            even_squares.append(square)
    return even_squares

def main():
    numbers = list(range(1000))  # Create a list of numbers
    result = inefficient_function(numbers)
    print(f"Number of even squares: {len(result)}")
def main():
    numbers = list(range(1000))  # Create a list of numbers
    result = inefficient_function(numbers)
    print(f"Number of even squares: {len(result)}")
def main():
    numbers = list(range(1000))  # Create a list of numbers
    result = inefficient_function(numbers)
    print(f"Number of even squares: {len(result)}")

if __name__ == "__main__":
    main()