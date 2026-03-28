import requests
import json

URL = "http://localhost:8000/register/teacher"
data = {
    "email": f"debug_{json.dumps(dict())}@test.com", # random-ish
    "password": "pass123",
    "full_name": "Debug User",
    "role": "Teacher"
}

try:
    print(f"Testing {URL}...")
    r = requests.post(URL, json=data)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
