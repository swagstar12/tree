import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute("ALTER TABLE answers ADD COLUMN date TEXT")
conn.commit()
conn.close()
print("Column 'date' added successfully.")
