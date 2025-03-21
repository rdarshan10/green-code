import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

import re
import requests
import subprocess
import os
import sys
import argparse

def get_api_key(api_key_file="api_key.txt"):
    """
    Read the API key from a file.
    """
    try:
        with open(api_key_file, "r") as file:
            api_key = file.read().strip()
            print(f"Successfully loaded API key from {api_key_file} ({len(api_key)} characters)")
            return api_key
    except FileNotFoundError:
        print(f"WARNING: API key file '{api_key_file}' not found. Please enter the API key manually.")
        api_key = input("Enter your Groq API key: ").strip()
        if not api_key:
            raise ValueError("No API key provided")
        return api_key

def get_git_file_info(file_path):
    """
    Get detailed information about a file in Git.
    """
    print(f"\nGIT INFO: Analyzing Git status for {file_path}")

    # Check if file is tracked by Git
    is_tracked = subprocess.call(
        ["git", "ls-files", "--error-unmatch", file_path],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL
    ) == 0

    print(f"  • Is file tracked by Git? {'Yes' if is_tracked else 'No'}")

    # Check if file is staged
    is_staged = subprocess.call(
        ["git", "diff", "--cached", "--quiet", "--", file_path],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL
    ) != 0

    print(f"  • Is file staged? {'Yes' if is_staged else 'No'}")

    # Check if file exists in HEAD
    try:
        subprocess.check_output(
            ["git", "cat-file", "-e", f"HEAD:{file_path}"],
            stderr=subprocess.DEVNULL
        )
        exists_in_head = True
        print(f"  • Does file exist in HEAD? Yes")
    except subprocess.CalledProcessError:
        exists_in_head = False
        print(f"  • Does file exist in HEAD? No (new file)")

    return {
        "is_tracked": is_tracked,
        "is_staged": is_staged,
        "exists_in_head": exists_in_head
    }

def get_staged_file_content(file_path):
    """
    Get the content of a staged file from Git index.
    """
    try:
        print(f"GIT CONTENT: Retrieving staged version from Git index...")
        staged_content = subprocess.check_output(
            ["git", "show", f":{file_path}"],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        print(f"  Successfully retrieved staged version ({len(staged_content)} bytes, {staged_content.count(chr(10))+1} lines)")
        print(f"  First 100 chars: {staged_content[:100].replace(chr(10), '⏎')}...")
        return staged_content
    except subprocess.CalledProcessError as e:
        print(f"  Error getting staged content: {e}")
        print(f"  WARNING: Falling back to reading file directly")
        with open(file_path, 'r') as file:
            content = file.read()
            print(f"  Read directly from file ({len(content)} bytes)")
            return content

def get_head_file_content(file_path):
    """
    Get the content of a file from HEAD.
    """
    try:
        print(f"GIT CONTENT: Retrieving HEAD version...")
        head_content = subprocess.check_output(
            ["git", "show", f"HEAD:{file_path}"],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        print(f"  Successfully retrieved HEAD version ({len(head_content)} bytes, {head_content.count(chr(10))+1} lines)")
        print(f"  First 100 chars: {head_content[:100].replace(chr(10), '⏎')}...")
        return head_content
    except subprocess.CalledProcessError as e:
        print(f"  Error getting HEAD content: {e}")
        return None

def analyze_code_changes(file_path):
    """
    Analyze changes between HEAD and staged versions.
    """
    git_info = get_git_file_info(file_path)

    # Get staged content
    staged_content = get_staged_file_content(file_path)

    # Get HEAD content if exists
    original_content = None
    if git_info["exists_in_head"]:
        original_content = get_head_file_content(file_path)

    # Compare if we have both versions
    if original_content and staged_content:
        print("DIFF ANALYSIS: Comparing HEAD and staged versions")

        if original_content == staged_content:
            print("  WARNING: No changes detected between HEAD and staged versions")
            return None

        import difflib
        d = difflib.Differ()
        diff = list(d.compare(original_content.splitlines(), staged_content.splitlines()))

        # Count changes
        added = len([l for l in diff if l.startswith('+ ')])
        removed = len([l for l in diff if l.startswith('- ')])
        changed = len([l for l in diff if l.startswith('? ')])

        print(f"  Diff stats: {added} lines added, {removed} lines removed, {changed} lines modified")

        # Print some of the changes
        change_lines = [l for l in diff if not l.startswith('  ')]
        if change_lines:
            print("  Sample changes (up to 5 lines):")
            for i, line in enumerate(change_lines[:5]):
                print(f"    {line[:100]}{'...' if len(line) > 100 else ''}")
            if len(change_lines) > 5:
                print(f"    ... and {len(change_lines) - 5} more changes")

        return {
            "original": original_content,
            "modified": staged_content
        }
    else:
        print(f"  INFO: Using only staged content for analysis (new file or HEAD not available)")
        return {
            "original": "",
            "modified": staged_content
        }

def analyze_and_update_code_for_sustainability(file_path, api_key_file="api_key.txt", changes_only=False):
    """
    Read code from a file, analyze it with Groq for sustainability,
    and replace the file content with the improved sustainable code.
    """
    print(f"\n===== SUSTAINABILITY ANALYSIS: {file_path} =====")

    # Get file content from Git
    print("\nSTEP 1: Retrieving file content")
    content_data = analyze_code_changes(file_path)

    if not content_data:
        print("WARNING: No content data available for analysis")
        return True

    # Get the API key
    print("\nSTEP 2: Preparing API access")
    api_key = get_api_key(api_key_file)

    # If we have both original and modified, use that information
    is_modified_file = content_data["original"] != ""
    file_content = content_data["modified"]

    # Define the prompt for sustainability analysis
    print("\nSTEP 3: Creating analysis prompt")

    # Determine what to send based on changes_only flag
    if changes_only and is_modified_file:
        # Extract only the changes instead of sending the entire file
        import difflib
        d = difflib.Differ()
        diff = list(d.compare(content_data["original"].splitlines(), content_data["modified"].splitlines()))
        changes = [line[2:] for line in diff if line.startswith('+ ') or line.startswith('- ')]

        code_to_analyze = '\n'.join(changes)
        print(f"  INFO: Analyzing only changed lines ({len(changes)} lines) to save tokens")

        prompt = f"""
        Role: You are a highly experienced software engineer specializing in sustainable and efficient coding practices.

        Task: Analyze the following Python code CHANGES and identify potential areas where it could be improved to reduce resource consumption (CPU, memory, energy), and minimize environmental impact.

        CODE CHANGES:
        ```python
        {code_to_analyze}
        ```

        Please provide suggestions to make these changes more sustainable and efficient. Focus on:
        1. Reducing computational complexity
        2. Minimizing memory usage
        3. Improving energy efficiency
        4. Using more efficient algorithms and data structures
        5. Reducing redundant operations

        Provide only the improved version of these specific changes, not the entire file.
        """
    else:
        # Send the entire file for analysis
        prompt = f"""
        Role: You are a highly experienced software engineer specializing in sustainable and efficient coding practices.

        Task: Analyze the following Python code and identify potential areas where it could be improved to reduce resource consumption (CPU, memory, energy), and minimize environmental impact.

        {'ORIGINAL CODE (BEFORE CHANGES):' if is_modified_file else 'CODE:'}
        ```python
        {content_data['original'] if is_modified_file else file_content}
        ```

        {'MODIFIED CODE (CURRENT VERSION):' if is_modified_file else ''}
        {'```python' if is_modified_file else ''}
        {content_data['modified'] if is_modified_file else ''}
        {'```' if is_modified_file else ''}

        Please provide ONLY the revised version of the ENTIRE file with sustainability improvements applied. The output should directly replace the original code file.
        Focus on:
        1. Reducing computational complexity
        2. Minimizing memory usage
        3. Improving energy efficiency
        4. Using more efficient algorithms and data structures
        5. Reducing redundant operations

        Return ONLY the improved code with no explanations.
        """

    # Send request to Groq API
    print("\nSTEP 4: Sending to Groq API")
    try:
        print(f"  Request size: {len(prompt)} characters")
        if is_modified_file:
            if changes_only:
                print(f"  INFO: Sending only code changes to save tokens")
            else:
                print(f"  INFO: Including both original and modified versions")

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": "You are a sustainable coding expert that optimizes code to reduce environmental impact."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
        )

        # Check for errors
        if response.status_code != 200:
            print(f"  Error from Groq API: {response.text}")
            return False

        print(f"  Received response: {len(response.text)} bytes")

        # Extract the response
        sustainable_code = response.json()["choices"][0]["message"]["content"]

        print("\nSTEP 5: Processing response")
        before_len = len(sustainable_code)

        # Remove Markdown code block markers if present
        sustainable_code = re.sub(r'^```python\n', '', sustainable_code, flags=re.MULTILINE)
        sustainable_code = re.sub(r'^```\n?$', '', sustainable_code, flags=re.MULTILINE)
        sustainable_code = sustainable_code.strip()

        print(f"  Processed response: {before_len} → {len(sustainable_code)} bytes")
        print(f"  First 100 chars: {sustainable_code[:100].replace(chr(10), '⏎')}...")

        # If we only sent changes, we need to apply them to the original file
        if changes_only and is_modified_file:
            # Apply the optimized changes to the full file
            # This is a simplistic approach - in practice would need more sophisticated patching
            print("  INFO: Applying optimized changes to the full file")
            with open(file_path, 'r') as file:
                current_content = file.read()

            # For simplicity, just append the optimized changes as comments
            sustainable_code = current_content + "\n\n# SUSTAINABLE CHANGES SUGGESTED:\n'''\n" + sustainable_code + "\n'''\n"

        # Compare with original to show what changed
        if file_content != sustainable_code:
            import difflib
            d = difflib.Differ()
            diff = list(d.compare(file_content.splitlines(), sustainable_code.splitlines()))

            # Count how many lines were added, removed, or changed
            added = len([l for l in diff if l.startswith('+ ')])
            removed = len([l for l in diff if l.startswith('- ')])
            changed = len([l for l in diff if l.startswith('? ')])

            print(f"  Sustainability improvements: {added} lines added, {removed} lines removed, {changed} lines modified")

            # Show the first few changes
            changes = [l for l in diff if not l.startswith('  ')]
            if changes:
                print("  Sample improvements (up to 5 lines):")
                for i, line in enumerate(changes[:5]):
                    print(f"    {line[:100]}{'...' if len(line) > 100 else ''}")
                if len(changes) > 5:
                    print(f"    ... and {len(changes) - 5} more changes")
        else:
            print("  INFO: No changes made by the optimization")

        # Write the improved code back to the original file
        print("\nSTEP 6: Updating file")
        with open(file_path, 'w') as output_file:
            output_file.write(sustainable_code)

        print(f"  File successfully updated with sustainable code: {file_path}")
        return True

    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Analyze code for sustainability using Groq API")

    # Add arguments
    parser.add_argument("file_path", help="Path to the file containing code to analyze and update")
    parser.add_argument("--api_key_file", default="api_key.txt", help="Path to the file containing the Groq API key")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--changes-only", "-c", action="store_true", help="Only analyze code changes to save tokens")

    # Parse arguments
    args = parser.parse_args()

    if not args.verbose:
        # Redirect stdout to null if not verbose
        sys.stdout = open(os.devnull, 'w')

    success = analyze_and_update_code_for_sustainability(
        args.file_path,
        args.api_key_file,
        args.changes_only
    )

    if not args.verbose:
        # Restore stdout
        sys.stdout = sys.__stdout__
        if success:
            print(f"File successfully updated with sustainable code: {args.file_path}")
        else:
            print(f"Error updating {args.file_path}")

    exit(0 if success else 1)