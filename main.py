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

def analyze_code_changes_and_info(file_path, api_key_file="api_key.txt", changes_only=False):
    """
    Read code from a file, analyze it with Groq for sustainability,
    and replace the file content with the improved sustainable code.
    This version removes the sustainability analysis and update, only retrieves file content and git info.
    """
    print(f"\n===== FILE ANALYSIS: {file_path} =====")

    # Get file content from Git
    print("\nSTEP 1: Retrieving file content")
    content_data = analyze_code_changes(file_path)

    if not content_data:
        print("WARNING: No content data available for analysis")
        return False

    print("\nAnalysis Complete.")
    return True


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Analyze code and get file information.")

    # Add arguments
    parser.add_argument("file_path", help="Path to the file containing code to analyze")
    parser.add_argument("--api_key_file", default="api_key.txt", help="Path to the file containing the Groq API key (not used in this version)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--changes-only", "-c", action="store_true", help="Only analyze code changes to save tokens (not used in this version)")

    # Parse arguments
    args = parser.parse_args()

    if not args.verbose:
        # Redirect stdout to null if not verbose
        sys.stdout = open(os.devnull, 'w')

    success = analyze_code_changes_and_info(
        args.file_path,
        args.api_key_file,
        args.changes_only
    )

    if not args.verbose:
        # Restore stdout
        sys.stdout = sys.__stdout__
        if success:
            print(f"File analysis completed for: {args.file_path}")
        else:
            print(f"Error analyzing {args.file_path}")

    exit(0 if success else 1)