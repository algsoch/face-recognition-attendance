cd F:\attendance; python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')

print('🗑️ CLEARING ENTIRE DATABASE...')
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# Drop all existing tables
cursor.execute('DROP TABLE IF EXISTS attendance CASCADE')
cursor.execute('DROP TABLE IF EXISTS student_classes CASCADE') 
cursor.execute('DROP TABLE IF EXISTS students CASCADE')
cursor.execute('DROP TABLE IF EXISTS classes CASCADE')
cursor.execute('DROP TABLE IF EXISTS teachers CASCADE')

print('✅ All tables dropped successfully!')
conn.commit()
conn.close()
"