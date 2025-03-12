# Sustainable Code Analyzer with Husky Git Hooks

This project automates code sustainability analysis using the **Groq API** and integrates **Husky** to enforce automated checks before commits.

## Features
- **Analyzes Python code** for sustainability improvements.
- **Uses Groq API** to optimize code for efficiency.
- **Husky pre-commit hook** ensures every commit is analyzed.
- **Automated file updates** with optimized code.

## Installation

### 1. Clone the Repository
```sh
git clone <your-repository-url>
cd <your-repository-name>
```

### 2. Install Dependencies
```sh
npm install
```

### 3. Setup Husky
```sh
npx husky-init && npm install
```

### 4. Add a Pre-commit Hook
Create a pre-commit hook file:
```sh
npx husky add .husky/pre-commit "python main.py"
```

Make it executable (Linux/Mac):
```sh
chmod +x .husky/pre-commit
```

## Usage

### Run the Analysis Manually
```sh
python main.py path/to/your/code.py
```

### Test the Husky Pre-commit Hook
Try committing a file:
```sh
git add .
git commit -m "Test commit"
```
If your code does not meet sustainability standards, the commit will be blocked until the code is optimized.

## Project Structure
```
/green-code
│── main.py           # Main script for sustainability analysis
│── bubble.py         # Sample script to test analysis
│── .husky/pre-commit # Git hook for automated checks
│── package.json      # Node.js dependencies and Husky config
│── package-lock.json # Lockfile for dependencies
│── .gitignore        # Ignore unnecessary files
```

## License
This project is licensed under the **MIT License**.

## Contributing
Feel free to submit pull requests or report issues!

```