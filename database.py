import sqlite3

def initialize_database():
    conn = sqlite3.connect('jobscreening.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_descriptions (
        id INTEGER PRIMARY KEY,
        job_title TEXT,
        company_name TEXT,
        job_summary TEXT,
        responsibilities TEXT,
        qualifications TEXT,
        technologies TEXT,
        offer TEXT
    )
    ''')

    conn.commit()
    conn.close()

initialize_database()
