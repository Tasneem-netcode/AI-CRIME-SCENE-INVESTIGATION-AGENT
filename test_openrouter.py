import os
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "google/gemini-2.0-flash-exp:free"

def test_connection():
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501", 
        "X-Title": "CSI Test Debug"
    }
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": "Hello, are you operational?"}]
    }
    
    print(f"Testing Model: {OPENROUTER_MODEL}")
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
