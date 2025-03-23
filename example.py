import os
import time

def efficient_function():
    return ",".join(str(i**2) for i in range(1000))

def main():
    print("Starting efficient operations...")
    start_time = time.time()

    data = range(100)
    doubled = (x * 2 for x in (x for x in data if x % 2 == 0))

    with open("temp.txt", "w") as f:
        f.write("\n".join(str(item) for item in doubled))

    with open("temp.txt", "r") as f:
        lines = f.readlines()

    os.remove("temp.txt")

    end_time = time.time()
    print(f"Completed in {end_time - start_time:.2f} seconds")
    print(f"Processed {len(lines)} items")

if __name__ == "__main__":
    main()