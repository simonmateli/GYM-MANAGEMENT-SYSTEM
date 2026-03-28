import sqlite3

# Connect to your database
conn = sqlite3.connect('gym.db') # Make sure this matches your DB filename
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE admin_users ADD COLUMN email TEXT")
    conn.commit()
    print("Column 'email' added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")

conn.close()