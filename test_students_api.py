#!/usr/bin/env python3
"""
Quick test script to check what the students API returns
"""
import requests
import json

# First login to get token
login_data = {
    "username": "npdimagine@gmail.com",
    "password": "Iit7065@"
}

print("🔧 Testing Students API...")
print("1. Logging in...")

try:
    # Login
    login_response = requests.post("http://localhost:8003/auth/login", data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        token = token_data.get("access_token")
        print(f"Token received: {'✅ Yes' if token else '❌ No'}")
        
        if token:
            # Test students API
            headers = {"Authorization": f"Bearer {token}"}
            students_response = requests.get("http://localhost:8003/students", headers=headers)
            print(f"\n2. Students API status: {students_response.status_code}")
            
            if students_response.status_code == 200:
                students_data = students_response.json()
                print(f"✅ Students API Response:")
                print(f"   Type: {type(students_data)}")
                print(f"   Length: {len(students_data) if isinstance(students_data, list) else 'Not a list'}")
                print(f"   Raw data: {json.dumps(students_data, indent=2)}")
                
                if isinstance(students_data, list) and len(students_data) > 0:
                    print(f"\n📋 First student sample:")
                    print(json.dumps(students_data[0], indent=2))
            else:
                print(f"❌ Students API failed: {students_response.text}")
        else:
            print("❌ No token received")
    else:
        print(f"❌ Login failed: {login_response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
