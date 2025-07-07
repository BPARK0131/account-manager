import requests
import json

url = "http://127.0.0.1:8000/register"
data = {
    "username": "bhpark",
    "password": "temp1",
    "role": "user"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(data), headers=headers)

print(response.status_code)
print(response.json())
