# Python Code Sustainability Pre-commit Hook

A smart Git pre-commit hook that automatically optimizes your Python code for sustainability and efficiency using the Groq LLM API.

## Overview

This tool analyzes your Python code changes during Git commits and enhances them to reduce resource consumption (CPU, memory, energy) and minimize environmental impact. It uses Groq's powerful LLM API to identify and implement sustainability improvements without disrupting your workflow.

## Features

- **Intelligent Analysis**: Identifies potential performance and sustainability issues in Python code
- **Change-Focused**: Analyzes only modified portions of files to optimize API usage
- **Git Integration**: Seamlessly works with your existing Git workflow
- **Automatic Optimization**: Applies sustainability improvements before committing
- **Resource-Efficient**: Minimizes API token usage by focusing only on changed code

## Requirements

- Python 3.6+
- Git
- Node.js and npm (for Husky)
- Groq API key

## Setup Instructions

### 1. Install the main script

Save the `main.py` file to your repository root.

### 2. Set up your Groq API key

Create a file named `api_key.txt` in your repository root with your Groq API key:

```
your_groq_api_key_here
```

### 3. Install Husky for Git hooks

Husky is a modern Git hooks manager that makes it easy to run scripts when certain Git events occur.

```bash
# Initialize npm if you haven't already
npm init -y

# Install Husky
npm install husky --save-dev

# Enable Git hooks
npx husky install

# Create a pre-commit hook
npx husky add .husky/pre-commit "python main.py --changes-only"

# Make the hook executable (if on Linux/Mac)
chmod +x .husky/pre-commit
```

### 4. Install Python dependencies

```bash
pip install requests
```

You might want to create a `requirements.txt` file:

```
requests>=2.25.0
```

## How It Works

1. When you run `git commit`, the Husky pre-commit hook activates
2. It identifies all staged Python files
3. For each file, it:
   - Analyzes the specific changes between the staged version and HEAD
   - Sends only the changed code to Groq API for sustainability optimization
   - Updates the file with the optimized code
   - Re-stages the file automatically
4. If all optimizations succeed, the commit completes as normal

## Example Workflow

1. Create or modify a Python file (e.g., `example.py`)
2. Stage the file with `git add example.py`
3. Run `git commit -m "Your commit message"`
4. The pre-commit hook will:
   - Analyze `example.py` for sustainability issues
   - Optimize only the changed parts of the code
   - Apply the optimizations to the file
   - Re-stage the optimized file
   - Complete the commit if all optimizations succeed

## Viewing Changes

To see the changes made by the sustainability optimization:

```bash
# After the hook has run but before completing the commit
git diff --cached

# Or if you want to see what changes were made to already committed files
git show HEAD
```

## Command Line Options

When running the script manually, you can use these options:

```bash
# Analyze a specific file with verbose output
python main.py path/to/your/file.py --verbose

# Only analyze changes (not the entire file)
python main.py path/to/your/file.py --changes-only 

# Specify a different API key file
python main.py path/to/your/file.py --api_key_file custom_key.txt
```

## Troubleshooting

- **API Key Issues**: Ensure your Groq API key is correctly set in `api_key.txt`
- **Permission Denied**: Make sure the Husky hooks are executable
- **No Files Analyzed**: Verify you've staged Python files before committing
- **Changes Not Visible**: The hook only analyzes and optimizes *staged* changes
- **Husky Not Running**: Check that Husky is properly installed and initialized
- **Missing package.json**: Make sure you've run `npm init` in your repository

## Benefits

- **Environmental Impact**: Reduce the carbon footprint of your code
- **Performance Gains**: Optimized code typically runs faster and uses fewer resources
- **Education**: Learn sustainable coding patterns through AI recommendations
- **Efficiency**: Save development time by automating code optimization

## Custom Configuration

You can customize Husky behavior by editing your `package.json` file:

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "python main.py --changes-only"
    }
  }
}
```

## License

This project is available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.