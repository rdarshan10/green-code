import math

def efficient_function(data):
    """
    This function filters even numbers efficiently.
    """
    return (x for x in range(data // 2, data, 2))

def main():
    data = 1000
    result = efficient_function(data)
    print(f"Number of even numbers: {data // 2}")

if __name__ == "__main__":
    main()