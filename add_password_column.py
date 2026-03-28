import sqlite3

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE members ADD COLUMN password_hash TEXT")

conn.commit()
conn.close()

print("Column added successfully.")