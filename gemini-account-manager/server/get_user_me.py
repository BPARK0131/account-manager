import requests

url = "http://127.0.0.1:8000/users/me"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiaHBhcmsiLCJyb2xlIjoidXNlciIsImV4cCI6MTc1MTg5MzkzOH0.ykFJ7i5aRVr_SmQoKABaW1-4bX_74e3JnKkX6dyctFg"
headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.json())
