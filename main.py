# -*- coding: utf-8 -*-
import sys
import io
try:
    # Ensure UTF-8 encoding for stdout/stderr, especially in non-UTF-8 environments
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)
except (AttributeError, ValueError):
    # Handle environments where buffer might not exist or other issues
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
import json
import math
import ast # For Python Syntax Check

# --- Constants ---
LLM_LOC_LIMIT = 1000 # Maximum Lines of Code to send to LLM for full file analysis
PERFECT_SCORE_THRESHOLD = 99.9 # Skip LLM if score is already near perfect

# --- CodeCarbon Import ---
try:
    from codecarbon import EmissionsTracker
    CODECARBON_AVAILABLE = True
except ImportError:
    CODECARBON_AVAILABLE = False
    EmissionsTracker = None # Define it as None if not available

# --- REVISED SCORING CONFIGURATION (Stricter Python + Density, No Semgrep) ---
SCORING_CONFIG = {
    'python': {
        # Metric Name: { good: value, bad: value, weight: value }

        # --- Complexity --- (Stricter 'good', Higher Weight)
        'cyclomatic_complexity_max': {'good': 2,  'bad': 15, 'weight': 30},
        'cyclomatic_complexity_avg': {'good': 1.5,'bad': 6,  'weight': 20},

        # --- Function Length --- (Stricter 'good', Higher Weight)
        'function_loc_max':          {'good': 10, 'bad': 40, 'weight': 15},

        # --- Code Size --- (Stricter 'good')
        'loc_code_cloc':             {'good': 50, 'bad': 500, 'weight': 5},
        'loc_logical_radon':         {'good': 40, 'bad': 400, 'weight': 5 },

        # --- Dependencies --- (Lower Weight slightly)
        'dependency_count':          {'good': 3,  'bad': 15, 'weight': 10}, # Reduced weight further

        # --- NEW: Complexity Density --- (Avg CCN per Logical LOC)
        # Lower is better. Good: Very low complexity relative to code lines.
        'complexity_density':        {'good': 0.05, 'bad': 0.20, 'weight': 10}, # Moderate weight

        # --- Anti-Patterns Placeholder --- (using LLM/Metrics as proxy)
        # 'anti_pattern_count':      {'good': 0,  'bad': 3,  'weight': 10}, # Not directly measured here
    },
    # --- Stricter configs for other languages (optional, keep or adjust) ---
    'javascript': {
        'cyclomatic_complexity_max': {'good': 3,  'bad': 20, 'weight': 25},
        'function_loc_max':          {'good': 15, 'bad': 60, 'weight': 15}, # Increased weight
        'loc_code_cloc':             {'good': 80, 'bad': 800,'weight': 5},
        # 'eslint_complexity_violations': {'good': 0, 'bad': 2, 'weight': 20}, # Placeholder if ESLint used
        'dependency_count':          {'good': 5,  'bad': 25, 'weight': 15}, # Reduced weight
        # 'complexity_density': Needs a reliable logical LOC source for JS (no dedicated metric here yet)
    },
    'c': {
        'cyclomatic_complexity_max': {'good': 4,  'bad': 25, 'weight': 30},
        'cyclomatic_complexity_avg': {'good': 2.5,'bad': 10, 'weight': 15},
        'function_loc_max':          {'good': 20, 'bad': 70, 'weight': 15},
        'loc_code_cloc':             {'good': 100,'bad': 900,'weight': 5},
        'dependency_count':          {'good': 2,  'bad': 12, 'weight': 20}, # Inc weight slightly
        # Use cloc LOC for density calculation in calculate_total_score
        'complexity_density_cloc':   {'good': 0.08, 'bad': 0.30, 'weight': 10}, # Using cloc LOC
    },
    'cpp': {
        'cyclomatic_complexity_max': {'good': 5,  'bad': 30, 'weight': 30},
        'cyclomatic_complexity_avg': {'good': 3,  'bad': 12, 'weight': 15},
        'function_loc_max':          {'good': 25, 'bad': 80, 'weight': 15},
        'loc_code_cloc':             {'good': 150,'bad': 1000,'weight': 5},
        'dependency_count':          {'good': 4,  'bad': 18, 'weight': 20}, # Inc weight slightly
        # Use cloc LOC for density calculation in calculate_total_score
        'complexity_density_cloc':   {'good': 0.08, 'bad': 0.30, 'weight': 10}, # Using cloc LOC
    }
    # Add/adjust other languages as needed
}

# --- Helper Functions ---

def get_api_key(api_key_file="api_key.txt"):
    """Read the API key from a file."""
    try:
        with open(api_key_file, "r", encoding='utf-8') as file:
            api_key = file.read().strip()
            if not api_key:
                print(f"WARNING: API key file '{api_key_file}' is empty. LLM step will fail if needed.")
                return None
            # print(f"Successfully loaded API key from {api_key_file}") # Less verbose
            return api_key
    except FileNotFoundError:
        print(f"WARNING: API key file '{api_key_file}' not found. LLM step will fail if needed.")
        return None
    except Exception as e:
        print(f"ERROR: Failed to read API key file '{api_key_file}': {e}")
        return None

def get_git_file_info(file_path):
    """Get detailed information about a file in Git."""
    print(f"\nGIT INFO: Analyzing Git status for {file_path}")
    info = {"is_tracked": False, "is_staged": False, "exists_in_head": False}
    try:
        # Check if file is tracked by Git
        is_tracked_cmd = ["git", "ls-files", "--error-unmatch", file_path]
        info["is_tracked"] = subprocess.run(is_tracked_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False).returncode == 0
        print(f"  • Is file tracked by Git? {'Yes' if info['is_tracked'] else 'No'}")

        if info["is_tracked"]:
            # Check if file is staged (changes added to index)
            is_staged_cmd = ["git", "diff", "--cached", "--quiet", "--", file_path]
            info["is_staged"] = subprocess.run(is_staged_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False).returncode != 0
            print(f"  • Is file staged? {'Yes' if info['is_staged'] else 'No'}")

            # Check if file exists in HEAD (was committed before)
            exists_in_head_cmd = ["git", "cat-file", "-e", f"HEAD:{file_path}"]
            info["exists_in_head"] = subprocess.run(exists_in_head_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False).returncode == 0
            print(f"  • Does file exist in HEAD? {'Yes' if info['exists_in_head'] else 'No (likely new file)'}")
        else:
             print("  • File not tracked by Git. Cannot determine staged status or HEAD existence.")

    except FileNotFoundError:
         print("  ERROR: 'git' command not found. Cannot get Git info.")
    except Exception as e:
         print(f"  ERROR: Unexpected error getting Git info: {e}")
    return info

def get_staged_file_content(file_path):
    """Get the content of a staged file from Git index."""
    try:
        print(f"GIT CONTENT: Retrieving staged version from Git index for {os.path.basename(file_path)}...")
        staged_content = subprocess.check_output(
            ["git", "show", f":{file_path}"],
            stderr=subprocess.STDOUT, # Capture stderr too, in case of warnings/errors
            universal_newlines=True,
            encoding='utf-8' # Ensure correct decoding
        )
        print(f"  Successfully retrieved staged version ({len(staged_content)} bytes, {staged_content.count(chr(10))+1} lines)")
        return staged_content
    except subprocess.CalledProcessError as e:
        # This often means the file is not staged or not tracked
        print(f"  INFO: Could not get staged content via 'git show :{file_path}'. Error: {e.output.strip()}")
        print(f"  Attempting to read file directly from disk.")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                print(f"  Read directly from disk ({len(content)} bytes)")
                return content
        except Exception as read_err:
            print(f"  ERROR: Failed to read file directly: {read_err}")
            return None # Indicate failure
    except FileNotFoundError:
        print("  ERROR: 'git' command not found. Cannot get staged content.")
        return None
    except Exception as e:
        print(f"  ERROR: Unexpected error getting staged content: {e}")
        return None

def get_head_file_content(file_path):
    """Get the content of a file from HEAD (last commit)."""
    try:
        print(f"GIT CONTENT: Retrieving HEAD version for {os.path.basename(file_path)}...")
        head_content = subprocess.check_output(
            ["git", "show", f"HEAD:{file_path}"],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8' # Ensure correct decoding
        )
        print(f"  Successfully retrieved HEAD version ({len(head_content)} bytes, {head_content.count(chr(10))+1} lines)")
        return head_content
    except subprocess.CalledProcessError:
        # This is common for new files, don't make it look like a severe error
        print(f"  INFO: Could not get HEAD content (likely a new file or not committed).")
        return None
    except FileNotFoundError:
        print("  ERROR: 'git' command not found. Cannot get HEAD content.")
        return None
    except Exception as e:
        print(f"  ERROR: Unexpected error getting HEAD content: {e}")
        return None

def analyze_code_changes(file_path):
    """
    Analyze changes between HEAD and staged versions using Git.
    Returns a dictionary with original content, modified content, and change blocks.
    """
    git_info = get_git_file_info(file_path)
    staged_content = get_staged_file_content(file_path)

    if staged_content is None:
        print(f"ERROR: Could not retrieve current/staged file content for {file_path}. Cannot analyze.")
        return None

    original_content = None
    if git_info["exists_in_head"]:
        original_content = get_head_file_content(file_path)
        if original_content is None:
             print(f"  WARNING: File exists in HEAD, but failed to retrieve HEAD content for {file_path}. Treating as new file for diff.")

    if original_content is not None:
        print("DIFF ANALYSIS: Comparing HEAD and staged versions")
        original_lines = original_content.splitlines()
        staged_lines = staged_content.splitlines()

        if original_lines == staged_lines:
            print("  INFO: No changes detected between HEAD and staged versions.")
            # Still return content, might be needed for full file analysis

        # Use difflib to find changed blocks
        s = difflib.SequenceMatcher(None, original_lines, staged_lines, autojunk=False)
        change_blocks = []
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            # We only care about blocks that are not 'equal' for optimization purposes
            if tag != 'equal':
                # Extract the lines involved in the change from the *staged* version
                # We optimize based on what's currently staged.
                modified_lines_in_block = staged_lines[j1:j2]

                # Store information about the block
                change_blocks.append({
                    'tag': tag, # 'replace', 'delete', 'insert'
                    'original_start_line': i1, # Line number in original (0-based)
                    'original_end_line': i2,
                    'modified_start_line': j1, # Line number in staged (0-based)
                    'modified_end_line': j2,
                    'modified_lines': modified_lines_in_block, # Content of the block in the staged version
                })
                print(f"  - Found change block ({tag}): Original lines {i1+1}-{i2}, Staged lines {j1+1}-{j2}")

        print(f"  Identified {len(change_blocks)} changed block(s)")
        return {
            "original": original_content,
            "modified": staged_content,
            "change_blocks": change_blocks,
            "is_modified": True # Explicitly state it's a modification of a tracked file
        }
    else:
        # Case: New file (not in HEAD or HEAD content retrieval failed)
        print(f"  INFO: Using only staged content for analysis (likely a new file or HEAD unavailable)")
        staged_lines = staged_content.splitlines()
        # Treat the entire file as one big 'insert' block
        change_blocks = [{
            'tag': 'insert',
            'original_start_line': 0,
            'original_end_line': 0,
            'modified_start_line': 0,
            'modified_end_line': len(staged_lines),
            'modified_lines': staged_lines,
        }]
        return {
            "original": None, # No original content available
            "modified": staged_content,
            "change_blocks": change_blocks,
            "is_modified": False # It's a new file, not a modification of a tracked one
        }


def apply_selective_changes(original_staged_content, change_blocks, optimized_blocks):
    """
    Reconstructs the file content by replacing modified blocks with optimized blocks.
    Operates on lists of lines for easier manipulation.
    """
    print("  INFO: Reconstructing file with selective optimized changes")

    if len(change_blocks) != len(optimized_blocks):
        print(f"  ERROR: Mismatch between number of change blocks ({len(change_blocks)}) "
              f"and optimized blocks ({len(optimized_blocks)}). Cannot apply changes.")
        return None # Indicate failure

    original_lines = original_staged_content.splitlines()
    result_lines = []
    last_copied_line_index = -1 # Keep track of where we are in the original staged lines

    for i, (block, optimized_code) in enumerate(zip(change_blocks, optimized_blocks)):
        start_line_in_staged = block['modified_start_line']
        end_line_in_staged = block['modified_end_line']
        optimized_lines = optimized_code.splitlines() # Split the LLM output

        # Copy the unchanged lines *before* the current block
        if start_line_in_staged > last_copied_line_index + 1:
            result_lines.extend(original_lines[last_copied_line_index + 1 : start_line_in_staged])

        # Append the *optimized* lines for the current block
        result_lines.extend(optimized_lines)

        # Update the index to show we've processed up to this point in the original
        last_copied_line_index = end_line_in_staged - 1

        num_original_lines_in_block = end_line_in_staged - start_line_in_staged
        print(f"    Applied optimization to block {i+1}: Staged lines {start_line_in_staged+1}-{end_line_in_staged} "
              f"({num_original_lines_in_block} lines) -> replaced with {len(optimized_lines)} optimized lines")

    # Copy any remaining lines *after* the last change block
    if last_copied_line_index < len(original_lines) - 1:
        result_lines.extend(original_lines[last_copied_line_index + 1 :])

    # Join lines back into a single string, preserving trailing newline if original had one
    updated_content = '\n'.join(result_lines)
    if original_staged_content.endswith('\n') and not updated_content.endswith('\n'):
         updated_content += '\n'
    elif not original_staged_content.endswith('\n') and updated_content.endswith('\n'):
         # Handle case where LLM added a newline unnecessarily (less common)
         pass # Keep the added newline for now, might be intentional

    print(f"  Successfully reconstructed content.")
    return updated_content


def detect_language(file_path, forced_language=None):
    """Detect language based on extension or shebang, return name and scoring key."""
    language_name = 'Unknown'
    language_key = None # Key used for SCORING_CONFIG

    # Map forced language input to canonical name and key
    lang_key_map_force = {
        'python': ('Python', 'python'), 'py': ('Python', 'python'),
        'javascript': ('JavaScript', 'javascript'), 'js': ('JavaScript', 'javascript'), 'jsx': ('JavaScript React', 'javascript'),
        'typescript': ('TypeScript', 'javascript'), 'ts': ('TypeScript', 'javascript'), 'tsx': ('TypeScript React', 'javascript'), # Often share JS rules/tools
        'c': ('C', 'c'),
        'c++': ('C++', 'cpp'), 'cpp': ('C++', 'cpp'), 'cxx': ('C++', 'cpp'), 'cc': ('C++', 'cpp'),
        'h': ('C/C++ Header', 'c'), 'hpp': ('C++ Header', 'cpp'), # Headers often follow rules of their implementation lang
        'java': ('Java', 'java'),
        'c#': ('C#', 'csharp'), 'cs': ('C#', 'csharp'),
        'go': ('Go', 'go'),
        'ruby': ('Ruby', 'ruby'), 'rb': ('Ruby', 'ruby'),
        'php': ('PHP', 'php'),
        'swift': ('Swift', 'swift'),
        'rust': ('Rust', 'rust'), 'rs': ('Rust', 'rust'),
        'kotlin': ('Kotlin', 'kotlin'), 'kt': ('Kotlin', 'kotlin'),
        'scala': ('Scala', 'scala'),
        'shell': ('Shell', 'shell'), 'sh': ('Shell', 'shell'), 'bash': ('Bash', 'shell'), 'zsh': ('Zsh', 'shell'),
    }

    if forced_language:
        lang_lower = forced_language.lower()
        if lang_lower in lang_key_map_force:
            language_name, language_key = lang_key_map_force[lang_lower]
            print(f"  Forced language: {language_name} (Scoring Key: {language_key})")
            return language_name, language_key
        else:
            # Use the forced name directly, but key remains None if not mapped
            language_name = forced_language
            language_key = None
            print(f"  Forced language: {language_name} (No specific scoring key found, using defaults if available)")
            return language_name, language_key

    # --- Automatic Detection ---
    file_extension = os.path.splitext(file_path)[1].lower()
    # Map extensions to language name and scoring key
    language_map_ext = {
        '.py': ('Python', 'python'), '.js': ('JavaScript', 'javascript'), '.jsx': ('JavaScript React', 'javascript'),
        '.ts': ('TypeScript', 'javascript'), '.tsx': ('TypeScript React', 'javascript'), '.java': ('Java', 'java'),
        '.c': ('C', 'c'), '.cpp': ('C++', 'cpp'), '.cxx': ('C++', 'cpp'), '.cc': ('C++', 'cpp'),
        '.h': ('C/C++ Header', 'c'), '.hpp': ('C++ Header', 'cpp'), '.cs': ('C#', 'csharp'),
        '.go': ('Go', 'go'), '.rb': ('Ruby', 'ruby'), '.php': ('PHP', 'php'), '.swift': ('Swift', 'swift'),
        '.rs': ('Rust', 'rust'), '.kt': ('Kotlin', 'kotlin'), '.kts': ('Kotlin Script', 'kotlin'),
        '.scala': ('Scala', 'scala'), '.sh': ('Shell', 'shell'), '.bash': ('Bash', 'shell'), '.zsh': ('Zsh', 'shell'),
        # Languages often without specific scoring keys but useful for LLM hint
        '.html': ('HTML', None), '.htm': ('HTML', None), '.css': ('CSS', None), '.scss': ('SCSS', None), '.sass': ('Sass', None),
        '.sql': ('SQL', None), '.json': ('JSON', None), '.yaml': ('YAML', None), '.yml': ('YAML', None),
        '.xml': ('XML', None), '.md': ('Markdown', None), '.txt': ('Text', None), '.dockerfile': ('Dockerfile', None),
        '.tf': ('Terraform', None),
    }

    if file_extension in language_map_ext:
        language_name, language_key = language_map_ext[file_extension]
        print(f"  Detected language by extension ({file_extension}): {language_name} (Scoring Key: {language_key})")
        return language_name, language_key

    # Shebang detection as fallback
    try:
        # Use context manager and ensure file closure
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            first_line = file.readline().strip()
            if first_line.startswith('#!'):
                shebang_lower = first_line.lower()
                # Check common interpreters mapped to scoring keys
                if 'python' in shebang_lower: language_name, language_key = 'Python', 'python'
                elif 'node' in shebang_lower: language_name, language_key = 'JavaScript', 'javascript'
                elif 'bash' in shebang_lower: language_name, language_key = 'Bash', 'shell'
                elif 'sh' in shebang_lower: language_name, language_key = 'Shell', 'shell'
                elif 'zsh' in shebang_lower: language_name, language_key = 'Zsh', 'shell'
                elif 'perl' in shebang_lower: language_name, language_key = 'Perl', None # No key defined yet
                elif 'ruby' in shebang_lower: language_name, language_key = 'Ruby', 'ruby'
                # Add more as needed

                if language_key: # If we found a mapping
                     print(f"  Detected language by shebang: {language_name} (Scoring Key: {language_key})")
                     return language_name, language_key
                elif language_name != 'Unknown': # If name identified but no key
                     print(f"  Detected language by shebang: {language_name} (No specific scoring key)")
                     return language_name, None

    except Exception as e:
        print(f"  Warning: Could not read file head for shebang detection: {e}")

    # Final fallback
    print(f"  Warning: Could not determine specific language for {os.path.basename(file_path)}. Using default '{language_name}'.")
    return language_name, language_key


def get_language_specific_system_prompt(language_name):
    """ Get language-specific system prompt, including anti-pattern guidance AND comment/output preservation rules. """
    prompts = {
        # --- Enhanced Prompts (Strategy 3) ---
        'Python': """You are a sustainable coding expert for Python. Focus on: efficient data structures (lists vs tuples vs sets vs dicts), reducing memory allocation/garbage collection pressure, optimizing algorithms (time/space complexity), minimizing I/O operations (buffering, batching), using built-ins efficiently (map, filter, list comprehensions), reducing unnecessary computations (caching/memoization), power-aware choices where applicable. Also identify and refactor common performance anti-patterns like inefficient loops (e.g., manual iteration instead of built-ins), redundant calculations inside loops, excessive string concatenation, or inappropriate data structure usage for the task. Preserve all existing comments. Preserve exact observable output (e.g., print statements). Only return the optimized code without explanations or markdown.""",
        'Java': """You are a sustainable coding expert for Java. Focus on: efficient object creation/reuse (pooling, flyweight), minimizing garbage collection overhead (avoid temporary objects), using try-with-resources for resource management, optimizing collections/streams (choose appropriate implementations, parallel streams cautiously), efficient thread/concurrency handling (avoid excessive locking), reducing I/O (NIO, buffering), efficient string handling (StringBuilder vs concatenation), using primitives vs wrappers appropriately. Also identify and refactor common performance anti-patterns like string concatenation in loops, inefficient collection iteration/lookups, N+1 query patterns if ORM context is implied, excessive object creation in hotspots. Preserve all existing comments. Preserve exact observable output (e.g., print statements). Only return the optimized code without explanations or markdown.""",
        'JavaScript': """You are a sustainable coding expert for JavaScript/TypeScript. Focus on: reducing DOM manipulations/reflows in browser contexts, efficient event handling (debouncing/throttling), optimizing asynchronous operations (Promise.all, avoiding nested callbacks), careful memory management (avoid leaks, large closures), choosing efficient data structures (Map/Set vs Object/Array), minimizing re-renders in UI frameworks, awareness of tree shaking for smaller bundles. For TS: use efficient types, avoid 'any'. Also identify and refactor common performance anti-patterns like inefficient loops (for...in on arrays, using Array.prototype methods inefficiently), unnecessary computations in render cycles, memory leaks from event listeners or closures, large bundle sizes due to unused imports. Preserve all existing comments. Preserve exact observable output (e.g., print statements). Only return the optimized code without explanations or markdown.""",
        'TypeScript': """You are a sustainable coding expert for TypeScript. Focus on: using efficient types/interfaces (avoid `any`, use specific types), leveraging generics for reusable, type-safe code, optimizing asynchronous operations (async/await, Promise.all), careful memory management, choosing efficient data structures (Map/Set vs Object/Array), reducing computations/re-renders in UI contexts, leveraging TS features for compile-time checks that prevent runtime overhead. Also identify and refactor common performance anti-patterns similar to JavaScript (inefficient loops, unnecessary computations, memory leaks), plus potential TS-specific issues like overly complex type manipulations causing slow compile times if applicable. Preserve all existing comments. Preserve exact observable output (e.g., print statements). Only return the optimized code without explanations or markdown.""",
        'C++': """You are a sustainable coding expert for C++. Focus on: RAII/smart pointers for memory/resource management, leveraging move semantics and copy elision to avoid unnecessary copies, using `const` references for parameters, optimizing loops/algorithms (considering cache locality, potential for vectorization), reducing dynamic memory allocations (prefer stack allocation where possible, use custom allocators if needed), effective use of `constexpr` for compile-time computation, choosing efficient STL containers/algorithms. Also identify and refactor common performance anti-patterns like unnecessary copies of large objects, inefficient string manipulations, cache misses due to poor data layout, excessive virtual function calls in performance-critical paths. Preserve all existing comments. Preserve exact observable output (e.g., print statements). Only return the optimized code without explanations or markdown.""",
        'C': """You are a sustainable coding expert for C. Focus on: careful and efficient manual memory management (minimizing malloc/free calls, checking bounds), optimizing loops/algorithms (cache locality, instruction-level parallelism awareness), minimizing function call overhead (inlining potential), reducing memory footprint (struct packing, bitfields cautiously), efficient I/O operations (buffering), safe and efficient pointer arithmetic, using standard library functions effectively. Also identify and refactor common performance anti-patterns like inefficient memory access patterns causing cache misses, redundant computations, unnecessary function calls in loops, suboptimal use of standard library functions. Preserve all existing comments. Preserve exact observable output (e.g., print statements). Only return the optimized code without explanations or markdown.""",
        'C#': """You are a sustainable coding expert for C#. Focus on: efficient LINQ usage (avoid multiple enumerations, prefer specific methods), proper async/await patterns (ConfigureAwait(false) where applicable), careful memory management (IDisposable/using statements, choosing struct vs class appropriately, using Span<T>/Memory<T>), optimizing collections (choose correct type, pre-size capacity), reducing allocations (string pooling/interning, StringBuilder), efficient exception handling (avoid exceptions for flow control), leveraging value types. Also identify and refactor common performance anti-patterns like multiple enumerations of IEnumerable, inefficient LINQ queries, excessive boxing/unboxing, string concatenation in loops, chatty I/O operations. Preserve all existing comments. Preserve exact observable output (e.g., print statements). Only return the optimized code without explanations or markdown.""",
        # Add other specific prompts here, ensuring they include the preservation rules...
    }

    # --- MODIFIED Default Prompt ---
    default_prompt = """You are a sustainable coding expert optimizing code for environmental impact.
Focus on these general optimization areas:
1. Reducing CPU usage (algorithmic efficiency, fewer operations, avoiding redundant calculations)
2. Minimizing memory consumption (efficient data structures, avoiding leaks/unnecessary copies/allocations)
3. Optimizing algorithms (better time/space complexity where possible)
4. Efficient data structures selection (choosing the right tool for the job)
5. Reducing I/O operations (disk and network - buffering, batching, minimizing frequency)
6. Identifying and applying energy-efficient coding patterns (platform/language specific if known)

Additionally, specifically look for and refactor common performance anti-patterns appropriate for the target language. This includes things like inefficient loops, algorithms, data structure usage, resource handling, or object creation patterns that negatively impact performance or resource usage.

Critically, preserve all existing comments from the original code.
Critically, preserve the exact observable output and side effects (e.g., print statements) of the original code. Do not make changes that alter what the user sees as output or how the code interacts externally, unless it's a direct consequence of fixing a specified sustainability anti-pattern in a way that maintains semantic equivalence.

Return ONLY the optimized code. Do not include any explanations, comments about the changes, or markdown formatting (like ```language ... ``` wrappers). Just return the raw code."""
    # --- End Modification ---

    # Handle specific language name variations or mappings
    if language_name in ['Bash', 'Zsh', 'Shell Script'] and 'Shell' in prompts: return prompts['Shell']
    if 'React' in language_name and 'JavaScript' in prompts: return prompts['JavaScript']
    if 'TypeScript' in language_name and 'TypeScript' in prompts: return prompts['TypeScript']

    # Return specific prompt if found, otherwise the enhanced default
    return prompts.get(language_name, default_prompt)

def run_tool(command, working_dir=None, check=False, timeout=60):
    """Runs an external tool, captures output, handles errors."""
    command_str = ' '.join(command)
    print(f"    Executing: {command_str}" + (f" in {working_dir}" if working_dir else ""))
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True, # Decode stdout/stderr as text
            cwd=working_dir,
            encoding='utf-8', # Specify encoding
            errors='ignore', # Ignore decoding errors if necessary
            check=check, # Raise CalledProcessError if return code != 0 if True
            timeout=timeout # Add a timeout
        )
        # Log warnings for non-zero exit codes if not checking
        if process.returncode != 0 and not check:
            print(f"    WARNING: Tool '{command[0]}' exited with code {process.returncode}.")
            if process.stderr:
                # Limit stderr length in logs to avoid flooding
                stderr_preview = process.stderr.strip()[:500]
                print(f"    Tool Stderr (preview):\n{stderr_preview}{'...' if len(process.stderr.strip()) > 500 else ''}")
        # Return stdout on success or non-checked failure
        return process.stdout

    except FileNotFoundError:
        print(f"    ERROR: Command not found: '{command[0]}'. Is it installed and in PATH?")
        return None
    except subprocess.TimeoutExpired:
        print(f"    ERROR: Tool '{command[0]}' timed out after {timeout} seconds.")
        return None
    except subprocess.CalledProcessError as e:
        # This happens if check=True and return code is non-zero
        print(f"    ERROR: Tool '{command[0]}' failed (Exit Code {e.returncode}).")
        # stderr/stdout are captured in the exception object
        if e.stdout: print(f"    Tool Stdout:\n{e.stdout.strip()}")
        if e.stderr: print(f"    Tool Stderr:\n{e.stderr.strip()}")
        return None # Indicate failure
    except Exception as e:
        # Catch other potential errors (e.g., permissions)
        print(f"    ERROR: Failed running tool '{command[0]}': {e}")
        return None

# --- Metric Parsing Functions ---

def parse_lizard_output(lizard_output):
    """Parses Lizard complexity and function length output."""
    metrics = {}
    if not lizard_output: return metrics
    lines = lizard_output.strip().split('\n')
    complexities, function_locs, total_nloc = [], [], 0
    try:
        # Find the summary line first (usually last or second to last)
        summary_line = None
        nloc_line = None
        for line in reversed(lines):
            if "NLOC" in line and "Avg." in line and "File" not in line: # Typical summary line format
                summary_line = line
            if "Total nloc" in line: # Older format or specific cases
                nloc_line = line
            if summary_line and nloc_line: # Stop if both found
                break

        # Extract total NLOC from summary or dedicated line
        if summary_line:
            match = re.search(r'\s+(\d+)\s+@\s+End', summary_line) # NLOC often before @ End
            if match: total_nloc = int(match.group(1))
        if total_nloc == 0 and nloc_line: # Fallback to "Total nloc =" line
            match = re.search(r'Total nloc\s*=\s*(\d+)', nloc_line)
            if match: total_nloc = int(match.group(1))
        if total_nloc > 0 : metrics['loc_code_lizard'] = total_nloc # Use Lizard's NLOC if available

        # Parse function details from the main table part
        for line in lines:
             # Look for lines starting with numbers (line no, CCN, token CCN, NLOC, name, ...)
             parts = line.split()
             if len(parts) >= 5 and parts[0].isdigit() and parts[1].isdigit() and parts[3].isdigit():
                 # Assuming format: line_no CCN tCCN NLOC func_name ...
                 try:
                     complexities.append(int(parts[1])) # Cyclomatic Complexity
                     function_locs.append(int(parts[3])) # NLOC for the function
                 except ValueError:
                     continue # Skip lines that don't parse correctly

        if complexities:
            metrics['cyclomatic_complexity_max'] = max(complexities)
            metrics['cyclomatic_complexity_avg'] = round(sum(complexities) / len(complexities), 2)
        if function_locs:
            metrics['function_loc_max'] = max(function_locs) # Max function length (NLOC)

    except Exception as e:
        print(f"    ERROR: Parsing Lizard output failed: {e}\nOutput was:\n{lizard_output[:500]}...")
    return metrics

def parse_cloc_output(cloc_json_output):
    """Parses cloc JSON output for LOC metrics."""
    metrics = {}
    if not cloc_json_output: return metrics
    try:
        cloc_data = json.loads(cloc_json_output)
        summary = cloc_data.get('SUM') # Summary block for multiple files/languages
        target_data = None

        if summary:
             target_data = summary # Use the summary if present
             print("    - Parsed cloc SUM block.")
        elif len(cloc_data) == 2 and "header" in cloc_data: # Check for single file case more reliably
            file_key = next((key for key in cloc_data if key != "header"), None)
            if file_key:
                 target_data = cloc_data[file_key]
                 print(f"    - Parsed cloc single file block ('{file_key}').")
        elif len(cloc_data) == 1 and "header" not in cloc_data: # Older single file case without header
            file_key = list(cloc_data.keys())[0]
            target_data = cloc_data[file_key]
            print(f"    - Parsed cloc legacy single file block ('{file_key}').")


        if target_data:
             metrics['loc_blank_cloc'] = target_data.get('blank', 0)
             metrics['loc_comment_cloc'] = target_data.get('comment', 0)
             metrics['loc_code_cloc'] = target_data.get('code', 0)
             # Calculate total LOC from components
             metrics['loc_total_cloc'] = sum([metrics['loc_blank_cloc'], metrics['loc_comment_cloc'], metrics['loc_code_cloc']])
        else:
             print(f"    WARNING: Could not find SUM or single file data block in cloc JSON output.")

    except json.JSONDecodeError:
        print(f"    ERROR: Decoding cloc JSON failed. Output (start):\n{cloc_json_output[:500]}...")
    except Exception as e:
        print(f"    ERROR: Processing cloc output failed: {e}")
    return metrics

# --- Dependency Counting Functions ---

def count_python_dependencies(file_path):
    """Counts unique base modules imported in a Python file."""
    modules = set()
    # Regex to capture the first part of the module name in import or from statements
    # Handles 'import x', 'import x.y', 'from x import ...', 'from x.y import ...'
    import_pattern = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z0-9_]+)")
    try:
        # Use context manager for file handling
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Simple comment skip
                if line.strip().startswith('#'): continue
                match = import_pattern.match(line)
                if match:
                    # Get the base module (e.g., 'os' from 'os.path')
                    base_module = match.group(1) # No need to split, pattern captures base
                    if base_module: modules.add(base_module)
        count = len(modules)
        print(f"    - Python Dependencies Found (base module count): {count} {sorted(list(modules)) if modules else ''}")
        return count
    except Exception as e:
        print(f"    ERROR: Counting Python dependencies failed: {e}")
        return 0 # Return 0 on error

def count_javascript_dependencies(file_path):
    """Counts unique non-relative module names in JS/TS require/import."""
    modules = set()
    # require('pkg') or require("pkg") - captures 'pkg'
    req_pattern = re.compile(r"""require\s*\(\s*['"]([^'"./][^'"]*)['"]\s*\)""")
    # import ... from 'pkg' or import ... from "pkg" - captures 'pkg'
    # Handles various import forms (named, default, namespace, side-effect)
    # Ensures module name doesn't start with '.' or '/' (non-relative)
    imp_pattern = re.compile(r"""import(?:[\s\S]*?from)?\s*['"]([^'"./][^'"]*)['"]""")
    try:
        # Use context manager for file handling
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Find all matches for require
        for match in req_pattern.finditer(content):
            modules.add(match.group(1))
        # Find all matches for import
        for match in imp_pattern.finditer(content):
            modules.add(match.group(1))
        count = len(modules)
        print(f"    - JS/TS Dependencies Found (non-relative count): {count} {sorted(list(modules)) if modules else ''}")
        return count
    except Exception as e:
        print(f"    ERROR: Counting JS/TS dependencies failed: {e}")
        return 0

def count_c_cpp_dependencies(file_path):
    """Counts unique system headers included via '#include <...>'. """
    modules = set()
    # Matches '#include <header.h>' or '#include <vector>' etc.
    include_pattern = re.compile(r"""^\s*#\s*include\s+<([^>]+)>""")
    try:
        # Use context manager for file handling
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: # Ignore encoding errors for C/C++
            for line in f:
                # Basic comment skip (simplistic, might miss block comments mid-line)
                stripped_line = line.strip()
                if stripped_line.startswith('//'): continue
                # Note: Doesn't handle multi-line /* ... */ comments robustly

                match = include_pattern.match(line)
                if match:
                    modules.add(match.group(1)) # Add the header name (e.g., 'stdio.h', 'vector')
        count = len(modules)
        print(f"    - C/C++ System Dependencies Found (#include <...> count): {count} {sorted(list(modules)) if modules else ''}")
        return count
    except Exception as e:
        print(f"    ERROR: Counting C/C++ dependencies failed: {e}")
        return 0


# --- Function to get static metrics ---
def get_static_metrics(file_path, language_key):
    """Calculate static analysis metrics using external tools."""
    metrics = {}
    if not os.path.exists(file_path):
        print(f"  ERROR: File not found for static analysis: {file_path}")
        return metrics

    print(f"\n  STATIC METRICS: Calculating for '{language_key or 'unknown lang'}' file: {os.path.basename(file_path)}")

    # --- Lizard (Complexity, Function Length, NLOC) ---
    lizard_path = shutil.which("lizard")
    if language_key and lizard_path: # Only run if language known and lizard installed
        print("    Running Lizard...")
        # Basic command
        lizard_cmd = [lizard_path, file_path]
        # Add language flag if supported by Lizard for potentially better parsing
        # List from lizard --languages, adapt if needed
        supported_lizard_langs = ['python', 'c', 'cpp', 'java', 'javascript', 'objectivec',
                                  'swift', 'csharp', 'ruby', 'ttcn', 'php', 'scala', 'gdscript',
                                  'go', 'lua', 'rust']
        if language_key in supported_lizard_langs:
            lizard_cmd.extend(["-l", language_key])
            print(f"      (Using language flag: -l {language_key})")
        else:
             print("      (Language not directly supported by Lizard flag, using auto-detection)")

        lizard_output = run_tool(lizard_cmd)
        if lizard_output is not None: # Check if run_tool succeeded
             metrics.update(parse_lizard_output(lizard_output))
             # Log what was parsed
             parsed_lizard = {k:v for k,v in metrics.items() if 'cyclomatic' in k or 'function_loc' in k or 'lizard' in k}
             print(f"    - Lizard Metrics Parsed: {parsed_lizard}")
        else:
             print("    - Lizard execution failed or returned no output.")

    elif language_key:
         print(f"    INFO: 'lizard' command not found or language key '{language_key}' unknown. Skipping Lizard metrics.")
    else:
         print("    INFO: Language key unknown. Skipping Lizard metrics.")


    # --- cloc (Code/Comment/Blank Lines) ---
    cloc_path = shutil.which("cloc")
    if cloc_path:
        print("    Running cloc...")
        # Use --json for easy parsing, --quiet to suppress progress messages
        cloc_output_json = run_tool([cloc_path, "--json", "--quiet", file_path])
        if cloc_output_json is not None:
            cloc_metrics = parse_cloc_output(cloc_output_json)
            metrics.update(cloc_metrics)
            # Log parsed cloc metrics
            parsed_cloc = {k:v for k,v in metrics.items() if 'cloc' in k}
            print(f"    - cloc Metrics Parsed: {parsed_cloc}")
            if 'loc_code_cloc' not in metrics:
                 print(f"    WARNING: Could not parse 'code' lines from cloc output.")
        else:
             print("    - cloc execution failed or returned no output.")
    else:
        print("    WARNING: 'cloc' command not found. Skipping cloc LOC metrics. (Install cloc for line counts)")

    # --- Language Specific Metrics ---
    if language_key == 'python':
        # Radon (Logical LOC for Python)
        radon_path = shutil.which("radon")
        if radon_path:
            print("    Running Radon (Logical LOC)...")
            # Use 'raw' command, '-s' to show summary including LLOC
            # Ensure python executable is found correctly
            python_exe = sys.executable or "python" # Fallback to just 'python'
            radon_raw_output = run_tool([python_exe, "-m", "radon", "raw", "-s", file_path])
            if radon_raw_output:
                # Regex to find the LLOC value in the summary output
                match = re.search(r"^\s*LLOC:\s*(\d+)", radon_raw_output, re.MULTILINE)
                if match:
                    try:
                        metrics['loc_logical_radon'] = int(match.group(1))
                        print(f"    - Logical LOC (radon): {metrics['loc_logical_radon']}")
                    except ValueError:
                        print("    ERROR: Could not parse LLOC value from Radon output.")
                else:
                    print("    WARNING: Could not find LLOC in Radon output.")
        else:
            print("    WARNING: 'radon' command not found. Skipping Python LLOC metric. (Install: pip install radon)")

        # Dependency Count (Python)
        print("    Counting Python Dependencies...")
        metrics['dependency_count'] = count_python_dependencies(file_path)

    elif language_key == 'javascript':
         # Dependency Count (JS/TS)
         print("    Counting JS/TS Dependencies...")
         metrics['dependency_count'] = count_javascript_dependencies(file_path)
         # Could add ESLint complexity check here if needed later

    elif language_key in ['c', 'cpp']:
         # Dependency Count (C/C++)
         print("    Counting C/C++ System Dependencies...")
         metrics['dependency_count'] = count_c_cpp_dependencies(file_path)
         # Could add cppcheck integration here if needed later

    # --- Log final metrics collected ---
    # Filter out None values before printing
    final_metrics_log = {k: v for k, v in metrics.items() if v is not None}
    print(f"  STATIC METRICS collected: {json.dumps(final_metrics_log)}")
    return metrics


def check_python_syntax(code_content, file_path_hint=""):
    """
    Checks Python code content for syntax errors using the 'ast' module.
    Safer and potentially faster than using py_compile on a temp file.

    Args:
        code_content (str): The Python code to check.
        file_path_hint (str): Original file path used for context in logs.

    Returns:
        bool: True if syntax is valid, False otherwise.
    """
    if not code_content:
        print("  SYNTAX CHECK: Skipping check for empty content.")
        return True # Treat empty content as valid syntax-wise

    print(f"  SYNTAX CHECK: Running 'ast.parse' on proposed code (from {os.path.basename(file_path_hint)})")
    try:
        ast.parse(code_content)
        print("  SYNTAX CHECK: Passed.")
        return True
    except SyntaxError as e:
        print(f"  ERROR: Syntax check failed. LLM output will be rejected.")
        # Provide specific error details from the exception
        print(f"    Error: {e.msg}")
        print(f"    Line:  {e.lineno}")
        print(f"    Offset:{e.offset}")
        # Show the problematic line if possible
        if e.lineno and e.lineno <= len(code_content.splitlines()):
             print(f"    Code:  {code_content.splitlines()[e.lineno-1].strip()}")
        return False
    except Exception as general_err:
        # Catch other potential errors during parsing (though less likely)
        print(f"  ERROR: Unexpected error during syntax check with 'ast.parse': {general_err}")
        return False


# --- Scoring Calculation Functions ---

def calculate_normalized_score(metric_name, value, config_details):
    """ Calculates a normalized score (0-100) for a single metric. """
    # config_details is the dict like {'good': x, 'bad': y, 'weight': z}
    good = config_details['good']
    bad = config_details['bad']
    weight = config_details['weight']

    # Handle edge case where good and bad are the same
    if good == bad:
        # Score is 100 if value matches the target, 0 otherwise
        score = 100.0 if value == good else 0.0
        return score, weight

    score = 0.0
    # Determine if lower is better or higher is better
    if good < bad: # Lower values are better (e.g., complexity, function length, density)
        if value <= good:
            score = 100.0
        elif value >= bad:
            score = 0.0
        else:
            # Linear interpolation between good and bad
            score = 100.0 * (bad - value) / (bad - good)
    else: # Higher values are better (e.g., potentially code coverage if added later)
        if value >= good:
            score = 100.0
        elif value <= bad:
            score = 0.0
        else:
            # Linear interpolation between bad and good
            score = 100.0 * (value - bad) / (good - bad)

    # Clamp score between 0 and 100
    score = max(0.0, min(100.0, score))
    return score, weight

def calculate_total_score(metrics, language_key):
    """
    Calculates the total weighted sustainability score based on collected metrics.
    Includes calculation for complexity density.
    Returns the score (0-100) and a dictionary of individual metric scores.
    """
    if not language_key or language_key not in SCORING_CONFIG:
        print(f"  SCORE: No scoring configuration found for language key '{language_key}'. Cannot calculate score.")
        return 0, {}

    lang_config = SCORING_CONFIG[language_key]
    total_score = 0.0
    total_weight = 0.0
    individual_scores = {}
    processed_metrics = metrics.copy() # Work on a copy to add derived metrics

    print(f"  SCORE: Calculating score using config for '{language_key}'")

    # --- Calculate Derived Metrics (Complexity Density) ---
    avg_ccn = processed_metrics.get('cyclomatic_complexity_avg') # Need average CCN

    # Python: Prefer Radon Logical LOC for density
    if language_key == 'python' and avg_ccn is not None and 'loc_logical_radon' in processed_metrics:
        lloc = processed_metrics['loc_logical_radon']
        if lloc is not None and lloc > 0:
            density = avg_ccn / lloc
            # Store using the standard 'complexity_density' key for Python
            processed_metrics['complexity_density'] = round(density, 4)
            print(f"    - Calculated Complexity Density (Python: CCN Avg / Radon LLOC): {processed_metrics['complexity_density']:.4f}")
        elif lloc == 0:
             print("    - INFO: Radon LLOC is 0, cannot calculate Python complexity density.")
        # else: # avg_ccn or lloc is None
             # print("    - INFO: Missing avg CCN or Radon LLOC for Python density calculation.") # Optional debug

    # C/C++: Use cloc code lines for density (or Python fallback if Radon failed)
    # The key in SCORING_CONFIG for this is 'complexity_density_cloc'
    density_metric_name_cloc = 'complexity_density_cloc'
    # Check if the cloc-based density metric is defined in the config for this language
    if density_metric_name_cloc in lang_config:
        # Check if we *need* to calculate it (either not Python, or Python density failed)
        # and if we have the necessary inputs
        if ('complexity_density' not in processed_metrics and # Python density wasn't calculated
            avg_ccn is not None and
            'loc_code_cloc' in processed_metrics):
                cloc_loc = processed_metrics['loc_code_cloc']
                if cloc_loc is not None and cloc_loc > 0:
                    density_cloc = avg_ccn / cloc_loc
                    # Store using the specific 'complexity_density_cloc' key
                    processed_metrics[density_metric_name_cloc] = round(density_cloc, 4)
                    print(f"    - Calculated Complexity Density ({language_key}: CCN Avg / cloc LOC): {processed_metrics[density_metric_name_cloc]:.4f}")
                elif cloc_loc == 0:
                     print(f"    - INFO: cloc LOC is 0, cannot calculate {language_key} complexity density.")
                # else: # avg_ccn or cloc_loc is None
                     # print(f"    - INFO: Missing avg CCN or cloc LOC for {language_key} density calculation.") # Optional debug

    # --- Score Calculation Loop ---
    # Iterate through the metrics defined *in the config* for the language
    for metric_name, config_details in lang_config.items():
        # Check if this metric (including derived ones like density) exists in our collected/processed metrics
        if metric_name in processed_metrics:
            value = processed_metrics[metric_name]
            # Ensure value is not None before scoring
            if value is None:
                 # print(f"    INFO: Metric '{metric_name}' has value None, skipping score calculation.") # Optional debug
                 continue

            # Use the helper function to get normalized score and weight
            score, weight = calculate_normalized_score(metric_name, value, config_details)

            # Only include if score calculation was successful and weight > 0
            if score is not None and weight > 0:
                # print(f"    Metric '{metric_name}': Value={value}, Score={score:.1f}, Weight={weight}") # Debug print
                total_score += score * weight
                total_weight += weight
                # Store individual results for potential reporting later
                individual_scores[metric_name] = {'value': value, 'score': round(score, 1), 'weight': weight}
        # else: # Metric in config but not found in collected/derived metrics
             # print(f"    INFO: Metric '{metric_name}' for scoring not found in collected/derived metrics.") # Optional debug noise

    # Normalize the total score by the total weight considered
    if total_weight > 0:
        final_score = total_score / total_weight
    else:
        # Handle case where no metrics were scored (e.g., all tools failed, or config was empty)
        final_score = 0
        print("  SCORE: Warning - Total weight considered is 0. No metrics were scored.")


    # Ensure final score is within bounds [0, 100] and round
    final_score = max(0.0, min(100.0, round(final_score, 1)))

    print(f"  SCORE: Calculated Total Score = {final_score:.1f} (Total Weight Considered: {total_weight:.1f})")
    # Optional: Print individual scores for debugging
    # print("  Individual Scores:")
    # for name, data in individual_scores.items():
    #    print(f"    - {name}: Value={data['value']}, Score={data['score']}/100, Weight={data['weight']}")

    return final_score, individual_scores


# --- CodeCarbon Measurement Function (Keep as before) ---
def measure_python_emissions(code_content, file_path_hint, stage_name, timeout_seconds=60):
    """ Measures Python emissions using CodeCarbon. Requires executable script."""
    if not CODECARBON_AVAILABLE:
        print("  MEASUREMENT: CodeCarbon library not found. Skipping emission measurement.")
        return None
    if not code_content:
        print("  MEASUREMENT: No code content provided. Skipping emission measurement.")
        return None
    # Check for a main execution block - heuristic for executability
    if not re.search(r'if __name__\s*==\s*["\']__main__["\']\s*:', code_content):
         print(f"  MEASUREMENT: No `if __name__ == '__main__':` block found in {os.path.basename(file_path_hint)}. "
               "Assuming not directly executable. Skipping measurement.")
         return None

    print(f"\n===== CodeCarbon Measurement ({stage_name.upper()}) for {os.path.basename(file_path_hint)} =====")
    emissions_kg = None
    # Use a temporary directory for the script and potential CodeCarbon output within it
    temp_dir = tempfile.mkdtemp(prefix="codecarbon_exec_")
    try:
        # Create a temporary Python file to execute
        temp_py_file_path = os.path.join(temp_dir, f"temp_script_{stage_name}_{os.path.basename(file_path_hint)}")
        with open(temp_py_file_path, "w", encoding="utf-8") as f:
            f.write(code_content)

        # Configure CodeCarbon tracker
        # Unique project name per run/stage/file to avoid conflicts if run concurrently
        project_name = f"sustain_{os.path.splitext(os.path.basename(file_path_hint))[0]}_{stage_name}_{os.getpid()}"
        # Place the report in a dedicated sub-directory within the temp dir
        output_dir = os.path.join(temp_dir, "codecarbon_report")
        os.makedirs(output_dir, exist_ok=True) # Ensure the output dir exists

        print(f"  Starting CodeCarbon tracker (Project: {project_name}, Output Dir: {output_dir})")
        # Lower log level to reduce console noise from CodeCarbon itself
        tracker = EmissionsTracker(
            project_name=project_name,
            output_dir=output_dir,
            log_level='warning', # Or 'error' for even less noise
            save_to_file=True # Ensure CSV report is saved
        )

        tracker.start()
        process = None
        execution_success = False
        try:
            print(f"  Executing: {sys.executable} {os.path.basename(temp_py_file_path)} (in {temp_dir})")
            process = subprocess.Popen(
                [sys.executable, temp_py_file_path], # Execute the temp script
                cwd=temp_dir, # Run from the temp directory
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            # Wait for process to finish, with timeout
            stdout, stderr = process.communicate(timeout=timeout_seconds)

            print(f"  Execution finished with code: {process.returncode}")
            if process.returncode == 0:
                execution_success = True
            else:
                print(f"  WARNING: Script execution failed ({stage_name}). Measurement might be inaccurate or incomplete.")
                if stderr:
                    stderr_preview = stderr.strip()[:500]
                    print(f"  Stderr (preview):\n{stderr_preview}{'...' if len(stderr.strip()) > 500 else ''}")
            # Optional stdout print for debugging
            # if stdout: print(f"  Stdout:\n{stdout.strip()}")

        except subprocess.TimeoutExpired:
            print(f"  ERROR: Script execution timed out after {timeout_seconds} seconds ({stage_name}). Killing process.")
            if process:
                try: process.kill()
                except OSError: pass # Ignore if already terminated
                # Try to communicate once more to gather any final output
                try: process.communicate(timeout=1)
                except Exception: pass
            execution_success = False # Timed out, not successful
        except Exception as e:
            print(f"  ERROR: Failed to execute script ({stage_name}): {e}")
            execution_success = False
        finally:
            # Stop the tracker regardless of execution success/failure
            try:
                # stop() returns emissions in kg CO2eq or None if tracking failed/duration too short
                emissions_data = tracker.stop()
                if isinstance(emissions_data, float):
                    emissions_kg = emissions_data
                    print(f"  CodeCarbon measurement complete ({stage_name}): {emissions_kg:.9f} kg CO₂eq")
                elif execution_success: # Execution finished but tracker didn't return float
                    # This often happens if the script runs faster than CodeCarbon's measurement interval (default 15s)
                    print(f"  WARNING: CodeCarbon tracker returned non-float ({emissions_data}) for emissions ({stage_name}). "
                          "Execution might have been too fast for measurement, or tracker encountered an issue.")
                    emissions_kg = 0.0 # Report as zero if execution was successful but too fast
                else: # Execution failed AND tracker didn't return float
                     print(f"  INFO: CodeCarbon tracker returned non-float ({emissions_data}) after failed execution ({stage_name}).")
                     emissions_kg = None # Report None if execution failed

            except Exception as e:
                print(f"  ERROR: Failed to stop CodeCarbon tracker ({stage_name}): {e}")
                emissions_kg = None # Failed to stop, no valid data

    except Exception as e:
        print(f"  ERROR: Unexpected error during emission measurement setup ({stage_name}): {e}")
        emissions_kg = None
    finally:
        # Cleanup the temporary directory
        if temp_dir and os.path.exists(temp_dir):
             try:
                 shutil.rmtree(temp_dir)
                 # print(f"  Cleaned up temporary directory: {temp_dir}") # Less verbose
             except Exception as e:
                 print(f"  WARNING: Failed to clean up temp dir {temp_dir}: {e}")
    print(f"===== CodeCarbon Measurement ({stage_name.upper()}) END =====")
    return emissions_kg


# --- Main Analysis Function (MODIFIED with Enhanced Prompts, No Semgrep) ---
def analyze_and_update_code_for_sustainability(
    file_path,
    api_key_file="api_key.txt",
    changes_only=False,
    forced_language=None,
    measure_emissions=False,
    execution_timeout=60,
    skip_llm_flag=False,
    full_file_mode=False
    ):
    """
    Main analysis workflow: Enhanced metrics/scoring/density, Enhanced LLM prompts, Syntax Check.
    """
    print(f"\n===== SUSTAINABILITY ANALYSIS & UPDATE: {file_path} =====")

    # --- PREP ---
    language_name, language_key = detect_language(file_path, forced_language)
    can_measure = measure_emissions and language_key == 'python' and CODECARBON_AVAILABLE
    if measure_emissions and language_key != 'python':
        print("  INFO: Emission measurement requested, but only supported for Python scripts. Skipping.")
    if measure_emissions and language_key == 'python' and not CODECARBON_AVAILABLE:
        print("  WARNING: Emission measurement requested for Python, but CodeCarbon library not found. Skipping.")

    # --- STEP 1: Get Code Content ---
    print("\nSTEP 1: Retrieving file content for analysis")
    staged_content, original_content, change_blocks = None, None, []
    is_modified_file = False # Flag to know if we're dealing with changes to an existing file

    if full_file_mode:
         print("  Mode: Full File (reading directly from disk)")
         try:
            # Use context manager for file reading
            with open(file_path, 'r', encoding='utf-8') as f:
                staged_content = f.read()
            print(f"  Successfully read file content ({len(staged_content)} bytes)")
            # In full file mode, we don't compare to HEAD
            original_content, change_blocks, is_modified_file = None, [], False
         except Exception as e:
             print(f"ERROR: Failed to read file {file_path}: {e}")
             return False # Cannot proceed without content
    else:
        print("  Mode: Git Staged (comparing staged version to HEAD if possible)")
        content_data = analyze_code_changes(file_path) # Uses Git commands
        if not content_data or content_data.get("modified") is None:
            print("ERROR: Failed to retrieve file content using Git. Cannot analyze.")
            # Attempt fallback to direct read? Or just fail? Let's fail for now.
            # If git fails, something is wrong with the setup or file state.
            return False
        staged_content = content_data["modified"] # The version we will analyze/optimize
        original_content = content_data.get("original") # HEAD version, if available
        change_blocks = content_data.get("change_blocks", [])
        is_modified_file = content_data.get("is_modified", False) # Was it a change vs HEAD?

    if staged_content is None: # Should not happen if checks above are correct, but safeguard
         print("FATAL ERROR: Staged content is None after retrieval step.")
         return False

    # --- STEP 1.5: Static Analysis & Scoring BEFORE ---
    # Create a temporary file with the staged content for analysis tools
    temp_before_file = None
    metrics_before = {}
    score_before = 0
    individual_scores_before = {}
    try:
        # Use context manager for temporary file creation
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=os.path.splitext(file_path)[1], encoding='utf-8') as temp_f:
            temp_f.write(staged_content)
            temp_before_file = temp_f.name
        print(f"\nSTEP 1.5: Static Analysis & Scoring (BEFORE) on temp file: {temp_before_file}")
        metrics_before = get_static_metrics(temp_before_file, language_key)
        score_before, individual_scores_before = calculate_total_score(metrics_before, language_key)
    except Exception as e:
        print(f"ERROR: Failed during BEFORE static analysis: {e}")
    finally:
        # Ensure cleanup of the temporary file
        if temp_before_file and os.path.exists(temp_before_file):
            try: os.remove(temp_before_file)
            except OSError: print(f"Warning: Failed to remove temp file {temp_before_file}")


    # --- STEP 1.6: Measure Emissions BEFORE ---
    emissions_before = None
    if can_measure:
        emissions_before = measure_python_emissions(staged_content, file_path, "before", execution_timeout)

    # --- STEP 2 & 3: Determine LLM Skip & Optimize ---
    optimized_full_code = None # This will hold the final code (optimized or original)
    llm_skip_reason = None
    should_skip_llm = skip_llm_flag # Start with the command-line flag

    # Check other skip conditions only if the flag didn't already force skip
    if not should_skip_llm:
        if score_before >= PERFECT_SCORE_THRESHOLD:
            should_skip_llm = True
            llm_skip_reason = f"Initial score ({score_before:.1f}) meets/exceeds threshold ({PERFECT_SCORE_THRESHOLD:.1f})"
        # Check LOC limit using cloc data if available
        elif 'loc_code_cloc' in metrics_before and metrics_before['loc_code_cloc'] is not None and metrics_before['loc_code_cloc'] > LLM_LOC_LIMIT:
            should_skip_llm = True
            llm_skip_reason = f"Code LOC ({metrics_before['loc_code_cloc']}) exceeds limit ({LLM_LOC_LIMIT})"
        elif not language_key: # Also skip if language unknown (can't give good prompts)
            should_skip_llm = True
            llm_skip_reason = "Language could not be determined, cannot provide specific LLM guidance"
        elif not staged_content.strip(): # Skip if file is empty or whitespace only
             should_skip_llm = True
             llm_skip_reason = "File content is empty"


    if skip_llm_flag and not llm_skip_reason:
        llm_skip_reason = "Command line flag (--skip-llm)"

    # --- LLM Optimization or Skip ---
    if should_skip_llm:
        print(f"\nSTEP 2 & 3: Skipping LLM Optimization ({llm_skip_reason})")
        # If skipping LLM, the "optimized" code is just the original staged content
        optimized_full_code = staged_content
    else:
        # --- Proceed with LLM Optimization ---
        print("\nSTEP 2: Preparing API access for LLM")
        api_key = get_api_key(api_key_file)
        if not api_key:
             print("ERROR: No API key found or loaded. Skipping LLM optimization.")
             optimized_full_code = staged_content # Fallback to original
        else:
            print("\nSTEP 3: Optimizing code with Groq API")
            system_prompt = get_language_specific_system_prompt(language_name) # Includes anti-pattern guidance
            # Use language key for code block hint if available, else simplified name
            code_block_lang_hint = language_key or language_name.lower().split()[0]

            # Determine if we should analyze only changed blocks
            # Requires: --changes-only flag, git mode (not --full-file-mode),
            #           file existed before (is_modified_file), and changes were found
            analyze_llvm_changes = changes_only and not full_file_mode and is_modified_file and change_blocks

            temp_llm_output = None # Variable to store the raw output from the LLM

            # --- *** ENHANCED LLM PROMPTS (Strategy 3 Integration) *** ---
            # The anti-pattern guidance is now part of the get_language_specific_system_prompt

            if analyze_llvm_changes:
                print(f"  LLM Mode: Analyzing only {len(change_blocks)} changed block(s)")
                optimized_blocks = [] # Store optimized version of each block
                all_blocks_processed_successfully = True

                # --- Loop through change blocks ---
                for i, block in enumerate(change_blocks):
                    code_to_optimize = '\n'.join(block['modified_lines'])
                    # Skip empty blocks (e.g., only deletions)
                    if not code_to_optimize.strip():
                       # If the block was purely a deletion, the "optimized" version is empty
                       # If it was whitespace, keep it empty
                       optimized_blocks.append("")
                       print(f"    Skipping empty block {i+1}")
                       continue

                    # --- Enhanced Block-Level User Prompt ---
                    # Focuses on the segment and asks for anti-pattern fixing within it
                    block_prompt = f"""You are optimizing ONLY the following code segment from a larger {language_name} file for sustainability and efficiency.
Focus on CPU, memory, I/O reduction, and algorithm optimization within this segment.
Specifically look for and refactor common performance anti-patterns *within this segment* (like inefficient loops, unnecessary calculations, poor data structure use, resource handling relevant to {language_name}).

Constraints for optimizing THIS SEGMENT:
- Return ONLY the optimized code segment.
- Do NOT add any explanations, comments about changes, or markdown formatting (like ```).
- Ensure all original comments within the segment are retained. # <--- Added
- Do NOT introduce new library imports/requires.
- Do NOT define new functions or classes outside the original scope of the segment.
- Preserve the core functionality and intended purpose of the segment.
- Preserve the exact observable output and side effects (e.g., print statements) of the segment. # <--- Added
- Minor efficiency improvements unrelated to the core sustainability anti-patterns are acceptable ONLY IF they strictly adhere to all other constraints (especially preserving output, comments, and functionality). The primary focus remains sustainability optimization. # <--- Added nuance
- Try to maintain the relative indentation of the code within the segment.
- Ensure the returned segment is syntactically valid IN THE CONTEXT where it will be placed back into the original file.

Code Segment to Optimize:
```""" + code_block_lang_hint + f"""
{code_to_optimize}
```"""
                    try:
                        print(f"    Sending block {i+1} ({len(code_to_optimize)} chars) to Groq API...")
                        response = requests.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": "llama3-8b-8192", # Or other suitable model
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": block_prompt},
                                ],
                                "temperature": 0.1, # Low temperature for more deterministic output
                                "max_tokens": 2048, # Adjust as needed for block size
                            },
                             timeout=60 # Timeout for API call
                        )
                        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                        response_data = response.json()
                        if not response_data.get("choices") or not response_data["choices"][0].get("message"):
                             raise ValueError("LLM response format unexpected (missing choices/message)")

                        optimized_code_segment = response_data["choices"][0]["message"]["content"]
                        # Clean up potential markdown code blocks returned by the LLM
                        optimized_code_segment = re.sub(r'^```[\w]*\n?|\n?```$', '', optimized_code_segment, flags=re.MULTILINE).strip()

                        optimized_blocks.append(optimized_code_segment)
                        print(f"    Block {i+1} optimization received ({len(optimized_code_segment)} chars)")

                    except requests.exceptions.Timeout:
                        print(f"    ERROR: API request timed out for block {i+1}. Aborting LLM optimization.")
                        all_blocks_processed_successfully = False; break
                    except requests.exceptions.RequestException as e:
                        print(f"    ERROR: API request failed for block {i+1}: {e}. Aborting LLM optimization.")
                        all_blocks_processed_successfully = False; break
                    except (ValueError, KeyError) as e:
                         print(f"    ERROR: Failed to parse LLM response for block {i+1}: {e}. Aborting LLM optimization.")
                         all_blocks_processed_successfully = False; break
                    except Exception as e:
                        print(f"    ERROR: Unexpected error processing block {i+1}: {e}. Aborting LLM optimization.")
                        all_blocks_processed_successfully = False; break
                # --- End block loop ---

                # If any block failed, fallback to original content
                if not all_blocks_processed_successfully:
                    temp_llm_output = staged_content # Fallback
                    print("  INFO: Reverting to original staged content due to error during block processing.")
                else:
                    # Reconstruct the file from original + optimized blocks
                    print("\nSTEP 3.5: Reconstructing file from optimized blocks")
                    temp_llm_output = apply_selective_changes(staged_content, change_blocks, optimized_blocks)
                    if temp_llm_output is None:
                        print("  ERROR: Failed to reconstruct file from optimized blocks. Reverting to original.")
                        temp_llm_output = staged_content # Fallback on reconstruction error

            else: # Full file LLM analysis
                 llm_mode_reason = "Full file mode requested (--full-file-mode)" if full_file_mode else \
                                   "Changes span too much or --changes-only not used" if is_modified_file else \
                                   "Analyzing a new file"
                 print(f"  LLM Mode: Analyzing full file ({llm_mode_reason})")

                 # --- Enhanced Full File User Prompt ---
                 # Contextualizes the request for the entire file, including anti-patterns
                 prompt_content_header = f"Optimize the following {language_name} code for sustainability and efficiency."
                 code_section_to_optimize = staged_content

                 # Provide original code as context if analyzing changes to an existing file
                 if original_content is not None and not full_file_mode:
                     prompt_content_header = (f"The following {language_name} code was modified. "
                                              f"Optimize the MODIFIED version for sustainability and efficiency, "
                                              f"considering the ORIGINAL for context.")
                     code_section_to_optimize = (f"--- ORIGINAL CODE ---\n"
                                                 f"```{code_block_lang_hint}\n{original_content}\n```\n\n"
                                                 f"--- MODIFIED CODE (Optimize This) ---\n"
                                                 f"```{code_block_lang_hint}\n{staged_content}\n```")

                 full_prompt = f"""{prompt_content_header}

Focus on reducing CPU usage, minimizing memory consumption, optimizing algorithms and data structures, and reducing I/O operations.
Specifically look for and refactor common performance anti-patterns appropriate for {language_name} throughout the code (e.g., inefficient loops/algorithms, unnecessary object creation, poor data structure choices, resource leaks if applicable).

Return ONLY the fully optimized version of the {'MODIFIED code section' if original_content is not None and not full_file_mode else 'entire code'}.
Do NOT include any explanations, comments about the changes you made, or markdown formatting (like ```language ... ``` wrappers). Just output the raw, optimized code.
Ensure all original comments are retained. # <--- Added
Ensure the exact observable output and side effects (e.g., print statements) are preserved. # <--- Added
Minor efficiency improvements unrelated to the core sustainability anti-patterns are acceptable ONLY IF they strictly adhere to all other constraints (especially preserving output, comments, and functionality). The primary focus remains sustainability optimization. # <--- Added nuance

{code_section_to_optimize}"""

                 try:
                    print(f"  Sending full file prompt ({len(full_prompt)} chars) to Groq API...")
                    response = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "llama3-8b-8192", # Adjust model if needed
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": full_prompt},
                            ],
                            "temperature": 0.1,
                            "max_tokens": 4096, # Larger allowance for full files
                        },
                         timeout=180 # Longer timeout for potentially larger files
                    )
                    response.raise_for_status()

                    response_data = response.json()
                    if not response_data.get("choices") or not response_data["choices"][0].get("message"):
                        raise ValueError("LLM response format unexpected (missing choices/message)")

                    llm_output_raw = response_data["choices"][0]["message"]["content"]

                    # --- BUG FIX START ---
                    # Initialize cleaned_output from the raw LLM output FIRST
                    cleaned_output = llm_output_raw

                    # 1. Clean potential markdown code blocks from the raw output
                    cleaned_output = re.sub(r'^```[\w]*\n?|\n?```$', '', cleaned_output, flags=re.MULTILINE).strip()

                    # 2. Remove common preamble lines (case-insensitive)
                    preamble_patterns = [
                        r"^\s*here[' i]*s the (optimized|updated|modified)?\s*code:?\s*$",
                        r"^\s*okay, here[' i]*s the code:?\s*$",
                        r"^\s*sure, here[' i]*s the code:?\s*$",
                        # Add more common patterns if observed
                    ]
                    lines = cleaned_output.splitlines() # Use the result from step 1
                    found_code = False
                    start_index = 0
                    for i, line in enumerate(lines):
                        is_preamble = any(re.match(pattern, line, re.IGNORECASE) for pattern in preamble_patterns)
                        # Check for empty lines only *immediately* after potential preamble lines or near start
                        is_empty_near_start = not line.strip() and i < 5

                        if not is_preamble and not is_empty_near_start:
                             # Assume the first non-preamble, non-empty line is the start of the code
                             start_index = i
                             found_code = True
                             break
                        # If it IS a preamble line or empty near start, continue searching

                    if found_code:
                        cleaned_output = '\n'.join(lines[start_index:]) # Update cleaned_output
                    #else: # If only preamble/empty lines were found, cleaned_output retains its value from step 1

                    # 3. Final strip just in case (applied to the potentially updated cleaned_output)
                    cleaned_output = cleaned_output.strip()
                    # --- BUG FIX END ---

                    # Assign to temp_llm_output only if cleaning resulted in non-empty string
                    if cleaned_output:
                        temp_llm_output = cleaned_output
                        # Try to preserve trailing newline consistency
                        if staged_content.endswith('\n') and not temp_llm_output.endswith('\n'):
                            temp_llm_output += '\n'
                        print(f"  Full file optimization received ({len(temp_llm_output)} chars)")
                    else:
                         print("  WARNING: LLM returned empty content after cleanup. Reverting.")
                         temp_llm_output = staged_content # Fallback

                 except requests.exceptions.Timeout:
                    print("  ERROR: API request timed out for full file. Reverting.")
                    temp_llm_output = staged_content # Fallback
                 except requests.exceptions.RequestException as e:
                    print(f"  ERROR: API request failed for full file: {e}. Reverting.")
                    temp_llm_output = staged_content # Fallback
                 except (ValueError, KeyError) as e:
                    print(f"  ERROR: Failed to parse LLM response for full file: {e}. Reverting.")
                    temp_llm_output = staged_content # Fallback
                 except Exception as e:
                    # Catch the specific error observed if possible, otherwise general exception
                    # The original error was "local variable 'cleaned_output' referenced before assignment"
                    # which is now fixed, but keep general catch.
                    print(f"  ERROR: Unexpected error during full file optimization: {e}. Reverting.")
                    temp_llm_output = staged_content # Fallback

            # --- STEP 3.6: Syntax Check --- (Crucial Safety Net)
            print("\nSTEP 3.6: Performing Syntax Check on LLM Output")
            syntax_is_valid = False
            # Check if LLM produced *any* output (could be None if errors occurred before assignment)
            if temp_llm_output is None or temp_llm_output == staged_content:
                 print("  INFO: LLM output same as original or processing failed before check. Skipping syntax check.")
                 # If it's the same as original, it's considered valid by definition here
                 # If it failed before, we are using original staged content
                 optimized_full_code = staged_content
                 syntax_is_valid = True # Treat as valid as it's the original code
            elif language_key == 'python':
                 # Use the 'ast' based check
                 syntax_is_valid = check_python_syntax(temp_llm_output, file_path)
                 if syntax_is_valid:
                     optimized_full_code = temp_llm_output # Accept LLM output
                 else:
                     print("  Syntax check failed. REVERTING to original staged content.")
                     optimized_full_code = staged_content # REJECT LLM output
            else:
                 # For non-Python, assume valid for now (no check implemented)
                 print(f"  INFO: Syntax check not implemented for language '{language_name}'. Assuming LLM output is valid.")
                 optimized_full_code = temp_llm_output # Accept LLM output
                 syntax_is_valid = True # Set true for non-python checks

            # Log final decision based on syntax check
            if optimized_full_code == staged_content and not should_skip_llm and temp_llm_output != staged_content:
                 print("  Outcome: LLM changes were REVERTED due to syntax errors (or other failures).")
            elif optimized_full_code != staged_content:
                 print("  Outcome: LLM changes PASSED syntax check (or check not applicable).")
            # Else: LLM was skipped or produced identical code


    # --- Final Content Check ---
    # Ensure optimized_full_code is assigned (should always be either staged_content or valid LLM output by now)
    if optimized_full_code is None:
         print("FATAL ERROR: optimized_full_code is None before final steps. Reverting to staged_content.")
         optimized_full_code = staged_content
         if optimized_full_code is None: # If even staged_content was somehow None
             print("FATAL ERROR: No code content available to proceed.")
             return False

    # --- STEP 4 & 4.5: Write Final Code to Temp File & Analyze AFTER ---
    # We need to analyze the final code that will be written, even if it's the original
    temp_after_file = None
    metrics_after = {}
    score_after = 0
    individual_scores_after = {}
    try:
        # Create a temporary file with the FINAL code content
        # Use context manager for temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=os.path.splitext(file_path)[1], encoding='utf-8') as temp_f:
            temp_f.write(optimized_full_code)
            temp_after_file = temp_f.name
        print(f"\nSTEP 4 & 4.5: Wrote final code to temp file for AFTER analysis: {temp_after_file}")

        # Run static analysis on the final code in the temp file
        metrics_after = get_static_metrics(temp_after_file, language_key)
        score_after, individual_scores_after = calculate_total_score(metrics_after, language_key)

    except Exception as e:
        print(f"ERROR: Failed during AFTER static analysis: {e}")
        # Metrics/score after will remain empty/zero
    finally:
        # Ensure cleanup of the temporary file
        if temp_after_file and os.path.exists(temp_after_file):
            try: os.remove(temp_after_file)
            except OSError: print(f"Warning: Failed to remove temp file {temp_after_file}")


    # --- STEP 5: Measure Emissions AFTER ---
    emissions_after = None
    if can_measure:
        # Measure emissions on the FINAL code content
        emissions_after = measure_python_emissions(optimized_full_code, file_path, "after", execution_timeout)

    # --- STEP 6: Update Original File (if changed) ---
    update_needed = (optimized_full_code != staged_content)
    write_success = False
    if update_needed:
        print("\nSTEP 6: Changes detected. Updating original file with modified code.")
        try:
            # Write the final, validated code back to the original file path
            # Use context manager for writing
            with open(file_path, 'w', encoding='utf-8') as output_file:
                output_file.write(optimized_full_code)
            print(f"  File successfully updated: {file_path}")
            write_success = True
        except Exception as e:
            print(f"ERROR: Failed to write updated code to {file_path}: {e}")
            write_success = False # Failed to write the changes
    else:
        print("\nSTEP 6: No changes applied (LLM skipped, reverted, or produced identical code). File not modified.")
        write_success = True # No write needed, so considered successful in terms of file state

    # --- STEP 7: Report Scores and Emissions Comparison ---
    print("\n===== Sustainability Score Summary =====")
    print(f"  Score BEFORE: {score_before:.1f}/100")
    print(f"  Score AFTER:  {score_after:.1f}/100") # Will be same as before if no changes applied/kept
    score_diff = score_after - score_before
    print(f"  Difference: {score_diff:+.1f} points")

    # Report detailed metrics diff if verbose? (Optional future enhancement)

    if can_measure:
        print("\n===== CO₂eq Emissions Summary (Experimental) =====")
        if emissions_before is not None:
            print(f"  Emissions BEFORE: {emissions_before:.9f} kg CO₂eq")
        else:
            print("  Emissions BEFORE: Not measured or failed.")
        if emissions_after is not None:
             print(f"  Emissions AFTER:  {emissions_after:.9f} kg CO₂eq")
        else:
             print("  Emissions AFTER:  Not measured or failed.")

        if emissions_before is not None and emissions_after is not None:
             diff_emissions = emissions_after - emissions_before
             diff_percent = (diff_emissions / emissions_before * 100) if emissions_before != 0 else 0
             print(f"  Difference: {diff_emissions:+.9f} kg CO₂eq ({diff_percent:+.2f}%)")
        else:
             print("  Difference: Cannot calculate emission difference.")

    print(f"\n===== Analysis Complete for {file_path} =====")

    # Overall success is true if we didn't encounter fatal errors AND file write (if needed) succeeded
    return write_success


# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze code file for sustainability metrics, optionally optimize with LLM, "
                    "perform syntax checks, measure emissions (Python), and update the file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("file_path", help="Path to the code file to analyze and potentially update.")
    parser.add_argument("--api_key_file", default="api_key.txt", help="Path to file containing Groq API key.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable detailed logging (currently always on).") # Note: Verbose flag doesn't suppress output currently
    parser.add_argument("--changes-only", "-c", action="store_true",
                        help="LLM analyzes only staged changes (vs HEAD) if using Git mode. Ignored if --full-file-mode.")
    parser.add_argument("--language", "-l", help="Force specific language (e.g., 'Python', 'JavaScript'). Overrides automatic detection.")
    parser.add_argument("--list-supported", action="store_true", help="List languages with specific prompts/scoring keys and exit.")
    parser.add_argument("--measure-emissions", "-m", action="store_true",
                        help="[EXPERIMENTAL] Measure CO2 emissions using CodeCarbon. Requires executable Python script with a main block.")
    parser.add_argument("--execution-timeout", type=int, default=60,
                        help="Timeout (seconds) for script execution during emission measurement.")
    parser.add_argument("--skip-llm", action="store_true",
                        help="Force skipping the LLM optimization step entirely, regardless of score or LOC.")
    parser.add_argument("--full-file-mode", action="store_true",
                        help="Read file directly from disk (skip Git diff/show). Useful for running outside a Git repo or on arbitrary files.")
    parser.add_argument("--check-tools", action="store_true", help="Check for required external analysis tools and exit.")

    args = parser.parse_args()

    # --- Tool Check ---
    if args.check_tools:
        print("Checking for required external tools...")
        # Specify which tools are core requirements vs optional/language-specific
        tools = {
            # Core for metrics:
            "lizard": ("pip install lizard", True, "Complexity, function length"),
            "cloc": ("sudo apt install cloc / brew install cloc / choco install cloc / etc.", True, "Line counts (code, comment, blank)"),
            # Core for non-full-file mode:
            "git": ("Install Git SCM from https://git-scm.com/", True, "Comparing staged vs HEAD, retrieving content"),
            # Language-specific optional:
            "radon": ("pip install radon", False, "Python Logical LOC (for density score)"),
            # Add others like eslint, cppcheck here if implemented later
        }
        all_required_found = True
        print("\nTool Status:")
        print("-" * 40)
        for tool, (install_cmd, required, purpose) in tools.items():
            req_str = "Required" if required else "Optional"
            status = "Found" if shutil.which(tool) else "NOT FOUND"
            print(f"  - {tool:<10} ({req_str:<8}): {status:<10} | Purpose: {purpose}")
            if status == "NOT FOUND":
                print(f"      Install/Setup: {install_cmd}")
                if required:
                    all_required_found = False

        print("-" * 40)
        if not all_required_found:
             print("\nERROR: One or more required tools are missing. Please install them and ensure they are in your system's PATH.")
             sys.exit(1)
        else:
             print("\nAll required tools found.")
             # Check CodeCarbon only if requested, as it's internal
             if args.measure_emissions:
                 if CODECARBON_AVAILABLE:
                     print("  - codecarbon (Python library): Found (for --measure-emissions)")
                 else:
                     print("  - codecarbon (Python library): NOT FOUND (Install: pip install codecarbon)")
                     print("      WARNING: --measure-emissions will be skipped.")
             sys.exit(0)

    # --- List Supported Languages ---
    if args.list_supported:
        print("\nLanguages/Keys with specific configuration:")
        print("-" * 40)
        print("System Prompts (for LLM):")
        # Extract keys from the get_language_specific_system_prompt function's dict
        # This is a bit manual, ideally prompts dict would be global
        known_prompts = ['Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C', 'C#'] # Add others if defined in get_language_specific_system_prompt
        for lang in sorted(known_prompts): print(f"  • {lang}")
        print("\nScoring Config Keys (for Metrics):")
        for key in sorted(SCORING_CONFIG.keys()):
            # Exclude fallback keys if they represent derived metrics handled internally
            # No such keys currently, but keep pattern if needed later
            print(f"  • {key}")
        print("-" * 40)
        print("Notes:")
        print(" - Other languages/file types may be detected but will use the default LLM prompt.")
        print(" - Scoring relies on metrics from tools (Lizard, cloc, Radon); applicability varies by language.")
        print(" - Language detection maps various extensions/names (e.g., .ts, React -> javascript key).")
        sys.exit(0)

    # --- Verbosity Handling ---
    # Currently, output is always printed. The --verbose flag is kept for potential future use
    # (e.g., suppressing non-error messages).
    if args.verbose:
        print("Verbose mode enabled (currently default).")
        pass # Explicitly do nothing extra for now

    # --- Check CodeCarbon Availability if Emission Measurement Requested ---
    if args.measure_emissions and not CODECARBON_AVAILABLE:
        print("\n" + "="*20 + " CONFIGURATION WARNING " + "="*20, file=sys.stderr)
        print("WARNING: --measure-emissions flag was used, but the 'codecarbon' Python library could not be imported.", file=sys.stderr)
        print("Emission measurement steps will be skipped.", file=sys.stderr)
        print("To enable measurements, install it: pip install codecarbon", file=sys.stderr)
        print("See: https://github.com/mlco2/codecarbon", file=sys.stderr)
        print("="*61, file=sys.stderr)
        # Continue execution without measurement capability

    # --- Run Main Analysis ---
    overall_success = False
    try:
        # Call the main function, passing all relevant arguments
        overall_success = analyze_and_update_code_for_sustainability(
            file_path=args.file_path,
            api_key_file=args.api_key_file,
            changes_only=args.changes_only,
            forced_language=args.language,
            measure_emissions=args.measure_emissions,
            execution_timeout=args.execution_timeout,
            skip_llm_flag=args.skip_llm,
            full_file_mode=args.full_file_mode
        )
    except Exception as main_e:
         # Catch any unexpected errors during the main workflow
         import traceback
         print(f"\nFATAL ERROR during analysis of {args.file_path}: {main_e}", file=sys.stderr)
         print("Traceback:", file=sys.stderr)
         traceback.print_exc(file=sys.stderr)
         overall_success = False # Ensure failure state
    finally:
        # Any final cleanup if needed (though temp files handled in function)
        pass

    # --- Final Status and Exit Code ---
    if overall_success:
        # Use print directly to ensure it goes to original stdout/stderr if redirection was attempted
        print(f"\n✅ Successfully processed: {args.file_path}")
        sys.exit(0)
    else:
        print(f"\n❌ Processing failed or changes could not be applied for: {args.file_path}", file=sys.stderr)
        sys.exit(1)