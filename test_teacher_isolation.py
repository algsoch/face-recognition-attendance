import requests
import json

print('🧪 Testing Teacher Isolation...')
print('=' * 50)

# Test login for Teacher 1 (npdimagine@gmail.com)
print('\n1. Testing Teacher 1 (npdimagine@gmail.com)...')
login_data1 = {
    'email': 'npdimagine@gmail.com',
    'password': 'demo123'
}

try:
    response = requests.post('http://localhost:8000/auth/login', json=login_data1)
    if response.status_code == 200:
        token1 = response.json()['access_token']
        print('✅ Teacher 1 login successful')
        
        # Get students for Teacher 1
        headers1 = {'Authorization': f'Bearer {token1}'}
        students_response1 = requests.get('http://localhost:8000/students', headers=headers1)
        if students_response1.status_code == 200:
            students1 = students_response1.json()
            print(f'📚 Teacher 1 sees {len(students1)} students:')
            for student in students1:
                print(f'   - {student["name"]} (Roll: {student["roll_number"]})')
        else:
            print(f'❌ Failed to get students: {students_response1.text}')
    else:
        print(f'❌ Teacher 1 login failed: {response.text}')
except Exception as e:
    print(f'❌ Error testing Teacher 1: {e}')

# Test login for Teacher 2 (vk927291@gmail.com)
print('\n2. Testing Teacher 2 (vk927291@gmail.com)...')
login_data2 = {
    'email': 'vk927291@gmail.com',
    'password': 'demo123'
}

try:
    response = requests.post('http://localhost:8000/auth/login', json=login_data2)
    if response.status_code == 200:
        token2 = response.json()['access_token']
        print('✅ Teacher 2 login successful')
        
        # Get students for Teacher 2
        headers2 = {'Authorization': f'Bearer {token2}'}
        students_response2 = requests.get('http://localhost:8000/students', headers=headers2)
        if students_response2.status_code == 200:
            students2 = students_response2.json()
            print(f'📚 Teacher 2 sees {len(students2)} students:')
            for student in students2:
                print(f'   - {student["name"]} (Roll: {student["roll_number"]})')
        else:
            print(f'❌ Failed to get students: {students_response2.text}')
    else:
        print(f'❌ Teacher 2 login failed: {response.text}')
except Exception as e:
    print(f'❌ Error testing Teacher 2: {e}')

print('\n🎯 Teacher isolation test completed!')
