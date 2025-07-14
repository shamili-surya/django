import requests

url = "http://localhost:11434/api/generate"
data = {
    "model": "gemma",
    "prompt": "Hello"
}

response = requests.post(url, json=data, stream=True)

full_response = ""
for line in response.iter_lines():
    if line:
        json_line = line.decode('utf-8')
        print(json_line)  # Show each line
        try:
            part = eval(json_line)
            full_response += part.get("response", "")
        except:
            pass

print("\nFull response from Gemma:")
print(full_response)
