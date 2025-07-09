import requests
import json

API_URL = "http://localhost:8000"
TEST_USER = {
    "username": "testuser.gemini@example.com",
    "password": "a.very.secure.password123",
    "role": "user"
}

def run_test():
    # 1. Register User
    try:
        print("--- 1. Testing Registration ---")
        reg_response = requests.post(f"{API_URL}/register", json=TEST_USER)
        
        if reg_response.status_code == 200:
            print("✅ Registration successful.")
            print("Response:", reg_response.json())
        elif reg_response.status_code == 400 and "already registered" in reg_response.text:
             print("✅ Registration endpoint works (user already exists).")
        else:
            print(f"❌ Registration FAILED. Status: {reg_response.status_code}")
            print("Response:", reg_response.text)
            return # Stop if registration fails
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION FAILED: Could not connect to the server at {API_URL}.")
        print("Please ensure the FastAPI server is running.")
        return

    # 2. Login User
    print("\n--- 2. Testing Login ---")
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        login_response = requests.post(f"{API_URL}/token", data=login_data, headers=headers)

        if login_response.status_code == 200:
            print("✅ Login successful.")
            print("Access Token:", login_response.json().get("access_token"))
        else:
            print(f"❌ Login FAILED. Status: {login_response.status_code}")
            print("Response:", login_response.text)

    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION FAILED during login test.")


if __name__ == "__main__":
    run_test()
