import sqlite3

conn = sqlite3.connect('normalisasi.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS normalisasi')
conn.commit()
conn.close()