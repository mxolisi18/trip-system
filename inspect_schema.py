import sqlite3
conn = sqlite3.connect('backend/instance/trip.db')
c = conn.cursor()
c.execute("PRAGMA table_info(user);")
print(c.fetchall())
