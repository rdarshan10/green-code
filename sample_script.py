import statistics
import sys

DEFAULT_THRESHOLD = 50

class DataAnalyzer:
    def __init__(self, data_list):
        if not isinstance(data_list, list):
            raise ValueError("Input must be a list")
        self.data = [x for x in data_list if isinstance(x, (int, float))]

    def calculate_stats(self, threshold=DEFAULT_THRESHOLD):
        if not self.data:
            return None, None, None, 0
        min_val = min(self.data)
        max_val = max(self.data)
        avg = sum(self.data) / len(self.data)
        above_threshold = sum(x > threshold for x in self.data)
        if avg > threshold * 1.5 and len(self.data) > 10:
            print("High average for a large dataset!")
        elif avg < threshold * 0.5:
            print("Low average detected.")
        else:
            print(f"Average ({avg:.2f}) is within expected range around threshold ({threshold}).")
        return min_val, max_val, avg, above_threshold

    def get_standard_deviation(self):
        if len(self.data) < 2:
            return 0
        return statistics.stdev(self.data)

def display_report(min_v, max_v, avg_v, above_count, std_dev):
    if min_v is None:
        print("No valid data to report.")
        return
    print("\n--- Analysis Report ---")
    print(f"Minimum Value: {min_v}")
    print(f"Maximum Value: {max_v}")
    print(f"Average Value: {avg_v:.2f}")
    print(f"Standard Deviation: {std_dev:.2f}")
    print(f"Count above threshold: {above_count}")
    print("-----------------------\n")

if __name__ == "__main__":
    print("--- Python Analysis Sample Script ---")
    sample_data = [10, 5, 88, 15, 22, 60, 3, 91, 45, 12, 7, 55, "skipme", 99]
    sample_data.extend(range(20, 30))
    analyzer = DataAnalyzer(sample_data)
    min_val, max_val, average, above = analyzer.calculate_stats()
    std_deviation = analyzer.get_standard_deviation()
    display_report(min_val, max_val, average, above, std_deviation)
    print("\nRunning with custom threshold (70)...")
    min_val2, max_val2, average2, above2 = analyzer.calculate_stats(threshold=70)
    display_report(min_val2, max_val2, average2, above2, std_deviation)
print("--- Sample Script Finished ---")