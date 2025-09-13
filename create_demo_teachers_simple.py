import psycopg2
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')

print('🔧 Creating demo teacher accounts for current system...')
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# Create demo teachers with integer IDs
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
    
    # Insert teacher (let database auto-assign ID) and ensure they're active
    cursor.execute('''
        INSERT INTO teachers (name, email, password_hash, department, phone, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, true, NOW(), NOW())
        ON CONFLICT (email) DO UPDATE SET
        password_hash = EXCLUDED.password_hash,
        is_active = true,
        updated_at = NOW()
    ''', (teacher['name'], teacher['email'], password_hash, teacher['department'], teacher['phone']))
    
    print(f'✅ Created/Updated teacher: {teacher["name"]} ({teacher["email"]})')

conn.commit()
conn.close()
print('🎯 Demo teachers created successfully!')
