-- Script de configuración para MySQL - CRM UMAEE
CREATE DATABASE IF NOT EXISTS crm_umaee;
USE crm_umaee;

-- Definición de Tablas

CREATE TABLE IF NOT EXISTS crm_escuelas (
    id_escuela INT AUTO_INCREMENT PRIMARY KEY,
    nombre_escuela VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS crm_carreras (
    id_carrera INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS crm_periodos (
    id_periodo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS crm_turnos (
    id_turno INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS crm_ofertas_academicas (
    id_oferta INT AUTO_INCREMENT PRIMARY KEY,
    id_carrera INT NOT NULL,
    id_periodo INT NOT NULL,
    id_turno INT,
    costo FLOAT NOT NULL,
    FOREIGN KEY (id_carrera) REFERENCES crm_carreras(id_carrera) ON DELETE CASCADE,
    FOREIGN KEY (id_periodo) REFERENCES crm_periodos(id_periodo) ON DELETE CASCADE,
    FOREIGN KEY (id_turno) REFERENCES crm_turnos(id_turno) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(255) NOT NULL,
    email VARCHAR(150) UNIQUE,
    rol VARCHAR(50) DEFAULT 'VENDEDOR',
    password_hash VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS crm_metas_vendedores (
    id_meta INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    periodo_mes VARCHAR(7) NOT NULL,
    meta_contactos INT DEFAULT 0,
    meta_inscritos INT DEFAULT 0,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS prospectos (
    id_prospecto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100),
    sexo VARCHAR(20),
    fecha_captura DATE,
    turno VARCHAR(50),
    email VARCHAR(150),
    telefono VARCHAR(20),
    id_escuela INT,
    semestre INT,
    promedio FLOAT,
    carrera_interes VARCHAR(100),
    fase_crm VARCHAR(50) DEFAULT 'NUEVO',
    origen_prospecto VARCHAR(50),
    id_vendedor_asignado INT,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    razon_perdido TEXT,
    id_oferta_inscripcion INT,
    FOREIGN KEY (id_escuela) REFERENCES crm_escuelas(id_escuela) ON DELETE SET NULL,
    FOREIGN KEY (id_vendedor_asignado) REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_oferta_inscripcion) REFERENCES crm_ofertas_academicas(id_oferta) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS crm_seguimiento (
    id_seguimiento INT AUTO_INCREMENT PRIMARY KEY,
    id_prospecto INT,
    tipo_contacto VARCHAR(50),
    comentarios TEXT NOT NULL,
    proxima_accion_fecha DATE,
    proxima_accion_nota VARCHAR(255),
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_prospecto) REFERENCES prospectos(id_prospecto) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Usuario Superadministrador Inicial
-- Usuario: admin@umaee.com
-- Contraseña: 123umaee

INSERT INTO usuarios (nombre_completo, email, rol, password_hash) 
VALUES ('Super Administrador', 'admin@umaee.com', 'SUPERADMIN', 'scrypt:32768:8:1$wjEQfl1vcLIjtFhM$be35d4a677d5cc970f8d032ff70c995011346af51d288ade1287e25474bc3367b3dbffb562b11392fc403f238c4147f553ac0a9911e2dbd43cb6e50789f0f052');
