import sqlite3

# connect to database (creates it if it doesn't exist)
conn = sqlite3.connect("assets/chinese.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM users WHERE")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
