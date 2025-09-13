import psycopg2
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')

print('🔧 Creating demo teacher accounts...')
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# Create demo teachers
demo_teachers = [
    {
        'teacher_id': 'teacher_001',
        'name': 'vicky',
        'email': 'npdimagine@gmail.com',
        'password': 'demo123',
        'department': 'Mechanical Engineering',
        'phone': '+91-9876543210'
    },
    {
        'teacher_id': 'teacher_002', 
        'name': 'Vicky Kumar',
        'email': 'vk927291@gmail.com',
        'password': 'demo123',
        'department': 'Computer Science',
        'phone': '+91-9876543211'
    }
]

for teacher in demo_teachers:
    # Hash password
    password_hash = bcrypt.hashpw(teacher['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Insert teacher
    cursor.execute('''
        INSERT INTO teachers (teacher_id, name, email, password_hash, department, phone, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (email) DO UPDATE SET
        password_hash = EXCLUDED.password_hash,
        updated_at = NOW()
    ''', (teacher['teacher_id'], teacher['name'], teacher['email'], password_hash, teacher['department'], teacher['phone']))
    
    print(f'✅ Created/Updated teacher: {teacher["name"]} ({teacher["email"]})')

conn.commit()
conn.close()
print('🎯 Demo teachers created successfully!')
