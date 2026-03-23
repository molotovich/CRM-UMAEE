import sqlite3
import pymysql
import os
import sys
from datetime import datetime

# Configuración: Ajustar según los detalles del VPS
SQLITE_DB = 'instance/crm.db'  # Usaremos la copia en la raíz
MYSQL_CONFIG = {
    'host': 'localhost',  # Cambiar por la IP del VPS si se corre localmente
    'user': 'crm_user',
    'password': 'your_password',
    'database': 'crm_umaee',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def migrate():
    if not os.path.exists(SQLITE_DB):
        print(f"Error: No se encontró {SQLITE_DB}")
        return

    print(f"Iniciando migración desde {SQLITE_DB} a MySQL...")
    
    # Conectar a SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # Conectar a MySQL
    try:
        mysql_conn = pymysql.connect(**MYSQL_CONFIG)
        mysql_cur = mysql_conn.cursor()
    except Exception as e:
        print(f"Error conectando a MySQL: {e}")
        return

    # Tablas en orden de dependencia
    tables = [
        'crm_escuelas',
        'crm_carreras',
        'crm_periodos',
        'crm_turnos',
        'usuarios',
        'crm_ofertas_academicas',
        'crm_metas_vendedores',
        'prospectos',
        'crm_seguimiento'
    ]

    try:
        # Desactivar checks de llaves foráneas temporalmente
        mysql_cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        for table in tables:
            print(f"Migrando tabla: {table}...")
            
            # Limpiar tabla destino (opcional, comentar si se quieren conservar datos)
            mysql_cur.execute(f"TRUNCATE TABLE {table};")
            
            # Leer de SQLite
            sqlite_cur.execute(f"SELECT * FROM {table}")
            rows = sqlite_cur.fetchall()
            
            if not rows:
                print(f"  Tabla {table} vacía.")
                continue

            # Preparar inserción en MySQL
            columns = rows[0].keys()
            placeholders = ", ".join(["%s"] * len(columns))
            cols_str = ", ".join(columns)
            insert_sql = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
            
            data_to_insert = []
            for row in rows:
                data_to_insert.append(tuple(row))
            
            mysql_cur.executemany(insert_sql, data_to_insert)
            print(f"  {len(rows)} registros migrados.")

        # Reactivar checks de llaves foráneas
        mysql_cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        mysql_conn.commit()
        print("\nMigración completada con éxito.")

    except Exception as e:
        print(f"\nError durante la migración: {e}")
        mysql_conn.rollback()
    finally:
        sqlite_conn.close()
        mysql_conn.close()

if __name__ == "__main__":
    # Opcional: Permitir pasar el host de MySQL por argumento
    if len(sys.argv) > 1:
        MYSQL_CONFIG['host'] = sys.argv[1]
    
    migrate()
