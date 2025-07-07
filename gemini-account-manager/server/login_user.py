import requests

url = "http://127.0.0.1:8000/token"
data = {
    "username": "bhpark",
    "password": "temp1"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=data, headers=headers)

print(response.status_code)
print(response.json())
