def efficient_function(data):
    """
    This function calculates squares of numbers and filters even squares efficiently.
    """
    return (x * x for x in data if x % 2 == 0)

def main():
    result = efficient_function(range(1000))
    print(f"Number of even squares: {sum(1 for _ in result)}")

if __name__ == "__main__":
    main()