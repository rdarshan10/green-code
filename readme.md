```markdown
# Sustainable Code Analyzer 🛠️🌱

## Introduction
This project automates the process of analyzing Python code for sustainability using the **Groq API**. The script optimizes code to reduce resource consumption and environmental impact.  
Additionally, **Husky** is integrated to enforce Git pre-commit hooks, ensuring that every commit goes through an automated check.

## Features
- ✅ **Automated Code Analysis**: Sends Python code to Groq API for sustainability improvements.
- ✅ **Husky Pre-Commit Hook**: Ensures that `main.py` runs before every commit.
- ✅ **Git Integration**: Prevents committing without running the sustainability check.

## Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### 2️⃣ Install Dependencies
Ensure you have **Node.js (>=18)** installed, then run:
```bash
npm install
```

### 3️⃣ Setup Husky
Initialize Husky and create a pre-commit hook:
```bash
npx husky init
npx husky set .husky/pre-commit "python main.py"
git add .husky/pre-commit
git commit -m "Setup Husky pre-commit hook"
```

### 4️⃣ Create a `.env` File
The script requires a Groq API key. Create a `.env` file in the root directory and add:
```plaintext
GROQ_API_KEY=your_api_key_here
```

## Usage

### Run the Sustainability Check Manually
```bash
python main.py path/to/your/code.py
```

### Test Husky Pre-Commit Hook
Make a dummy change and commit:
```bash
echo "print('Test')" >> test.py
git add test.py
git commit -m "Testing Husky"
```
Husky should automatically execute `main.py` before the commit.

## Troubleshooting

### 🔹 Husky Hook Not Running?
- Ensure `.husky/pre-commit` is executable:
  ```bash
  chmod +x .husky/pre-commit
  ```

### 🔹 Pre-Commit Hook Failing?
- Run `main.py` manually to check for errors:
  ```bash
  python main.py path/to/code.py
  ```
- Verify `.env` contains a valid API key.

## Contributing
Pull requests are welcome! Ensure your code passes the pre-commit checks before submitting.

## License
This project is licensed under the MIT License.
```

This README provides everything needed to set up, use, and troubleshoot your project. 🚀 Let me know if you need modifications!