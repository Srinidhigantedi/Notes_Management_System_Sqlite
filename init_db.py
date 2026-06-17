import sqlite3

def init_database():
    conn = sqlite3.connect('notes.db')
    cur = conn.cursor()

    # Read schema.sql file
    with open('schema.sql', 'r') as f:
        sql_script = f.read()

    # Execute all SQL commands
    cur.executescript(sql_script)

    conn.commit()
    cur.close()
    conn.close()

    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()