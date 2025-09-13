from backend.database import engine
from backend.models import Base
from sqlalchemy import text

print('Testing database connection...')
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        print('✅ Database connected successfully!')
        
        # Check if tables exist
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        result = conn.execute(text(query))
        tables = result.fetchall()
        print('\nExisting tables:')
        for table in tables:
            print(f'  - {table[0]}')
            
        if not tables:
            print('\n⚠️  No tables found. Need to create them.')
        else:
            print(f'\n✅ Found {len(tables)} existing tables.')
        
except Exception as e:
    print(f'❌ Database connection failed: {e}')