cd F:\attendance; python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')

print('🔍 Checking teacher account status after update...')
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

cursor.execute('SELECT teacher_id, name, email, is_active FROM teachers')
teachers = cursor.fetchall()

print('=== TEACHER ACCOUNTS STATUS ===')
for teacher in teachers:
    teacher_id, name, email, is_active = teacher
    status = '✅ ACTIVE' if is_active else '❌ INACTIVE'
    print(f'ID: {teacher_id}, Name: {name}, Email: {email}, Status: {status}')

conn.close()
"