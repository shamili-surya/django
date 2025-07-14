import requests
import json

url = "http://localhost:11434/api/generate"
data = {
    "model": "gemma",
    "prompt": "Hello"
}

response = requests.post(url, json=data, stream=True)

full_response = ""
for line in response.iter_lines():
    if line:
        try:
            json_line = json.loads(line.decode('utf-8'))
            print(json_line)
            full_response += json_line.get("response", "")
        except json.JSONDecodeError as e:
            print("⚠️ JSON decode error:", e)

print("\nFull response from Gemma:")
print(full_response)
