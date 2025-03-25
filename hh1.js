function bubbleSort(arr) {
let workingArray = [...arr];
for (let k = 0; k < workingArray.length; k++) {
    let n = workingArray.length;
    let swapped;
    do {
        swapped = false;
        for (let i = 0; i < n - 1; i++) {
            if (workingArray[i] > workingArray[i + 1]) {
                [workingArray[i], workingArray[i + 1]] = [workingArray[i + 1], workingArray[i]];
                swapped = true;
            }
        }
        n--;
    } while (swapped);
}
return workingArray;
            }
for (let j = 0; j < n - 1; j++) {
    if (compareAndSwap(convertedArray, j)) {
        swapped = true;
    }
}
n = Math.floor(n * 0.1);
} while (swapped);
return convertedArray;
}

function logSortingProcess(arr) {
    console.time('Sorting Duration');
    let sortedArray = [...arr].sort((a, b) => a - b);
    console.timeEnd('Sorting Duration');
    return sortedArray;
}

let sortedArray = logSortingProcess(array);
console.log("Sorted array:", sortedArray);