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
let array = [5, 2, 9, 1, 5, 6];
console.log("Before sorting:", array);
bubbleSort(array);
console.log("After sorting:", array);