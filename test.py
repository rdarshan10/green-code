import requests

# Replace with your API key
api_key = "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"

# Try a simple request
try:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",  # Correct URL for Groq
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "user", "content": "Hello, this is a test message to verify my API key works."}
            ],
            "temperature": 0.2
        }
    )

    if response.status_code == 200:
        print("API key is working! Response:")
        print(response.json()["choices"][0]["message"]["content"])
    else:
        print(f"API key verification failed with error:\n{response.text}")

except Exception as e:
    print("API key verification failed with error:")
    print(str(e))
