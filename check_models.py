import google.generativeai as genai
import os

# Default from app.py
api_key = "AIzaSyB6suR8iFycHZ7VNI5Ybn0apiqf-MrUnb0" 
genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
