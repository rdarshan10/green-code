import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
import re
import requests
import subprocess
import os
import sys
import argparse
import difflib

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
        return head_content
    except subprocess.CalledProcessError as e:
        print(f"  Error getting HEAD content: {e}")
        return None

def analyze_code_changes(file_path):
    """
    Analyze changes between HEAD and staged versions.
    Returns a dictionary with original content, modified content, and change blocks.
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
        
        # Use SequenceMatcher to identify changes more precisely
        s = difflib.SequenceMatcher(None, original_content.splitlines(), staged_content.splitlines())
        
        # Collect change blocks
        change_blocks = []
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            if tag != 'equal':
                # For each non-equal block, store the line ranges and content
                orig_lines = original_content.splitlines()[i1:i2] if i1 < i2 else []
                mod_lines = staged_content.splitlines()[j1:j2] if j1 < j2 else []
                
                # Add some context (3 lines before and after) for better understanding
                context_before = 3
                context_after = 3
                
                # Get context lines from original content
                start_context = max(0, i1 - context_before)
                end_context = min(len(original_content.splitlines()), i2 + context_after)
                
                change_blocks.append({
                    'tag': tag,  # 'replace', 'delete', or 'insert'
                    'original_start': i1,
                    'original_end': i2,
                    'modified_start': j1,
                    'modified_end': j2,
                    'original_lines': orig_lines,
                    'modified_lines': mod_lines,
                    'context_start': start_context,
                    'context_end': end_context,
                    'context_lines': original_content.splitlines()[start_context:end_context]
                })
        
        print(f"  Identified {len(change_blocks)} changed blocks")
        return {
            "original": original_content,
            "modified": staged_content,
            "change_blocks": change_blocks
        }
    else:
        print(f"  INFO: Using only staged content for analysis (new file or HEAD not available)")
        # For new files, treat the entire file as one change block
        change_blocks = [{
            'tag': 'insert',
            'original_start': 0,
            'original_end': 0,
            'modified_start': 0,
            'modified_end': len(staged_content.splitlines()),
            'original_lines': [],
            'modified_lines': staged_content.splitlines(),
            'context_start': 0,
            'context_end': 0,
            'context_lines': []
        }]
        return {
            "original": "",
            "modified": staged_content,
            "change_blocks": change_blocks
        }

def apply_selective_changes(file_path, change_blocks, optimized_blocks):
    """
    Apply optimized changes selectively to the file, preserving unchanged parts.
    
    Args:
        file_path: Path to the file to update
        change_blocks: List of detected change blocks from analyze_code_changes
        optimized_blocks: List of optimized code blocks (corresponding to change_blocks)
    """
    print("  INFO: Applying selective optimized changes to the file")
    
    # Read the current file content
    with open(file_path, 'r') as file:
        current_lines = file.read().splitlines()
    
    # Create a new list for the updated content
    updated_lines = current_lines.copy()
    
    # Apply each optimized block
    # We need to apply them in reverse order to avoid shifting line numbers
    for i, (block, optimized) in reversed(list(enumerate(zip(change_blocks, optimized_blocks)))):
        start = block['modified_start']
        end = block['modified_end']
        
        # Split the optimized block into lines
        optimized_lines = optimized.splitlines()
        
        # Replace the lines in the updated content
        updated_lines[start:end] = optimized_lines
        
        print(f"  Applied optimization to block {i+1}: lines {start+1}-{end} "
              f"({end-start} lines) → {len(optimized_lines)} lines")
    
    # Write the updated content back to the file
    with open(file_path, 'w') as file:
        file.write('\n'.join(updated_lines))
    
    print(f"  Successfully applied selective changes to {file_path}")
    return True

def detect_language(file_path, forced_language=None):
    """
    Detect the programming language based on file extension or shebang.
    """
    if forced_language:
        return forced_language
    
    # First, check by file extension
    file_extension = os.path.splitext(file_path)[1].lower()
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript React',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript React',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.cs': 'C#',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.rs': 'Rust',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.zsh': 'Zsh',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sql': 'SQL',
        '.r': 'R',
        '.pl': 'Perl',
        '.pm': 'Perl',
        '.lua': 'Lua',
        '.dart': 'Dart',
        '.elm': 'Elm',
        '.ex': 'Elixir',
        '.exs': 'Elixir',
        '.erl': 'Erlang',
        '.hrl': 'Erlang',
        '.fs': 'F#',
        '.fsx': 'F#',
        '.hs': 'Haskell',
        '.lhs': 'Haskell',
        '.jl': 'Julia',
    }
    
    if file_extension in language_map:
        return language_map[file_extension]
    
    # For files with no extension or unknown extensions,
    # try to detect by reading the first few lines (e.g., shebang)
    try:
        with open(file_path, 'r') as file:
            first_line = file.readline().strip()
            if first_line.startswith('#!'):
                if 'python' in first_line:
                    return 'Python'
                elif 'node' in first_line or 'javascript' in first_line:
                    return 'JavaScript'
                elif 'ruby' in first_line:
                    return 'Ruby'
                elif 'bash' in first_line:
                    return 'Bash'
                elif 'perl' in first_line:
                    return 'Perl'
                elif 'php' in first_line:
                    return 'PHP'
                elif 'sh' in first_line:
                    return 'Shell'
    except:
        pass
    
    # Default fallback
    return 'Code'

def get_language_specific_system_prompt(language):
    """
    Get a language-specific system prompt for sustainable code optimization.
    """
    prompts = {
        'Python': """You are a sustainable coding expert for Python. 
Focus on these optimization areas:
1. Efficient data structures (using appropriate containers)
2. Reducing memory usage (avoiding unnecessary copies)
3. Optimizing algorithms (improving time complexity)
4. Minimizing I/O operations
5. Using built-in functions and standard library efficiently
6. Reducing unnecessary computations
Only return the optimized code without any explanations.""",
        'JavaScript': """You are a sustainable coding expert for JavaScript.
Focus on these optimization areas:
1. Reducing DOM manipulations
2. Efficient event handling (proper event delegation)
3. Optimizing async operations
4. Memory management (preventing leaks)
5. Efficient data structures and algorithms
6. Minimizing unnecessary re-renders
Only return the optimized code without any explanations.""",
        'TypeScript': """You are a sustainable coding expert for TypeScript.
Focus on these optimization areas:
1. Efficient type definitions and interfaces
2. Proper use of generics
3. Optimizing async operations
4. Memory management
5. Efficient data structures and algorithms
6. Reducing unnecessary computations
Only return the optimized code without any explanations.""",
        'Java': """You are a sustainable coding expert for Java.
Focus on these optimization areas:
1. Efficient object creation and GC pressure
2. Proper resource management (try-with-resources)
3. Optimizing collections usage
4. Thread and concurrency optimization
5. Reducing I/O operations
6. Efficient string handling
Only return the optimized code without any explanations.""",
        'C++': """You are a sustainable coding expert for C++.
Focus on these optimization areas:
1. Memory management (avoiding leaks, using smart pointers)
2. Efficient use of move semantics
3. Proper reference usage
4. Optimizing loops and algorithms
5. Reducing unnecessary copies
6. Cache-friendly code structure
Only return the optimized code without any explanations.""",
        'C#': """You are a sustainable coding expert for C#.
Focus on these optimization areas:
1. Efficient LINQ usage
2. Proper async/await patterns
3. Memory management (IDisposable usage)
4. Optimizing collections
5. Reducing allocations
6. Efficient string operations
Only return the optimized code without any explanations.""",
        'Go': """You are a sustainable coding expert for Go.
Focus on these optimization areas:
1. Efficient goroutine usage
2. Proper error handling
3. Memory efficiency
4. Reducing allocations
5. Efficient I/O operations
6. Using standard library efficiently
Only return the optimized code without any explanations.""",
        'Ruby': """You are a sustainable coding expert for Ruby.
Focus on these optimization areas:
1. Efficient object creation
2. Optimizing iterations
3. Proper memory usage
4. Reducing I/O operations
5. Using built-in methods efficiently
6. Avoiding N+1 query problems
Only return the optimized code without any explanations.""",
        'Rust': """You are a sustainable coding expert for Rust.
Focus on these optimization areas:
1. Efficient memory usage
2. Proper ownership and borrowing
3. Optimizing algorithms
4. Reducing unnecessary allocations
5. Using zero-cost abstractions
6. Efficient error handling
Only return the optimized code without any explanations.""",
        'Shell': """You are a sustainable coding expert for Shell scripting.
Focus on these optimization areas:
1. Reducing process spawning
2. Efficient file handling
3. Proper use of built-in commands
4. Minimizing pipe operations
5. Optimizing loops
6. Reducing unnecessary computations
Only return the optimized code without any explanations.""",
    }
    
    # Default fallback for languages not in the map
    default_prompt = """You are a sustainable coding expert that optimizes code to reduce environmental impact.
Focus on these optimization areas:
1. Reducing CPU usage
2. Minimizing memory consumption
3. Optimizing algorithms
4. Efficient data structures
5. Reducing I/O operations
6. Energy-efficient coding patterns
Only return the optimized code without any explanations."""
    
    return prompts.get(language, default_prompt)

def analyze_and_update_code_for_sustainability(file_path, api_key_file="api_key.txt", changes_only=False, forced_language=None):
    """
    Read code from a file, analyze it with Groq for sustainability,
    and selectively update the file with optimized changes.
    """
    print(f"\n===== SUSTAINABILITY ANALYSIS: {file_path} =====")
    
    # Detect the programming language
    language = detect_language(file_path, forced_language)
    print(f"  Detected language: {language}")
    
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
    
    # Get language-specific system prompt
    system_prompt = get_language_specific_system_prompt(language)
    
    # Define the prompt for sustainability analysis
    print("\nSTEP 3: Creating analysis prompt")
    
    # Get correct markdown code block language identifier
    code_block_lang = language.lower().split()[0]  # Handle cases like "TypeScript React"
    
    # Determine what to send based on changes_only flag
    if changes_only and is_modified_file:
        # Process each change block separately 
        change_blocks = content_data["change_blocks"]
        optimized_blocks = []
        
        for i, block in enumerate(change_blocks):
            print(f"\n  Processing change block {i+1} of {len(change_blocks)}")
            
            # Create context for this change block
            context_before = '\n'.join([
                f"# CONTEXT (lines before change - DO NOT MODIFY):",
                *[line for line in block['context_lines'][:block['original_start'] - block['context_start']]]
            ]) if block['original_start'] > block['context_start'] else ""
            
            context_after = '\n'.join([
                f"# CONTEXT (lines after change - DO NOT MODIFY):",
                *[line for line in block['context_lines'][block['original_end'] - block['context_start']:]]
            ]) if block['original_end'] < block['context_end'] else ""
            
            # Extract the changed code
            changed_code = '\n'.join(block['modified_lines'])
            
            # Create the prompt for this block
            block_prompt = f"""
            Role: You are a highly experienced software engineer specializing in sustainable and efficient coding practices.
            Task: Analyze and optimize the following {language} code segment to reduce resource consumption and minimize environmental impact.
            
            {context_before if context_before else ""}
            
            ```{code_block_lang}
            {changed_code}
            ```
            
            {context_after if context_after else ""}
            
            Return ONLY the optimized version of THE CHANGED CODE SEGMENT (between the markers), nothing else.
            Do not include the context lines in your response.
            Your response should be code only, no explanations or comments about the changes.
            """
            
            # Send request to Groq API for this block
            try:
                print(f"  Sending block {i+1} to Groq API ({len(block_prompt)} characters)")
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama3-70b-8192",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": block_prompt}
                        ],
                        "temperature": 0.2
                    }
                )
                
                # Check for errors
                if response.status_code != 200:
                    print(f"  Error from Groq API: {response.text}")
                    return False
                
                # Extract the response
                optimized_code = response.json()["choices"][0]["message"]["content"]
                
                # Clean up the response
                optimized_code = re.sub(r'^```\w*\n', '', optimized_code, flags=re.MULTILINE)
                optimized_code = re.sub(r'^```\n?$', '', optimized_code, flags=re.MULTILINE)
                optimized_code = optimized_code.strip()
                
                # Store this optimized block
                optimized_blocks.append(optimized_code)
                print(f"  Block {i+1} optimization complete: {len(optimized_code)} characters")
                
            except Exception as e:
                print(f"  Error processing block {i+1}: {e}")
                return False
        
        # Apply all optimized blocks to the file
        print("\nSTEP 4: Applying selective changes")
        return apply_selective_changes(file_path, change_blocks, optimized_blocks)
    
    else:
        # For full file analysis, use the original approach
        file_content = content_data["modified"]
        prompt = f"""
        Role: You are a highly experienced software engineer specializing in sustainable and efficient coding practices.
        Task: Analyze the following {language} code and optimize it to reduce resource consumption (CPU, memory, energy), and minimize environmental impact.
        {'ORIGINAL CODE (BEFORE CHANGES):' if is_modified_file else 'CODE:'}
        ```{code_block_lang}
        {content_data['original'] if is_modified_file else file_content}
        ```
        {'MODIFIED CODE (CURRENT VERSION):' if is_modified_file else ''}
        {'```' + code_block_lang if is_modified_file else ''}
        {content_data['modified'] if is_modified_file else ''}
        {'```' if is_modified_file else ''}
        Return ONLY the optimized version of the entire file with no explanations or suggestions.
        """
        
        # Send request to Groq API
        print("\nSTEP 4: Sending to Groq API")
        try:
            print(f"  Request size: {len(prompt)} characters")
            if is_modified_file:
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
                        {"role": "system", "content": system_prompt},
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
            sustainable_code = re.sub(r'^```\w*\n', '', sustainable_code, flags=re.MULTILINE)
            sustainable_code = re.sub(r'^```\n?$', '', sustainable_code, flags=re.MULTILINE)
            sustainable_code = sustainable_code.strip()
            
            print(f"  Processed response: {before_len} → {len(sustainable_code)} bytes")
            
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
    parser.add_argument("--language", "-l", help="Force specific language for analysis (overrides automatic detection)")
    parser.add_argument("--list-supported", action="store_true", help="List all supported programming languages")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle listing supported languages
    if args.list_supported:
        print("Supported Programming Languages:")
        languages = [
            "Python", "JavaScript", "TypeScript", "Java", "C", "C++", "C#", 
            "Go", "Ruby", "PHP", "Swift", "Rust", "Kotlin", "Scala", "Shell",
            "Bash", "HTML", "CSS", "SQL", "R", "Perl", "Lua", "Dart"
        ]
        for lang in sorted(languages):
            print(f"  • {lang}")
        sys.exit(0)
    
    if not args.verbose:
        # Redirect stdout to null if not verbose
        sys.stdout = open(os.devnull, 'w')
    
    success = analyze_and_update_code_for_sustainability(
        args.file_path,
        args.api_key_file,
        args.changes_only,
        args.language
    )
    
    if not args.verbose:
        # Restore stdout
        sys.stdout = sys.__stdout__
        if success:
            print(f"File successfully updated with sustainable code: {args.file_path}")
        else:
            print(f"Error updating {args.file_path}")
    
    sys.exit(0 if success else 1)