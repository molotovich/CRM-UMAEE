import sqlite3
import os

db_path = os.path.join('instance', 'crm.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS crm_metas_vendedores (
    id_meta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    periodo_mes VARCHAR(7) NOT NULL,
    meta_contactos INTEGER DEFAULT 0,
    meta_inscritos INTEGER DEFAULT 0,
    UNIQUE(id_usuario, periodo_mes)
)''')

conn.commit()
conn.close()
print("Table created.")
