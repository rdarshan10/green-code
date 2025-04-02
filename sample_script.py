# -*- coding: utf-8 -*-
"""
This file should achieve a perfect sustainability score.
- Low complexity (CCN=1)
- Short functions
- Low LOC
- Minimal dependencies (only sys if needed)
"""
import sys # Minimal import

def simple_adder(a, b):
    """Adds two numbers. Very simple."""
    # This function has CCN = 1
    # It is very short.
    result = a + b
    return result

def main():
    """Main entry point."""
    x = 5
    y = 10
    total = simple_adder(x, y)
    print(f"The sum of {x} and {y} is: {total}", file=sys.stdout) # Use stdout
    # Keep LOC low

# Standard execution guard
if __name__ == "__main__":
    main()
    # Total code lines should be well below thresholds.
    # Cyclomatic complexity max = 1, avg = 1
    # Function LOC max = ~5-6 lines
    # Dependency count = 1 (sys)