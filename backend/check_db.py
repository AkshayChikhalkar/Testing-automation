import psycopg2

try:
    conn = psycopg2.connect('postgresql://matlab_user:matlab_password@193.16.126.186:5432/matlab_automation')
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cursor.fetchall()
    print('Existing tables:', [table[0] for table in tables])
    conn.close()
    print('Database connection successful!')
except Exception as e:
    print(f'Error: {e}')
