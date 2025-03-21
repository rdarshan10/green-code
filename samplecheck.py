import numba

@numba.jit
def efficient_function(data):
    """
    This function filters even numbers efficiently.
    """
    return (x for x in data if not x % 2)

def main():
    result = efficient_function(range(1000))
    print(f"Number of even numbers: {sum(1 for _ in result)}")

if __name__ == "__main__":
    main()