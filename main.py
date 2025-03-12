import os
import re
from dotenv import load_dotenv
import requests

def analyze_and_update_code_for_sustainability(file_path):
    """
    Read code from a file, analyze it with Groq for sustainability, 
    and replace the file content with the improved sustainable code.
    """
    # Load environment variables (for API key)
    load_dotenv()
    
    # Get API key from environment variable or allow direct input
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        api_key = input("Enter your Groq API key: ")
        if not api_key:
            raise ValueError("No API key provided")
    
    # Read the input file
    try:
        with open(file_path, 'r') as file:
            code_content = file.read()
        print(f"Successfully read file: {file_path}")
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Define the prompt for sustainability analysis
    prompt = f"""
    Role: You are a highly experienced software engineer specializing in sustainable and efficient coding practices.
    
    Task: Analyze the following code snippet and identify potential areas where it could be improved to reduce resource consumption (CPU, memory, energy), and minimize environmental impact.
    
    CODE:
    ```python
    {code_content}
    ```
    
    Please provide ONLY the revised code without any explanations or comments. The output should directly replace the original code file.
    """
    
    # Send request to Groq API
    try:
        print("Sending code to Groq for sustainability analysis...")
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
            print("Error from Groq API:", response.text)
            return
        
        # Extract the response
        sustainable_code = response.json()["choices"][0]["message"]["content"]
        
        # Remove Markdown code block markers
        sustainable_code = re.sub(r'^```.*$', '', sustainable_code, flags=re.MULTILINE)
        
        # Write the improved code back to the original file
        with open(file_path, 'w') as output_file:
            output_file.write(sustainable_code)
        print(f"File successfully updated with sustainable code: {file_path}")
        
    except Exception as e:
        print(f"Error using Groq API: {e}")
        return

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze code for sustainability using Groq API and update the file")
    parser.add_argument("file_path", help="Path to the file containing code to analyze and update")
    
    args = parser.parse_args()
    analyze_and_update_code_for_sustainability(args.file_path)
