from backend.database import engine
from sqlalchemy import text

print('Comprehensive database check...')
try:
    with engine.connect() as conn:
        # Check all tables in all schemas
        query = """
        SELECT schemaname, tablename, tableowner
        FROM pg_tables 
        ORDER BY schemaname, tablename
        """
        result = conn.execute(text(query))
        tables = result.fetchall()
        
        if tables:
            print('All tables in database:')
            for schema, table, owner in tables:
                print(f'  {schema}.{table} (owner: {owner})')
        else:
            print('❌ No tables found in any schema')
            
        # Check what the attendance user can actually do
        print('\nChecking user privileges...')
        query = """
        SELECT rolname, rolcreatedb, rolcreaterole, rolcanlogin, rolsuper
        FROM pg_roles 
        WHERE rolname = current_user
        """
        result = conn.execute(text(query))
        role_info = result.fetchone()
        if role_info:
            rolname, createdb, createrole, canlogin, super_user = role_info
            print(f'User: {rolname}')
            print(f'  Can create databases: {createdb}')
            print(f'  Can create roles: {createrole}')
            print(f'  Can login: {canlogin}')
            print(f'  Is superuser: {super_user}')
        
except Exception as e:
    print(f'❌ Database check failed: {e}')