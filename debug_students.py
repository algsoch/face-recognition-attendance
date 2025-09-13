#!/usr/bin/env python3
"""
Comprehensive Students API Debug Script
This script will test the students API endpoint and analyze the data structure.
"""

import requests
import json
import sys
from datetime import datetime

def debug_students_api():
    """Debug the students API comprehensively"""
    base_url = "http://localhost:8003"
    
    print("🔍 COMPREHENSIVE STUDENTS API DEBUG")
    print("=" * 50)
    print(f"Time: {datetime.now()}")
    print(f"Testing API at: {base_url}")
    print()
    
    # Step 1: Test login
    print("1️⃣ TESTING LOGIN...")
    login_data = {
        "email": "npdimagine@gmail.com",
        "password": "Iit7065@"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('access_token')
            print(f"   ✅ Login successful!")
            print(f"   Token: {token[:50]}..." if token else "   ❌ No token received")
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return
    
    # Step 2: Test students API
    print("\n2️⃣ TESTING STUDENTS API...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        students_response = requests.get(
            f"{base_url}/students",
            headers=headers
        )
        print(f"   Students API Status: {students_response.status_code}")
        
        if students_response.status_code == 200:
            students_data = students_response.json()
            print(f"   ✅ Students API successful!")
            print(f"   Response type: {type(students_data)}")
            
            # Analyze the data structure
            if isinstance(students_data, list):
                print(f"   📊 Data is a list with {len(students_data)} items")
                if len(students_data) > 0:
                    first_student = students_data[0]
                    print(f"   📋 First student structure:")
                    print(f"        Type: {type(first_student)}")
                    if isinstance(first_student, dict):
                        for key, value in first_student.items():
                            print(f"        {key}: {type(value).__name__} = {value}")
            elif isinstance(students_data, dict):
                print(f"   📊 Data is a dict with keys: {list(students_data.keys())}")
                for key, value in students_data.items():
                    print(f"        {key}: {type(value).__name__} = {value}")
            else:
                print(f"   ⚠️  Unexpected data type: {type(students_data)}")
            
            # Print full data (truncated)
            print(f"\n   📄 FULL RESPONSE:")
            print(json.dumps(students_data, indent=2, default=str)[:2000] + "..." if len(str(students_data)) > 2000 else json.dumps(students_data, indent=2, default=str))
            
        else:
            print(f"   ❌ Students API failed: {students_response.text}")
            
    except Exception as e:
        print(f"   ❌ Students API error: {e}")
    
    # Step 3: Test attendance statistics for comparison
    print("\n3️⃣ TESTING ATTENDANCE STATISTICS...")
    try:
        stats_response = requests.get(
            f"{base_url}/attendance/statistics",
            headers=headers
        )
        print(f"   Statistics Status: {stats_response.status_code}")
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"   ✅ Statistics successful!")
            print(f"   Total students from stats: {stats_data.get('total_students', 'Unknown')}")
            print(f"   Present today: {stats_data.get('present_today', 'Unknown')}")
            print(f"   Absent today: {stats_data.get('absent_today', 'Unknown')}")
        else:
            print(f"   ❌ Statistics failed: {stats_response.text}")
            
    except Exception as e:
        print(f"   ❌ Statistics error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 DEBUG COMPLETE")

if __name__ == "__main__":
    debug_students_api()
