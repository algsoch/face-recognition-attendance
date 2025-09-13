from backend.database import engine
from sqlalchemy import text

print('Checking database permissions...')
try:
    with engine.connect() as conn:
        # Check current user
        result = conn.execute(text('SELECT current_user'))
        user = result.fetchone()[0]
        print(f'Current user: {user}')
        
        # Check database name
        result = conn.execute(text('SELECT current_database()'))
        db_name = result.fetchone()[0]
        print(f'Current database: {db_name}')
        
        # Check schema permissions
        query = """
        SELECT schema_name, 
               has_schema_privilege(current_user, schema_name, 'USAGE') as usage,
               has_schema_privilege(current_user, schema_name, 'CREATE') as create_perm
        FROM information_schema.schemata 
        WHERE schema_name IN ('public', 'teacher_data')
        """
        result = conn.execute(text(query))
        schemas = result.fetchall()
        print('\nSchema permissions:')
        for schema, usage, create in schemas:
            print(f'  {schema}: USAGE={usage}, CREATE={create}')
            
        # Try to create a simple table
        print('\nTesting table creation...')
        try:
            conn.execute(text('CREATE TABLE test_table (id integer)'))
            print('✅ Table creation successful!')
            conn.execute(text('DROP TABLE test_table'))
            conn.commit()
        except Exception as e:
            print(f'❌ Table creation failed: {e}')
        
except Exception as e:
    print(f'❌ Permission check failed: {e}')