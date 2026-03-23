-- CRM UMAEE - Esquema de Base de Datos (SQLite)

-- Tabla de Escuelas de Procedencia
CREATE TABLE IF NOT EXISTS crm_escuelas (
    id_escuela INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_escuela TEXT NOT NULL
);

-- Tabla de Carreras
CREATE TABLE IF NOT EXISTS crm_carreras (
    id_carrera INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

-- Tabla de Periodos
CREATE TABLE IF NOT EXISTS crm_periodos (
    id_periodo INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

-- Tabla de Turnos
CREATE TABLE IF NOT EXISTS crm_turnos (
    id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

-- Tabla de Ofertas Académicas
CREATE TABLE IF NOT EXISTS crm_ofertas_academicas (
    id_oferta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_carrera INTEGER NOT NULL,
    id_periodo INTEGER NOT NULL,
    id_turno INTEGER,
    costo REAL NOT NULL,
    FOREIGN KEY (id_carrera) REFERENCES crm_carreras (id_carrera),
    FOREIGN KEY (id_periodo) REFERENCES crm_periodos (id_periodo),
    FOREIGN KEY (id_turno) REFERENCES crm_turnos (id_turno)
);

-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    email TEXT UNIQUE,
    rol TEXT DEFAULT 'VENDEDOR',
    password_hash TEXT
);

-- Tabla de Metas de Vendedores
CREATE TABLE IF NOT EXISTS crm_metas_vendedores (
    id_meta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    periodo_mes TEXT NOT NULL,
    meta_contactos INTEGER DEFAULT 0,
    meta_inscritos INTEGER DEFAULT 0,
    FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
);

-- Tabla de Prospectos
CREATE TABLE IF NOT EXISTS prospectos (
    id_prospecto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido_paterno TEXT NOT NULL,
    apellido_materno TEXT,
    sexo TEXT,
    curp TEXT,
    fecha_captura DATE,
    turno TEXT,
    email TEXT,
    telefono TEXT,
    id_escuela INTEGER,
    semestre INTEGER,
    promedio REAL,
    carrera_interes TEXT,
    carrera_interes_2 TEXT,
    carrera_interes_3 TEXT,
    periodo_interes TEXT,
    turno_interes TEXT,
    tutor_nombre TEXT,
    tutor_email TEXT,
    tutor_telefono TEXT,
    fecha_cita DATETIME,
    fase_crm TEXT DEFAULT 'NUEVO',
    origen_prospecto TEXT,
    id_vendedor_asignado INTEGER,
    fecha_register DATETIME DEFAULT CURRENT_TIMESTAMP,
    razon_perdido TEXT,
    id_oferta_inscripcion INTEGER,
    FOREIGN KEY (id_escuela) REFERENCES crm_escuelas (id_escuela),
    FOREIGN KEY (id_vendedor_asignado) REFERENCES usuarios (id_usuario),
    FOREIGN KEY (id_oferta_inscripcion) REFERENCES crm_ofertas_academicas (id_oferta)
);
CREATE INDEX IF NOT EXISTS idx_prospectos_email ON prospectos(email);
CREATE INDEX IF NOT EXISTS idx_prospectos_telefono ON prospectos(telefono);
CREATE INDEX IF NOT EXISTS idx_prospectos_fase ON prospectos(fase_crm);

-- Tabla de Seguimientos
CREATE TABLE IF NOT EXISTS crm_seguimiento (
    id_seguimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_prospecto INTEGER,
    tipo_contacto TEXT,
    comentarios TEXT NOT NULL,
    proxima_accion_fecha DATE,
    proxima_accion_nota TEXT,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_prospecto) REFERENCES prospectos (id_prospecto)
);
CREATE INDEX IF NOT EXISTS idx_seguimiento_prospecto ON crm_seguimiento(id_prospecto);

-- Insertar Usuario Administrador por defecto (admin@umaee.edu.mx / 123umaee)
-- Hash generado para '123umaee' usando werkzeug.security
INSERT OR IGNORE INTO usuarios (nombre_completo, email, rol, password_hash) 
VALUES ('Administrador Sistema', 'admin@umaee.edu.mx', 'SUPERADMIN', 'pbkdf2:sha256:600000$pEwTq0Yv1v3y$37c37c37c37c37c37c37c37c37c37c37c37c37c37c37c37c37c37c37c37c');
-- Nota: El hash de arriba es un placeholder, en el arranque real el sistema lo generará o validará via Python.
