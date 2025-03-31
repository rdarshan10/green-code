def sorted_array(arr):
    return sorted(arr)

# Example usage
arr = [64, 34, 25, 12, 22, 11, 90]
arr = sorted_array(arr)
print("Sorted array:", arr)
import random

def is_sorted(arr):
    return all(arr[i] <= arr[i+1] for i in range(len(arr)-1))

def bogo_sort(arr):
    while not is_sorted(arr):
        random.shuffle(arr)

# Example usage
arr1 = [64, 34, 25, 12, 22, 11, 90]
arr2 = arr1[:]  # Copy of the array for Bogo Sort
bogo_sort(arr2)
print("Bogo Sort Result:", arr2)