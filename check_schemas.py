from backend.database import engine
from sqlalchemy import text

print('Checking all available schemas...')
try:
    with engine.connect() as conn:
        # Check all schemas and permissions
        query = """
        SELECT schema_name, 
               has_schema_privilege(current_user, schema_name, 'USAGE') as usage,
               has_schema_privilege(current_user, schema_name, 'CREATE') as create_perm
        FROM information_schema.schemata 
        ORDER BY schema_name
        """
        result = conn.execute(text(query))
        schemas = result.fetchall()
        print('All schemas and permissions:')
        for schema, usage, create in schemas:
            print(f'  {schema}: USAGE={usage}, CREATE={create}')
            
        print('\nChecking if tables can be created in any schema...')
        writable_schemas = [schema for schema, usage, create in schemas if create]
        if writable_schemas:
            print(f'✅ Can create tables in: {writable_schemas}')
            
            # Test creating in the first writable schema
            test_schema = writable_schemas[0]
            try:
                conn.execute(text(f'CREATE TABLE {test_schema}.test_table (id integer)'))
                print(f'✅ Successfully created table in {test_schema}!')
                conn.execute(text(f'DROP TABLE {test_schema}.test_table'))
                conn.commit()
            except Exception as e:
                print(f'❌ Failed to create table in {test_schema}: {e}')
        else:
            print('❌ No schemas with CREATE permission found')
        
except Exception as e:
    print(f'❌ Schema check failed: {e}')