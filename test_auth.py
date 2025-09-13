import requests
import json

# Test the authentication system
print("🧪 Testing Authentication System")
print("=" * 50)

# Test Registration
print("\n1. Testing Registration...")
new_teacher = {
    "name": "Test Teacher",
    "email": "test@example.com",
    "password": "test123",
    "department": "Testing",
    "phone": "+91-1234567890"
}

try:
    response = requests.post('http://localhost:8003/auth/register', 
                           json=new_teacher)
    print(f"Registration Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Registration successful!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Registration failed: {response.text}")
except Exception as e:
    print(f"❌ Registration error: {e}")

# Test Login with demo account
print("\n2. Testing Login...")
login_data = {
    "email": "npdimagine@gmail.com",
    "password": "demo123"
}

try:
    response = requests.post('http://localhost:8003/auth/login', 
                           json=login_data)
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Login successful!")
        print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
        
        # Test accessing protected endpoint
        token = result.get('access_token')
        if token:
            print("\n3. Testing Protected Endpoint...")
            headers = {'Authorization': f'Bearer {token}'}
            students_response = requests.get('http://localhost:8003/students', 
                                           headers=headers)
            print(f"Students API Status: {students_response.status_code}")
            if students_response.status_code == 200:
                students = students_response.json()
                print(f"✅ Found {len(students)} students")
            else:
                print(f"❌ Students API failed: {students_response.text}")
    else:
        print(f"❌ Login failed: {response.text}")
except Exception as e:
    print(f"❌ Login error: {e}")

print("\n🎯 Authentication test completed!")
