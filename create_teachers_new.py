import psycopg2
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')

print('👥 Creating teachers with new structure...')
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# Create demo teachers
demo_teachers = [
    {
        'name': 'vicky',
        'email': 'npdimagine@gmail.com',
        'password': 'demo123',
        'department': 'Mechanical Engineering',
        'phone': '+91-9876543210'
    },
    {
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
        INSERT INTO teachers (name, email, password_hash, department, phone, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING teacher_id
    ''', (teacher['name'], teacher['email'], password_hash, teacher['department'], teacher['phone'], True))
    
    teacher_id = cursor.fetchone()[0]
    print(f'✅ Created teacher: {teacher["name"]} (ID: {teacher_id}, Email: {teacher["email"]})')

conn.commit()
conn.close()
print('🎯 Demo teachers created with new structure!')
