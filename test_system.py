"""
Test script for Attendance Management System
"""
import asyncio
import asyncpg
import requests
import json
from datetime import date, datetime
import os
from decouple import config

# Test configuration
API_BASE_URL = "http://localhost:8000"
DATABASE_URL = config('DATABASE_URL')

class AttendanceSystemTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.token = None

    def test_database_connection(self):
        """Test database connectivity"""
        print("🔗 Testing database connection...")
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def test_connection():
                conn = await asyncpg.connect(DATABASE_URL)
                result = await conn.fetchrow('SELECT 1 as test')
                await conn.close()
                return result
            
            result = loop.run_until_complete(test_connection())
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def test_api_health(self):
        """Test API health endpoint"""
        print("🏥 Testing API health...")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API health check: {data['status']}")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API health check error: {e}")
            return False

    def test_teacher_registration(self):
        """Test teacher registration"""
        print("👨‍🏫 Testing teacher registration...")
        try:
            teacher_data = {
                "name": "Test Teacher",
                "email": f"test.teacher.{datetime.now().timestamp()}@school.edu",
                "password": "testpassword123",
                "department": "Computer Science"
            }
            
            response = requests.post(f"{self.base_url}/auth/register", json=teacher_data)
            if response.status_code == 200:
                print("✅ Teacher registration successful")
                return True, teacher_data
            else:
                print(f"❌ Teacher registration failed: {response.status_code}")
                print(response.text)
                return False, None
        except Exception as e:
            print(f"❌ Teacher registration error: {e}")
            return False, None

    def test_teacher_login(self, teacher_data):
        """Test teacher login"""
        print("🔐 Testing teacher login...")
        try:
            login_data = {
                "email": teacher_data["email"],
                "password": teacher_data["password"]
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✅ Teacher login successful")
                return True
            else:
                print(f"❌ Teacher login failed: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Teacher login error: {e}")
            return False

    def test_student_creation(self):
        """Test student creation"""
        print("👨‍🎓 Testing student creation...")
        try:
            student_data = {
                "roll_number": f"TEST{datetime.now().timestamp():.0f}",
                "name": "Test Student",
                "class_name": "12",
                "section": "A",
                "stream": "Computer Science",
                "email": f"test.student.{datetime.now().timestamp()}@student.edu"
            }
            
            response = self.session.post(f"{self.base_url}/students", json=student_data)
            if response.status_code == 200:
                data = response.json()
                print("✅ Student creation successful")
                return True, data
            else:
                print(f"❌ Student creation failed: {response.status_code}")
                print(response.text)
                return False, None
        except Exception as e:
            print(f"❌ Student creation error: {e}")
            return False, None

    def test_class_creation(self):
        """Test class creation"""
        print("📚 Testing class creation...")
        try:
            # First get current teacher info
            response = self.session.get(f"{self.base_url}/auth/me")
            if response.status_code != 200:
                print("❌ Could not get teacher info")
                return False, None
            
            teacher = response.json()
            
            class_data = {
                "class_name": "12",
                "section": "Test",
                "subject": "Computer Science Test",
                "teacher_id": teacher["teacher_id"]
            }
            
            response = self.session.post(f"{self.base_url}/classes", json=class_data)
            if response.status_code == 200:
                data = response.json()
                print("✅ Class creation successful")
                return True, data
            else:
                print(f"❌ Class creation failed: {response.status_code}")
                print(response.text)
                return False, None
        except Exception as e:
            print(f"❌ Class creation error: {e}")
            return False, None

    def test_attendance_marking(self, student_data, class_data):
        """Test attendance marking"""
        print("✔️ Testing attendance marking...")
        try:
            attendance_data = {
                "student_id": student_data["student_id"],
                "class_id": class_data["class_id"],
                "status": "Present",
                "attendance_date": date.today().isoformat(),
                "notes": "Test attendance"
            }
            
            response = self.session.post(f"{self.base_url}/attendance", json=attendance_data)
            if response.status_code == 200:
                data = response.json()
                print("✅ Attendance marking successful")
                return True, data
            else:
                print(f"❌ Attendance marking failed: {response.status_code}")
                print(response.text)
                return False, None
        except Exception as e:
            print(f"❌ Attendance marking error: {e}")
            return False, None

    def test_analytics(self):
        """Test analytics endpoints"""
        print("📊 Testing analytics...")
        try:
            endpoints = [
                "/analytics/attendance-stats",
                "/analytics/trends",
                "/analytics/top-performers",
                "/analytics/attention-needed"
            ]
            
            success_count = 0
            for endpoint in endpoints:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    success_count += 1
                    print(f"✅ {endpoint} - OK")
                else:
                    print(f"❌ {endpoint} - Failed ({response.status_code})")
            
            if success_count == len(endpoints):
                print("✅ All analytics endpoints working")
                return True
            else:
                print(f"⚠️ {success_count}/{len(endpoints)} analytics endpoints working")
                return False
        except Exception as e:
            print(f"❌ Analytics testing error: {e}")
            return False

    def test_file_upload_endpoint(self):
        """Test file upload endpoint (without actual file)"""
        print("📁 Testing file upload endpoint...")
        try:
            # Test endpoint availability (will fail due to no file, but endpoint should exist)
            response = self.session.post(f"{self.base_url}/students/upload")
            
            # We expect this to fail with 422 (validation error) since no file provided
            if response.status_code == 422:
                print("✅ File upload endpoint accessible")
                return True
            else:
                print(f"❌ File upload endpoint issue: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ File upload endpoint error: {e}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Attendance Management System Tests")
        print("=" * 50)
        
        results = {}
        
        # Database test
        results['database'] = self.test_database_connection()
        
        # API health test
        results['api_health'] = self.test_api_health()
        
        # Teacher registration and login
        teacher_success, teacher_data = self.test_teacher_registration()
        results['teacher_registration'] = teacher_success
        
        if teacher_success:
            results['teacher_login'] = self.test_teacher_login(teacher_data)
            
            if results['teacher_login']:
                # Student and class operations
                student_success, student_data = self.test_student_creation()
                results['student_creation'] = student_success
                
                class_success, class_data = self.test_class_creation()
                results['class_creation'] = class_success
                
                # Attendance marking
                if student_success and class_success:
                    attendance_success, _ = self.test_attendance_marking(student_data, class_data)
                    results['attendance_marking'] = attendance_success
                else:
                    results['attendance_marking'] = False
                
                # Analytics
                results['analytics'] = self.test_analytics()
                
                # File upload
                results['file_upload'] = self.test_file_upload_endpoint()
            else:
                results.update({
                    'student_creation': False,
                    'class_creation': False,
                    'attendance_marking': False,
                    'analytics': False,
                    'file_upload': False
                })
        else:
            results.update({
                'teacher_login': False,
                'student_creation': False,
                'class_creation': False,
                'attendance_marking': False,
                'analytics': False,
                'file_upload': False
            })
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            if success:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is ready for use.")
        elif passed > total // 2:
            print("⚠️ Most tests passed. Check failed tests.")
        else:
            print("❌ Many tests failed. System needs attention.")
        
        return results

def main():
    """Main test function"""
    print("Attendance Management System - Test Suite")
    print("Make sure the server is running on http://localhost:8000")
    input("Press Enter to continue...")
    
    tester = AttendanceSystemTester()
    results = tester.run_all_tests()
    
    return results

if __name__ == "__main__":
    main()
