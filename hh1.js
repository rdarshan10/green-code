function bubbleSort(arr) {
    let n = arr.length;
    let swapped;

    do {
        swapped = false;
        for (let j = 0; j < n - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
                swapped = true;
            }
        }
        n--;
    } while (swapped);

    return arr;
}

// Example usage
let array = [64, 34, 25, 12, 22, 11, 90];
console.log("Before sorting:", array);
let sortedArray = bubbleSort(array);
console.log("After sorting:", sortedArray);
console.log("Original array:", array);