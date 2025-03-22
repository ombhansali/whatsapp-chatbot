import psycopg2

# Replace YOUR-PASSWORD with your actual password
conn_string = "postgresql://postgres:Ganpati%4098Appa@db.wewgmuoefdsdomohokwz.supabase.co:5432/postgres"

try:
    conn = psycopg2.connect(conn_string)
    print("Connected to the database successfully")
    cursor = conn.cursor()

    # Example query
    cursor.execute("SELECT * FROM users;")
    results = cursor.fetchall()
    for row in results:
        print(row)

    cursor.close()
    conn.close()
    print("Connection closed")
except Exception as e:
    print(f"Error: {e}")
