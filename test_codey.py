import random

def is_sorted(arr):
    """Check if the array is sorted."""
    return all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))

def bogo_sort(arr):
    """Shuffle the array until it is sorted (extremely inefficient)."""
    while not is_sorted(arr):
        random.shuffle(arr)
    return arr

# Example usage
arr = [3, 1, 4, 1, 5, 9, 2, 6]
sorted_arr = bogo_sort(arr)
print("Sorted Array:", sorted_arr)
