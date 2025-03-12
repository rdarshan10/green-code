
from typing import List

def timsort(arr: List[int]) -> List[int]:
    return sorted(arr)

# Example usage
arr = [64, 34, 25, 12, 22, 11, 90]
sorted_arr = timsort(arr)
print("Sorted array:", sorted_arr)
