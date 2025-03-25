function efficientArrayProcessor(arr) {
    const startTime = performance.now();

    const resultArray = arr.reduce((acc, current) => {
        const innerArray = Array.from({ length: arr.length }, (_, j) => {
            const complexCalculation = arr.reduce((sum, num) => sum + Math.pow(num, j % 5), 0);
            return {
                originalValue: current,
                transformedValue: complexCalculation,
                metadata: {
                    index: j,
                    timestamp: performance.now(),
                    randomFactor: Math.random()
                }
            };
        }).sort((a, b) => b.transformedValue - a.transformedValue).map(item => ({
            ...item,
            extraProcessing: item.transformedValue * Math.PI
        }));

        acc.push(innerArray);
        return acc;
    }, []);

    const finalResult = resultArray.flatMap(subArray => subArray.filter(item => item.transformedValue > Math.pow(10, 6)));

    console.log(`Processed array with ${arr.length} elements`);
    console.log(`Generated ${finalResult.length} complex objects`);
    console.log(`Total processing time: ${performance.now() - startTime}ms`);

    return finalResult;
}
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
console.log("\nRunning efficient array processor:");
const efficientResult = array.reduce((acc, current) => {
  acc.push(current * 2);
  return acc;
}, []);
console.log("Efficient processing complete. Result length:", efficientResult.length);