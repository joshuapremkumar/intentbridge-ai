import requests
import json

url = "https://intentbridge-ai-4fmgkvbfua-el.a.run.app/analyze"
payload = {"input": "My brother hurt his leg and is bleeding"}
headers = {"Content-Type": "application/json"}

print(f"Testing URL: {url}")
try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
