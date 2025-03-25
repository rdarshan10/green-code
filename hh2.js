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

let array = [5, 2, 9, 1, 5, 6];
console.log("Original array:", array);

function logSortingProcess(arr) {
    console.time('Sorting Duration');
    let sortedArray = bubbleSort(arr);
    console.timeEnd('Sorting Duration');
    console.log("Sorted array:", sortedArray);
    return sortedArray;
}

let sortedArray = logSortingProcess(array);