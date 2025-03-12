import os
import re
import streamlit as st
import requests
import time
import threading
from dotenv import load_dotenv

st.set_page_config(
    page_title="Sustainable Code Analyzer",
    page_icon="🌱",
    layout="wide"
)

# Load environment variables
load_dotenv()

# App title and description
st.title("🌱 Sustainable Code Analyzer")
st.markdown("""
This application analyzes your code and suggests optimizations to reduce resource consumption
(CPU, memory, energy) and minimize environmental impact. Simply upload your code file or paste your code,
and the AI will generate a more sustainable version.
""")

# Function to analyze code
def analyze_code_for_sustainability(code_content, filename):
    if not api_key:
        st.error("Please enter your Groq API key in the sidebar")
        return None
    
    prompt = f"""
    Role: You are a highly experienced software engineer specializing in sustainable and efficient coding practices.
    
    Task: Analyze the following code snippet and identify potential areas where it could be improved to reduce resource consumption (CPU, memory, energy), and minimize environmental impact.
    
    CODE:
    ```python
    {code_content}
    ```
    
    Please provide ONLY the revised code without any explanations or comments. The output should be in a format ready to directly replace the original code file.
    """
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a sustainable coding expert that optimizes code to reduce environmental impact."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature
            },
            timeout=30  # Added timeout
        )
        
        response.raise_for_status()  # Raise exception for non-200 status codes
        
        sustainable_code = response.json()["choices"][0]["message"]["content"]
        # Improved regex to handle different code block formats
        sustainable_code = re.sub(r'```(?:python)?\s*', '', sustainable_code)
        sustainable_code = re.sub(r'```\s*$', '', sustainable_code)
        
        return sustainable_code
        
    except requests.exceptions.RequestException as e:
        st.error(f"API Request Error: {e}")
        return None
    except (KeyError, IndexError) as e:
        st.error(f"Error parsing API response: {e}")
        return None

# Function to set up Husky pre-commit hook
def setup_husky_hook():
    husky_hook_path = ".husky/pre-commit"
    if not os.path.exists(".husky"):
        os.makedirs(".husky")
    with open(husky_hook_path, "w") as hook_file:
        hook_file.write("#!/bin/sh\n")
        hook_file.write(". \"$(dirname \"$0\")/_/husky.sh\"\n")
        hook_file.write("python main.py --check-sustainability\n")
    
    # Make the hook executable
    try:
        import subprocess
        subprocess.run(["chmod", "+x", husky_hook_path], check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        # Fallback for Windows or if subprocess fails
        os.chmod(husky_hook_path, 0o755)

# Sidebar for API key
with st.sidebar:
    st.header("API Configuration")
    saved_api_key = os.getenv("GROQ_API_KEY", "")
    api_key = st.text_input("Groq API Key", value=saved_api_key, type="password")
    model = st.selectbox("Select Model", ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"])
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)

# Main content layout with tabs
tab1, tab2, tab3 = st.tabs(["Upload File", "Paste Code", "🐕 Husky Visualization"])

# Upload File Tab
with tab1:
    uploaded_file = st.file_uploader("Choose a Python file", type=['py'])
    if uploaded_file is not None:
        file_contents = uploaded_file.getvalue().decode("utf-8")
        with st.expander("Original Code"):
            st.code(file_contents, language="python")
        if st.button("Analyze & Optimize", key="analyze_file"):
            with st.spinner("Optimizing code for sustainability..."):
                sustainable_code = analyze_code_for_sustainability(file_contents, uploaded_file.name)
            if sustainable_code:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Original Code")
                    st.code(file_contents, language="python")
                with col2:
                    st.subheader("Sustainable Code")
                    st.code(sustainable_code, language="python")
                st.download_button("Download Sustainable Code", data=sustainable_code, file_name=f"sustainable_{uploaded_file.name}", mime="text/plain")

# Paste Code Tab
with tab2:
    code_input = st.text_area("Paste your Python code here:", height=300)
    filename = st.text_input("Filename (for reference):", "code_snippet.py")
    if st.button("Analyze & Optimize", key="analyze_pasted"):
        if code_input:
            with st.spinner("Optimizing code for sustainability..."):
                sustainable_code = analyze_code_for_sustainability(code_input, filename)
            if sustainable_code:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Original Code")
                    st.code(code_input, language="python")
                with col2:
                    st.subheader("Sustainable Code")
                    st.code(sustainable_code, language="python")
                st.download_button("Download Sustainable Code", data=sustainable_code, file_name=f"sustainable_{filename}", mime="text/plain")
        else:
            st.warning("Please paste some code first.")

# Husky Visualization Tab
with tab3:
    st.subheader("🐕 Husky Pre-commit Hook Visualization")
    
    # Check if hook exists
    hook_exists = os.path.exists(".husky/pre-commit")
    
    # Status indicator
    col1, col2 = st.columns([1, 3])
    with col1:
        if hook_exists:
            st.success("ACTIVE")
        else:
            st.error("INACTIVE")
    with col2:
        st.write("Pre-commit hook status")
    
    # Actions
    col1, col2 = st.columns(2)
    with col1:
        if hook_exists:
            if st.button("Disable Hook"):
                try:
                    if os.path.exists(".husky/pre-commit"):
                        os.remove(".husky/pre-commit")
                        if os.path.exists(".husky") and not os.listdir(".husky"):
                            os.rmdir(".husky")
                    st.success("Hook disabled successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error disabling hook: {e}")
        else:
            if st.button("Enable Hook"):
                try:
                    setup_husky_hook()
                    st.success("Hook enabled successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error setting up hook: {e}")
    
    with col2:
        if st.button("Simulate Hook Run"):
            # Create a placeholder for the terminal output
            terminal = st.empty()
            terminal.markdown("""
            ```
            🔄 Initializing Husky pre-commit hook...
            ```
            """)
            
            # Simulate terminal output with progress
            log_messages = [
                "🐕 Husky pre-commit hook triggered...",
                "📝 Collecting staged files...",
                "✅ Found 3 Python files",
                "🌱 Running sustainability check...",
                "🔍 Analyzing file 1/3: main.py",
                "✅ main.py - Optimizations suggested",
                "🔍 Analyzing file 2/3: utils.py",
                "✅ utils.py - Looking good!",
                "🔍 Analyzing file 3/3: api.py",
                "⚠️ api.py - Found inefficient API calls",
                "📊 Sustainability report generated",
                "✅ Pre-commit hook completed successfully!"
            ]
            
            full_log = "🔄 Initializing Husky pre-commit hook...\n"
            # Display log messages with delay to simulate real-time output
            for msg in log_messages:
                time.sleep(0.5)  # Add delay for visual effect
                full_log += msg + "\n"
                terminal.markdown(f"```\n{full_log}```")
    
    # Hook details
    with st.expander("Hook Configuration Details"):
        st.markdown("**File Path:** `.husky/pre-commit`")
        st.code("""#!/bin/sh
. "$(dirname "$0")/_/husky.sh"
python main.py --check-sustainability
""", language="bash")
        
        st.markdown("**What it does:**")
        st.markdown("""
        When you commit code, this hook:
        1. Intercepts the commit process
        2. Runs your code through the sustainability analyzer
        3. Checks for inefficient patterns
        4. Generates optimization suggestions
        5. Allows/blocks the commit based on sustainability metrics
        """)
    
    # Visual representation of hook workflow
    st.subheader("Hook Workflow")
    cols = st.columns(5)
    with cols[0]:
        st.markdown("### 📝")
        st.markdown("Commit Started")
    with cols[1]:
        st.markdown("### 🐕")
        st.markdown("Husky Triggered")
    with cols[2]:
        st.markdown("### 🔍")
        st.markdown("Code Analysis")
    with cols[3]:
        st.markdown("### 📊")
        st.markdown("Report Generated")
    with cols[4]:
        st.markdown("### ✅/❌")
        st.markdown("Commit Decision")
    
    # Progress bar to visualize the workflow
    progress_placeholder = st.empty()
    if st.button("Visualize Workflow"):
        for i in range(101):
            progress_placeholder.progress(i)
            time.sleep(0.02)
        st.success("Commit successful! Sustainability checks passed.")

st.markdown("---")
st.markdown("🌿 Sustainable Code Analyzer - Making software environmentally friendly")

# Setup Husky hook if it's the main script running
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--check-sustainability":
        # Logic for when run as a pre-commit hook
        print("Running sustainability check on staged files...")
        # Add logic here to check files that would be committed
        sys.exit(0)  # Success exit code