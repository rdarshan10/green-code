# -*- coding: utf-8 -*-
import sys
import io
# Ensure UTF-8 output even if redirected
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)
except (AttributeError, ValueError):
    # Handle cases where stdout/stderr might not be standard streams (e.g., in some IDEs)
    pass

import re
import requests 
import subprocess
import os
import sys
import argparse
import difflib
import tempfile
import shutil

# Attempt to import codecarbon, but don't make it a hard requirement unless used
try:
    from codecarbon import EmissionsTracker 
    CODECARBON_AVAILABLE = True
except ImportError:
    CODECARBON_AVAILABLE = False
    EmissionsTracker = None # Define dummy for type hinting/checking



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
            universal_newlines=True,
            encoding='utf-8' # Ensure correct decoding
        )
        print(f"  Successfully retrieved staged version ({len(staged_content)} bytes, {staged_content.count(chr(10))+1} lines)")
        return staged_content
    except subprocess.CalledProcessError as e:
        print(f"  Error getting staged content: {e}")
        print(f"  WARNING: Falling back to reading file directly")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                print(f"  Read directly from file ({len(content)} bytes)")
                return content
        except Exception as read_err:
            print(f"  Error reading file directly: {read_err}")
            return None # Indicate failure
    except Exception as e:
        print(f"  Unexpected error getting staged content: {e}")
        return None

def get_head_file_content(file_path):
    """
    Get the content of a file from HEAD.
    """
    try:
        print(f"GIT CONTENT: Retrieving HEAD version...")
        head_content = subprocess.check_output(
            ["git", "show", f"HEAD:{file_path}"],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8' # Ensure correct decoding
        )
        print(f"  Successfully retrieved HEAD version ({len(head_content)} bytes, {head_content.count(chr(10))+1} lines)")
        return head_content
    except subprocess.CalledProcessError as e:
        print(f"  Error getting HEAD content: {e}")
        return None
    except Exception as e:
        print(f"  Unexpected error getting HEAD content: {e}")
        return None

def analyze_code_changes(file_path):
    """
    Analyze changes between HEAD and staged versions.
    Returns a dictionary with original content, modified content, and change blocks.
    """
    git_info = get_git_file_info(file_path)
    # Get staged content
    staged_content = get_staged_file_content(file_path)
    if staged_content is None:
        print("ERROR: Could not retrieve staged file content.")
        return None

    # Get HEAD content if exists
    original_content = None
    if git_info["exists_in_head"]:
        original_content = get_head_file_content(file_path)

    # Compare if we have both versions
    if original_content is not None and staged_content is not None:
        print("DIFF ANALYSIS: Comparing HEAD and staged versions")
        original_lines = original_content.splitlines()
        staged_lines = staged_content.splitlines()

        if original_lines == staged_lines:
            print("  WARNING: No changes detected between HEAD and staged versions")
            # Still return content, might be needed for full file analysis
            # return None # Previous behavior

        # Use SequenceMatcher to identify changes more precisely
        s = difflib.SequenceMatcher(None, original_lines, staged_lines)

        # Collect change blocks
        change_blocks = []
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            if tag != 'equal':
                # For each non-equal block, store the line ranges and content
                orig_lines = original_lines[i1:i2]
                mod_lines = staged_lines[j1:j2]

                # Add some context (3 lines before and after) for better understanding
                context_before = 3
                context_after = 3

                # Get context lines from original content (or staged if original is shorter)
                context_source_lines = original_lines if len(original_lines) >= i2 else staged_lines
                context_source_len = len(context_source_lines)

                start_context = max(0, i1 - context_before)
                # Ensure end_context doesn't exceed the length of the source lines
                end_context = min(context_source_len, i2 + context_after)

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
                    # Use staged context if original is missing/shorter
                    'context_lines': staged_lines[start_context:end_context] if not original_lines else original_lines[start_context:end_context]
                })

        print(f"  Identified {len(change_blocks)} changed blocks")
        return {
            "original": original_content,
            "modified": staged_content,
            "change_blocks": change_blocks
        }
    elif staged_content is not None:
        print(f"  INFO: Using only staged content for analysis (new file or HEAD not available)")
        staged_lines = staged_content.splitlines()
        # For new files, treat the entire file as one change block
        change_blocks = [{
            'tag': 'insert',
            'original_start': 0,
            'original_end': 0,
            'modified_start': 0,
            'modified_end': len(staged_lines),
            'original_lines': [],
            'modified_lines': staged_lines,
            'context_start': 0,
            'context_end': 0,
            'context_lines': []
        }]
        return {
            "original": "", # Represent no original content
            "modified": staged_content,
            "change_blocks": change_blocks
        }
    else:
        # Case where even staged content couldn't be read
        print("ERROR: Failed to retrieve any content for analysis.")
        return None


def apply_selective_changes(file_path, original_staged_content, change_blocks, optimized_blocks):
    """
    Apply optimized changes selectively to the original staged content.

    Args:
        file_path: Path to the file to update (used for logging)
        original_staged_content: The full content of the staged file before optimization.
        change_blocks: List of detected change blocks from analyze_code_changes
        optimized_blocks: List of optimized code blocks (corresponding to change_blocks)

    Returns:
        The full content with optimizations applied, or None if an error occurs.
    """
    print("  INFO: Reconstructing file with selective optimized changes")

    if len(change_blocks) != len(optimized_blocks):
        print(f"  ERROR: Mismatch between change blocks ({len(change_blocks)}) and optimized blocks ({len(optimized_blocks)})")
        return None

    # Start with the original staged lines
    current_lines = original_staged_content.splitlines()
    offset = 0 # Keep track of line number changes due to insertions/deletions

    # Apply optimized blocks sequentially (easier to manage offset)
    for i, (block, optimized_code) in enumerate(zip(change_blocks, optimized_blocks)):
        # Adjust start/end based on previous changes
        start = block['modified_start'] + offset
        end = block['modified_end'] + offset

        # Split the optimized block into lines
        optimized_lines = optimized_code.splitlines()
        num_optimized_lines = len(optimized_lines)
        num_original_lines_in_block = block['modified_end'] - block['modified_start']

        # Replace the lines in the current content
        current_lines[start:end] = optimized_lines

        # Update the offset for subsequent blocks
        offset += (num_optimized_lines - num_original_lines_in_block)

        print(f"  Applied optimization to block {i+1}: lines {block['modified_start']+1}-{block['modified_end']} "
              f"({num_original_lines_in_block} lines) → {num_optimized_lines} lines")

    updated_content = '\n'.join(current_lines)
    # Add a trailing newline if the original content had one and the new one doesn't
    if original_staged_content.endswith('\n') and not updated_content.endswith('\n'):
         updated_content += '\n'

    print(f"  Successfully reconstructed content for {file_path}")
    return updated_content


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
        with open(file_path, 'r', encoding='utf-8') as file:
            # Read first few lines to find shebang or other hints
            for _ in range(5): # Check first 5 lines
                 line = file.readline()
                 if not line: break # End of file
                 line = line.strip()
                 if line.startswith('#!'):
                     if 'python' in line: return 'Python'
                     if 'node' in line: return 'JavaScript'
                     if 'deno' in line: return 'TypeScript' # Deno often uses TS
                     if 'ruby' in line: return 'Ruby'
                     if 'bash' in line: return 'Bash'
                     if 'perl' in line: return 'Perl'
                     if 'php' in line: return 'PHP'
                     if 'sh' in line: return 'Shell'
                     # Add more shebang checks if needed
                     break # Found shebang, stop checking lines
    except Exception as e:
        print(f"  Warning: Could not read file head for language detection: {e}")
        pass

    # Default fallback
    print(f"  Warning: Could not determine language for {file_path}. Using 'Code'.")
    return 'Code'

def get_language_specific_system_prompt(language):
    """
    Get a language-specific system prompt for sustainable code optimization.
    """
    prompts = {
        'Python': """You are a sustainable coding expert for Python.
Focus on these optimization areas:
1. Efficient data structures (using appropriate containers)
2. Reducing memory usage (avoiding unnecessary copies, generators)
3. Optimizing algorithms (improving time complexity)
4. Minimizing I/O operations (buffering, batching)
5. Using built-in functions and standard library efficiently
6. Reducing unnecessary computations (memoization, lazy evaluation)
7. Power-aware choices (e.g., prefer efficient libraries)
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        'JavaScript': """You are a sustainable coding expert for JavaScript.
Focus on these optimization areas:
1. Reducing DOM manipulations and reflows
2. Efficient event handling (proper event delegation, debouncing/throttling)
3. Optimizing async operations (Promise.all, avoiding unnecessary awaits)
4. Memory management (preventing leaks, efficient closures)
5. Efficient data structures and algorithms (Map, Set, avoiding O(n^2))
6. Minimizing unnecessary re-renders (React, Vue, etc.)
7. Tree shaking and code splitting awareness
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        'TypeScript': """You are a sustainable coding expert for TypeScript.
Focus on these optimization areas:
1. Efficient type definitions and interfaces (avoiding `any`)
2. Proper use of generics for code reuse and type safety
3. Optimizing async operations (Promise.all, avoiding unnecessary awaits)
4. Memory management (preventing leaks, efficient closures)
5. Efficient data structures and algorithms (Map, Set, avoiding O(n^2))
6. Reducing unnecessary computations and re-renders
7. Leveraging TS features for better compile-time checks that prevent runtime overhead
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        'Java': """You are a sustainable coding expert for Java.
Focus on these optimization areas:
1. Efficient object creation and GC pressure reduction (pooling, immutability)
2. Proper resource management (try-with-resources)
3. Optimizing collections usage (choosing right implementations, streams API efficiency)
4. Thread and concurrency optimization (avoiding excessive locking, using efficient concurrent structures)
5. Reducing I/O operations (NIO, buffering)
6. Efficient string handling (StringBuilder vs String concatenation)
7. Primitive types vs Wrapper classes where appropriate
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        'C++': """You are a sustainable coding expert for C++.
Focus on these optimization areas:
1. Memory management (RAII, smart pointers, avoiding leaks)
2. Efficient use of move semantics and copy elision
3. Proper reference usage (const references)
4. Optimizing loops and algorithms (cache locality, vectorization hints)
5. Reducing unnecessary copies and allocations (pass by reference, placement new)
6. Compile-time computation (constexpr)
7. Efficient use of STL containers and algorithms
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        'C#': """You are a sustainable coding expert for C#.
Focus on these optimization areas:
1. Efficient LINQ usage (avoiding multiple enumerations)
2. Proper async/await patterns (ConfigureAwait(false))
3. Memory management (IDisposable usage, struct vs class, Span<T>)
4. Optimizing collections (choosing right implementations)
5. Reducing allocations (string interpolation efficiency, StringBuilder)
6. Efficient exception handling
7. Value types and memory locality
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        'Go': """You are a sustainable coding expert for Go.
Focus on these optimization areas:
1. Efficient goroutine usage and channel communication (avoiding deadlocks, buffer sizes)
2. Proper error handling (avoiding panic for recoverable errors)
3. Memory efficiency (struct layout, avoiding unnecessary allocations)
4. Reducing allocations (sync.Pool, passing pointers vs values appropriately)
5. Efficient I/O operations (bufio)
6. Using standard library efficiently (strings package, etc.)
7. Profiling for bottlenecks
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        'Ruby': """You are a sustainable coding expert for Ruby.
Focus on these optimization areas:
1. Efficient object creation and reducing GC pressure
2. Optimizing iterations (each vs map vs select, avoiding intermediate arrays)
3. Proper memory usage (symbol vs string, lazy enumerators)
4. Reducing I/O operations (buffering)
5. Using built-in methods efficiently (avoiding reimplementing standard library)
6. Database query optimization (avoiding N+1 queries in web frameworks)
7. Efficient string manipulation
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        'Rust': """You are a sustainable coding expert for Rust.
Focus on these optimization areas:
1. Efficient memory usage through ownership and borrowing (avoiding clones)
2. Proper use of lifetimes
3. Optimizing algorithms and data structures (using standard library efficiently)
4. Reducing unnecessary allocations (stack vs heap, Box, Rc, Arc)
5. Using zero-cost abstractions effectively
6. Efficient error handling (Result vs panic)
7. Concurrency patterns (async/await, threads)
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        'Shell': """You are a sustainable coding expert for Shell scripting (Bash/Sh/Zsh).
Focus on these optimization areas:
1. Reducing process spawning (use builtins where possible)
2. Efficient file handling (avoiding reading whole files into memory, using tools like awk/sed efficiently)
3. Proper use of built-in commands vs external utilities
4. Minimizing pipe operations where alternatives exist
5. Optimizing loops (avoiding loops for text processing where tools like grep/awk/sed are better)
6. Efficient variable handling and string manipulation
7. Using command substitution $(...) sparingly
Only return the optimized code without any explanations, comments about changes, or markdown formatting.""",
        # Add more language prompts here...
    }

    # Default fallback for languages not in the map
    default_prompt = """You are a sustainable coding expert that optimizes code to reduce environmental impact.
Focus on these general optimization areas:
1. Reducing CPU usage (algorithmic efficiency, fewer operations)
2. Minimizing memory consumption (efficient data structures, avoiding leaks/unnecessary copies)
3. Optimizing algorithms (better time/space complexity)
4. Efficient data structures selection
5. Reducing I/O operations (disk and network)
6. Energy-efficient coding patterns (platform/language specific if known)
Only return the optimized code without any explanations, comments about changes, or markdown formatting."""

    # Handle specific shell variants mapping to the generic Shell prompt
    if language in ['Bash', 'Zsh'] and 'Shell' in prompts:
        return prompts['Shell']

    return prompts.get(language, default_prompt)


# --- New Function for CodeCarbon Measurement ---
def measure_python_emissions(code_content, file_path_hint, stage_name, timeout_seconds=60):
    """
    Executes Python code content in a temporary file and measures emissions using CodeCarbon.

    Args:
        code_content (str): The Python code to execute.
        file_path_hint (str): Original file path, used for naming the CodeCarbon project.
        stage_name (str): 'before' or 'after' optimization.
        timeout_seconds (int): Max execution time for the script.

    Returns:
        float or None: Estimated emissions in kg CO2eq, or None if measurement fails/skipped.
    """
    if not CODECARBON_AVAILABLE:
        print("  MEASUREMENT: CodeCarbon library not found. Skipping emission measurement.")
        return None
    if not code_content:
        print("  MEASUREMENT: No code content provided. Skipping emission measurement.")
        return None

    print(f"\n===== CodeCarbon Measurement ({stage_name.upper()}) =====")
    emissions_kg = None
    temp_py_file = None

    # Use a temporary directory to potentially handle module imports within the script
    temp_dir = tempfile.mkdtemp(prefix="codecarbon_exec_")
    try:
        # Create a temporary file within the temp directory
        temp_py_file_path = os.path.join(temp_dir, f"temp_script_{stage_name}.py")
        with open(temp_py_file_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        print(f"  Created temporary script: {temp_py_file_path}")

        # Configure and start the tracker
        # Use a unique project name to avoid conflicts if run multiple times
        project_name = f"sustain_{os.path.basename(file_path_hint)}_{stage_name}_{os.getpid()}"
        # Ensure output dir exists
        output_dir = "codecarbon_reports"
        os.makedirs(output_dir, exist_ok=True)

        print(f"  Starting CodeCarbon tracker (Project: {project_name}, Output: {output_dir})")
        # Offline mode might be more robust if network issues are common
        # tracker = OfflineEmissionsTracker(project_name=project_name, output_dir=output_dir, country_iso_code="USA") # Example: Force region
        tracker = EmissionsTracker(project_name=project_name, output_dir=output_dir, log_level='warning') # Reduce verbosity

        tracker.start()
        process = None
        try:
            print(f"  Executing: {sys.executable} {temp_py_file_path}")
            # Execute the temporary script in its own directory context
            process = subprocess.Popen(
                [sys.executable, temp_py_file_path],
                cwd=temp_dir, # Run from the temp dir
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout, stderr = process.communicate(timeout=timeout_seconds)

            print(f"  Execution finished with code: {process.returncode}")
            if process.returncode != 0:
                print(f"  WARNING: Script execution failed ({stage_name}). Measurement might be inaccurate.")
                print(f"  Stderr:\n{stderr}")
            # Optional: print stdout if needed for debugging
            # print(f"  Stdout:\n{stdout}")

        except subprocess.TimeoutExpired:
            print(f"  ERROR: Script execution timed out after {timeout_seconds} seconds ({stage_name}).")
            if process:
                process.kill() # Ensure the process is terminated
                process.communicate() # Consume any remaining output
            # No meaningful emissions data if it timed out before finishing
            return None
        except Exception as e:
            print(f"  ERROR: Failed to execute script ({stage_name}): {e}")
            # No meaningful emissions data if execution failed
            return None
        finally:
            # Stop the tracker regardless of execution success/failure
            try:
                emissions_kg = tracker.stop()
                if emissions_kg is not None:
                    print(f"  CodeCarbon measurement complete ({stage_name}): {emissions_kg:.9f} kg CO₂eq")
                else:
                    # This can happen if measurement duration is too short or other issues
                    print(f"  WARNING: CodeCarbon tracker returned None for emissions ({stage_name}). Measurement might be invalid.")
            except Exception as e:
                print(f"  ERROR: Failed to stop CodeCarbon tracker ({stage_name}): {e}")
                emissions_kg = None # Ensure None is returned on error

    except Exception as e:
        print(f"  ERROR: Unexpected error during emission measurement setup ({stage_name}): {e}")
        emissions_kg = None
    finally:
        # Clean up the temporary directory and its contents
        if temp_dir and os.path.exists(temp_dir):
             try:
                 shutil.rmtree(temp_dir)
                 print(f"  Cleaned up temporary directory: {temp_dir}")
             except Exception as e:
                 print(f"  WARNING: Failed to clean up temporary directory {temp_dir}: {e}")

    return emissions_kg


# --- Modified Main Analysis Function ---
def analyze_and_update_code_for_sustainability(
    file_path,
    api_key_file="api_key.txt",
    changes_only=False,
    forced_language=None,
    measure_emissions=False,
    execution_timeout=60
    ):
    """
    Reads code, analyzes with Groq, optionally measures Python emissions,
    and updates the file.
    """
    print(f"\n===== SUSTAINABILITY ANALYSIS & UPDATE: {file_path} =====")

    # Detect the programming language
    language = detect_language(file_path, forced_language)
    print(f"  Detected language: {language}")

    # Check if measurement is requested and possible
    can_measure = measure_emissions and language == 'Python' and CODECARBON_AVAILABLE
    if measure_emissions and not CODECARBON_AVAILABLE:
        print("  WARNING: --measure-emissions requested, but 'codecarbon' library is not installed. Skipping measurement.")
        print("  Install it using: pip install codecarbon")
    if measure_emissions and language != 'Python':
        print(f"  INFO: --measure-emissions requested, but language is {language}. Measurement currently only supported for Python.")
        can_measure = False

    # --- STEP 1: Get Code Content ---
    print("\nSTEP 1: Retrieving file content for analysis")
    content_data = analyze_code_changes(file_path)
    if not content_data or content_data.get("modified") is None:
        print("ERROR: Failed to retrieve code content. Aborting.")
        return False

    staged_content = content_data["modified"]
    original_content = content_data["original"]
    change_blocks = content_data["change_blocks"]
    is_modified_file = original_content != "" # Check if there was a HEAD version

    # --- STEP 1.5: Measure Emissions BEFORE Optimization (if applicable) ---
    emissions_before = None
    if can_measure:
        emissions_before = measure_python_emissions(staged_content, file_path, "before", execution_timeout)

    # --- STEP 2: Prepare API Access ---
    print("\nSTEP 2: Preparing API access")
    api_key = get_api_key(api_key_file)

    # --- STEP 3: Call Groq API for Optimization ---
    print("\nSTEP 3: Optimizing code with Groq API")
    system_prompt = get_language_specific_system_prompt(language)
    code_block_lang = language.lower().split()[0]

    optimized_full_code = None # Will hold the final optimized content

    if changes_only and is_modified_file and change_blocks:
        print("  Mode: Analyzing only changed blocks")
        optimized_blocks = []
        all_blocks_processed = True
        for i, block in enumerate(change_blocks):
            print(f"\n  Processing change block {i+1} of {len(change_blocks)} (Lines {block['modified_start']+1}-{block['modified_end']})")

            # Extract the code to be optimized (the modified lines)
            code_to_optimize = '\n'.join(block['modified_lines'])
            if not code_to_optimize.strip():
                print("    Skipping empty block.")
                optimized_blocks.append("") # Add empty string for placeholder
                continue

            # Create context hints (optional, maybe less useful for pure optimization)
            # context_before_hint = f"# Context Before:\n# ... {block['context_lines'][0] if block['context_lines'] else ''} ..."
            # context_after_hint = f"# Context After:\n# ... {block['context_lines'][-1] if block['context_lines'] else ''} ..."

            block_prompt = f"""Optimize the following {language} code segment for sustainability and efficiency. Focus on CPU, memory, and energy reduction.
Return ONLY the optimized version of the provided code segment, nothing else. Preserve the core functionality.

```{code_block_lang}
{code_to_optimize}
```"""

            try:
                print(f"    Sending block {i+1} to Groq API ({len(code_to_optimize)} chars code)")
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "llama3-70b-8192",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": block_prompt}
                        ],
                        "temperature": 0.1 # Lower temperature for more deterministic optimization
                    },
                    timeout=60 # Add timeout for API call
                )

                if response.status_code != 200:
                    print(f"    ERROR from Groq API (Block {i+1}): {response.status_code} {response.text}")
                    all_blocks_processed = False
                    break # Stop processing further blocks on error

                optimized_code_segment = response.json()["choices"][0]["message"]["content"]

                # Clean up the response (remove markdown, strip whitespace)
                optimized_code_segment = re.sub(r'^```[\w]*\n?', '', optimized_code_segment, flags=re.MULTILINE)
                optimized_code_segment = re.sub(r'\n?```$', '', optimized_code_segment, flags=re.MULTILINE)
                optimized_code_segment = optimized_code_segment.strip()

                optimized_blocks.append(optimized_code_segment)
                print(f"    Block {i+1} optimization received: {len(optimized_code_segment)} chars")

            except requests.exceptions.Timeout:
                 print(f"    ERROR: Groq API request timed out for block {i+1}")
                 all_blocks_processed = False
                 break
            except Exception as e:
                print(f"    ERROR processing block {i+1}: {e}")
                all_blocks_processed = False
                break

        if not all_blocks_processed:
            print("ERROR: Failed to process all change blocks. Aborting update.")
            return False

        # Reconstruct the full file content using the optimized blocks
        print("\nSTEP 4: Reconstructing file from optimized blocks")
        optimized_full_code = apply_selective_changes(file_path, staged_content, change_blocks, optimized_blocks)
        if optimized_full_code is None:
            print("ERROR: Failed to reconstruct file content. Aborting update.")
            return False

    else:
        # Full file analysis
        print("  Mode: Analyzing full file content")
        prompt_content = staged_content # Default to staged content
        prompt_header = f"Optimize the following {language} code for sustainability and efficiency:"

        # If comparing changes, provide both versions to the LLM
        if is_modified_file and original_content is not None:
             prompt_header = f"You are given an original and a modified version of a {language} file. Optimize the MODIFIED version for sustainability and efficiency, considering the changes made:"
             prompt_content = f"ORIGINAL CODE:\n```\n{original_content}\n```\n\nMODIFIED CODE:\n```{code_block_lang}\n{staged_content}\n```"
             print("  INFO: Providing both original and modified versions to the LLM.")


        full_prompt = f"""{prompt_header}
Focus on CPU, memory, and energy reduction. Return ONLY the fully optimized version of the {'MODIFIED' if is_modified_file else 'entire'} code, nothing else. Preserve the core functionality. No explanations, comments about changes, or markdown formatting.

{prompt_content}"""


        try:
            print(f"  Sending full file prompt to Groq API ({len(full_prompt)} chars)")
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama3-70b-8192",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_prompt}
                    ],
                    "temperature": 0.1 # Lower temperature
                },
                timeout=120 # Longer timeout for potentially larger files
            )

            if response.status_code != 200:
                print(f"  ERROR from Groq API (Full File): {response.status_code} {response.text}")
                return False

            print(f"  Received response: {len(response.text)} bytes")
            optimized_full_code = response.json()["choices"][0]["message"]["content"]

            # Clean up the response
            before_len = len(optimized_full_code)
            optimized_full_code = re.sub(r'^```[\w]*\n?', '', optimized_full_code, flags=re.MULTILINE)
            optimized_full_code = re.sub(r'\n?```$', '', optimized_full_code, flags=re.MULTILINE)
            optimized_full_code = optimized_full_code.strip()
            print(f"  Processed response: {before_len} -> {len(optimized_full_code)} bytes")

            # Add trailing newline if original had one and optimized doesn't
            if staged_content.endswith('\n') and not optimized_full_code.endswith('\n'):
                optimized_full_code += '\n'

        except requests.exceptions.Timeout:
            print("  ERROR: Groq API request timed out for full file analysis.")
            return False
        except Exception as e:
            print(f"  ERROR during full file optimization: {e}")
            return False

    if optimized_full_code is None:
        print("ERROR: No optimized code was generated. Aborting update.")
        return False

    # --- STEP 5: Measure Emissions AFTER Optimization (if applicable) ---
    emissions_after = None
    if can_measure:
        emissions_after = measure_python_emissions(optimized_full_code, file_path, "after", execution_timeout)

    # --- STEP 6: Update File ---
    print("\nSTEP 5: Updating file with optimized code")
    try:
        with open(file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(optimized_full_code)
        print(f"  File successfully updated: {file_path}")
    except Exception as e:
        print(f"  ERROR: Failed to write updated file {file_path}: {e}")
        return False

    # --- STEP 7: Report Emissions Comparison (if applicable) ---
    if can_measure and emissions_before is not None and emissions_after is not None:
        print("\n===== Emission Comparison =====")
        print(f"  Estimated Emissions BEFORE: {emissions_before:.9f} kg CO₂eq")
        print(f"  Estimated Emissions AFTER:  {emissions_after:.9f} kg CO₂eq")
        try:
            diff = emissions_after - emissions_before
            percent_change = (diff / emissions_before * 100) if emissions_before else 0
            print(f"  Difference: {diff:+.9f} kg CO₂eq ({percent_change:+.2f}%)")
            if diff < 0:
                print("  SUCCESS: Optimization potentially reduced estimated emissions.")
            elif diff > 0:
                print("  WARNING: Optimization potentially increased estimated emissions.")
            else:
                print("  INFO: No significant change in estimated emissions detected.")
        except ZeroDivisionError:
             print("  INFO: Cannot calculate percentage change from zero baseline emissions.")
    elif can_measure:
        print("\n===== Emission Comparison =====")
        print("  Could not complete emission comparison (measurement failed for before or after).")


    print(f"\n===== Analysis and Update Complete for {file_path} =====")
    return True


# --- Main Execution Block ---
if __name__ == "__main__":
    # ... (Argument parsing setup remains the same) ...
    parser = argparse.ArgumentParser(
        description="Analyze staged code changes or full files for sustainability using Groq API, optionally measure Python emissions with CodeCarbon, and update the file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Add arguments
    parser.add_argument("file_path", help="Path to the file to analyze and update")
    parser.add_argument("--api_key_file", default="api_key.txt", help="Path to file containing Groq API key")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed logs during processing")
    parser.add_argument("--changes-only", "-c", action="store_true", help="Analyze only staged changes (vs HEAD) to potentially save tokens and focus optimization. Requires file to be in Git index.")
    parser.add_argument("--language", "-l", help="Force specific language for analysis (e.g., 'Python', 'JavaScript'). Overrides automatic detection.")
    parser.add_argument("--list-supported", action="store_true", help="List known programming languages with specific prompts")
    parser.add_argument("--measure-emissions", "-m", action="store_true", help="[EXPERIMENTAL] Measure estimated CO2 emissions using CodeCarbon before and after optimization. Currently only supports executable Python scripts. Requires `codecarbon` package.")
    parser.add_argument("--execution-timeout", type=int, default=60, help="Timeout in seconds for script execution during emission measurement.")

    args = parser.parse_args()

    # ... (Handling --list-supported remains the same) ...
    if args.list_supported:
        print("Languages with specific system prompts:")
        known_languages = [
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go',
            'Ruby', 'Rust', 'Shell', 'Bash', 'Zsh'
        ]
        for lang in sorted(known_languages):
            print(f"  • {lang}")
        print("\nOther languages will use a default prompt.")
        sys.exit(0)


    # Handle verbosity (capture original streams first)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    devnull = None
    if not args.verbose:
        # Redirect stdout/stderr *after* the initial debug prints for codecarbon import
        try:
            devnull = open(os.devnull, 'w', encoding='utf-8')
            sys.stdout = devnull
            sys.stderr = devnull # Redirect stderr as well if not verbose
        except Exception as e:
            sys.stdout = original_stdout # Restore on error
            sys.stderr = original_stderr
            print(f"Warning: Could not suppress output: {e}", file=sys.stderr)


    # --- Improved Check for CodeCarbon ---
    if args.measure_emissions and not CODECARBON_AVAILABLE:
         # Restore output temporarily to show the warning clearly
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        print("\n" + "="*20 + " CONFIGURATION ERROR " + "="*20, file=sys.stderr)
        print("ERROR: --measure-emissions flag was used, but the 'codecarbon' library could not be imported.", file=sys.stderr)
        print("       This usually means it's not installed in the Python environment being used to run this script.", file=sys.stderr)
        print(f"\n       Current Python Interpreter: {sys.executable}", file=sys.stderr)
        # Suggest the specific command using the detected interpreter's basename
        interpreter_basename = os.path.basename(sys.executable)
        print(f"\n       To install it for this interpreter, try running:", file=sys.stderr)
        print(f"         {interpreter_basename} -m pip install codecarbon", file=sys.stderr)
        print("\n       If you are using a virtual environment (like venv or conda), ensure it is activated before running the script.", file=sys.stderr)
        print("="*61 + "\n", file=sys.stderr)

         # No need to re-apply suppression, we are exiting
        if devnull: # Close devnull if it was opened
             devnull.close()
        sys.exit(1) # Exit with an error code
    # --- End Improved Check ---


    # Run the main analysis function
    success = False
    try:
        # Ensure output is not suppressed when calling the main function if verbose is true
        if args.verbose:
             sys.stdout = original_stdout
             sys.stderr = original_stderr

        success = analyze_and_update_code_for_sustainability(
            args.file_path,
            args.api_key_file,
            args.changes_only,
            args.language,
            args.measure_emissions,
            args.execution_timeout
        )
    except Exception as main_e:
         # Restore output fully to show the error
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        import traceback
        print(f"\nFATAL ERROR during analysis: {main_e}", file=sys.stderr)
        print("Traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        success = False # Ensure failure state
    finally:
        # Restore stdout/stderr if they were redirected
        if not args.verbose:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        if devnull:
            devnull.close() # Ensure devnull is closed

    # Print final status (only if not verbose, otherwise it's already printed)
    if not args.verbose:
        if success:
            print(f"File successfully analyzed and updated: {args.file_path}")
            # Consider adding a summary of emissions change here if measured
        else:
            print(f"Error processing file: {args.file_path}", file=sys.stderr)

    sys.exit(0 if success else 1)