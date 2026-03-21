import sqlite3
import os
db_path = os.path.join('instance', 'crm.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS crm_turnos (
    id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE
)''')

turnos = ['MATUTINO', 'VESPERTINO', 'SABATINO', 'SABATINO VESPERTINO', 'DOMINICAL', 'DOMINICAL VESPERTINO']
for t in turnos:
    try:
        c.execute("INSERT INTO crm_turnos (nombre) VALUES (?)", (t,))
    except sqlite3.IntegrityError:
        pass

try:
    c.execute("ALTER TABLE crm_ofertas_academicas ADD COLUMN id_turno INTEGER REFERENCES crm_turnos(id_turno) DEFAULT 1")
except sqlite3.OperationalError:
    pass

conn.commit()
conn.close()
print('DB fields added')
