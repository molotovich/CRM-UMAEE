from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class EscuelaProcedencia(db.Model):
    __tablename__ = 'crm_escuelas'
    id_escuela = db.Column(db.Integer, primary_key=True)
    nombre_escuela = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'id_escuela': self.id_escuela,
            'nombre_escuela': self.nombre_escuela
        }

class Carrera(db.Model):
    __tablename__ = 'crm_carreras'
    id_carrera = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, unique=True)

    def to_dict(self):
        return {
            'id_carrera': self.id_carrera,
            'nombre': self.nombre
        }

class Periodo(db.Model):
    __tablename__ = 'crm_periodos'
    id_periodo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, unique=True)

    def to_dict(self):
        return {
            'id_periodo': self.id_periodo,
            'nombre': self.nombre
        }

class Turno(db.Model):
    __tablename__ = 'crm_turnos'
    id_turno = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)

    def to_dict(self):
        return {
            'id_turno': self.id_turno,
            'nombre': self.nombre
        }

class OfertaAcademica(db.Model):
    __tablename__ = 'crm_ofertas_academicas'
    id_oferta = db.Column(db.Integer, primary_key=True)
    id_carrera = db.Column(db.Integer, db.ForeignKey('crm_carreras.id_carrera'), nullable=False)
    id_periodo = db.Column(db.Integer, db.ForeignKey('crm_periodos.id_periodo'), nullable=False)
    id_turno = db.Column(db.Integer, db.ForeignKey('crm_turnos.id_turno'), nullable=True)
    costo = db.Column(db.Float, nullable=False)

    carrera = db.relationship('Carrera', backref='ofertas', lazy=True)
    periodo = db.relationship('Periodo', backref='ofertas', lazy=True)
    turno = db.relationship('Turno', backref='ofertas', lazy=True)

    def to_dict(self):
        return {
            'id_oferta': self.id_oferta,
            'id_carrera': self.id_carrera,
            'id_periodo': self.id_periodo,
            'id_turno': self.id_turno,
            'carrera_nombre': self.carrera.nombre if self.carrera else None,
            'periodo_nombre': self.periodo.nombre if self.periodo else None,
            'turno_nombre': self.turno.nombre if hasattr(self, 'turno') and self.turno else None,
            'costo': self.costo
        }

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(150), unique=True)
    rol = db.Column(db.String(50), default='VENDEDOR') # SUPERADMIN, ADMIN, VENDEDOR
    password_hash = db.Column(db.String(255))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'nombre_completo': self.nombre_completo,
            'email': self.email,
            'rol': self.rol
        }

class MetaVendedor(db.Model):
    __tablename__ = 'crm_metas_vendedores'
    id_meta = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    periodo_mes = db.Column(db.String(7), nullable=False) # e.g. "2026-03"
    meta_contactos = db.Column(db.Integer, default=0)
    meta_inscritos = db.Column(db.Integer, default=0)

    vendedor = db.relationship('Usuario', backref='metas', lazy=True)

    def to_dict(self):
        return {
            'id_meta': self.id_meta,
            'id_usuario': self.id_usuario,
            'vendedor_nombre': self.vendedor.nombre_completo if self.vendedor else None,
            'periodo_mes': self.periodo_mes,
            'meta_contactos': self.meta_contactos,
            'meta_inscritos': self.meta_inscritos
        }

class Prospecto(db.Model):
    __tablename__ = 'prospectos'
    id_prospecto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(100), nullable=False)
    apellido_materno = db.Column(db.String(100))
    sexo = db.Column(db.String(20)) # M / F / OTRO
    curp = db.Column(db.String(18))
    fecha_captura = db.Column(db.Date) # Date of data entry
    turno = db.Column(db.String(50)) # MATUTINO / VESPERTINO
    email = db.Column(db.String(150), index=True)
    telefono = db.Column(db.String(20), index=True)
    id_escuela = db.Column(db.Integer, db.ForeignKey('crm_escuelas.id_escuela'))
    semestre = db.Column(db.Integer)
    promedio = db.Column(db.Float)
    carrera_interes = db.Column(db.String(100))
    carrera_interes_2 = db.Column(db.String(100))
    carrera_interes_3 = db.Column(db.String(100))
    periodo_interes = db.Column(db.String(100))
    turno_interes = db.Column(db.String(50))
    tutor_nombre = db.Column(db.String(255))
    tutor_email = db.Column(db.String(150))
    tutor_telefono = db.Column(db.String(20))
    fecha_cita = db.Column(db.DateTime)
    fase_crm = db.Column(db.String(50), default='NUEVO', index=True)
    origen_prospecto = db.Column(db.String(50))
    id_vendedor_asignado = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), index=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    razon_perdido = db.Column(db.Text)
    id_oferta_inscripcion = db.Column(db.Integer, db.ForeignKey('crm_ofertas_academicas.id_oferta'))

    seguimientos = db.relationship('Seguimiento', backref='prospecto', lazy=True, order_by="desc(Seguimiento.fecha_creacion)")
    vendedor = db.relationship('Usuario', backref='prospectos_asignados', lazy=True)
    oferta_inscripcion = db.relationship('OfertaAcademica', backref='prospectos_inscritos', lazy=True)

    def to_dict(self):
        # Get latest follow-up
        ultimo = self.seguimientos[0].fecha_creacion.isoformat() if self.seguimientos else None
        
        return {
            'id_prospecto': self.id_prospecto,
            'nombre': f"{self.nombre} {self.apellido_paterno} {self.apellido_materno or ''}".strip(),
            'nombre_solo': self.nombre,
            'apellido_paterno': self.apellido_paterno,
            'apellido_materno': self.apellido_materno,
            'sexo': self.sexo,
            'curp': self.curp,
            'fecha_captura': self.fecha_captura.isoformat() if self.fecha_captura else None,
            'turno': self.turno,
            'email': self.email,
            'telefono': self.telefono,
            'id_escuela': self.id_escuela,
            'escuela': self.prospecto_escuela.nombre_escuela if hasattr(self, 'prospecto_escuela') and self.prospecto_escuela else None,
            'semestre': self.semestre,
            'promedio': self.promedio,
            'carrera_interes': self.carrera_interes,
            'carrera_interes_2': self.carrera_interes_2,
            'carrera_interes_3': self.carrera_interes_3,
            'periodo_interes': self.periodo_interes,
            'turno_interes': self.turno_interes,
            'tutor_nombre': self.tutor_nombre,
            'tutor_email': self.tutor_email,
            'tutor_telefono': self.tutor_telefono,
            'fase_crm': self.fase_crm,
            'origen_prospecto': self.origen_prospecto,
            'id_vendedor_asignado': self.id_vendedor_asignado,
            'vendedor_nombre': self.vendedor.nombre_completo if self.vendedor else "Sin asignar",
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'razon_perdido': self.razon_perdido,
            'ultimo_seguimiento': ultimo,
            'fecha_cita': self.fecha_cita.isoformat() if self.fecha_cita else None,
            'id_oferta_inscripcion': self.id_oferta_inscripcion,
            'oferta_carrera': self.oferta_inscripcion.carrera.nombre if self.oferta_inscripcion and self.oferta_inscripcion.carrera else None,
            'oferta_periodo': self.oferta_inscripcion.periodo.nombre if self.oferta_inscripcion and self.oferta_inscripcion.periodo else None,
            'oferta_turno': self.oferta_inscripcion.turno.nombre if self.oferta_inscripcion and hasattr(self.oferta_inscripcion, 'turno') and self.oferta_inscripcion.turno else None,
            'oferta_costo': self.oferta_inscripcion.costo if self.oferta_inscripcion else None
        }

# Update relationship in Prospecto to access Escuela name
Prospecto.prospecto_escuela = db.relationship('EscuelaProcedencia', backref='prospectos', lazy=True, foreign_keys=[Prospecto.id_escuela])

class Seguimiento(db.Model):
    __tablename__ = 'crm_seguimiento'
    id_seguimiento = db.Column(db.Integer, primary_key=True)
    id_prospecto = db.Column(db.Integer, db.ForeignKey('prospectos.id_prospecto'), index=True)
    tipo_contacto = db.Column(db.String(50))
    comentarios = db.Column(db.Text, nullable=False)
    proxima_accion_fecha = db.Column(db.Date)
    proxima_accion_nota = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id_seguimiento': self.id_seguimiento,
            'id_prospecto': self.id_prospecto,
            'tipo_contacto': self.tipo_contacto,
            'comentarios': self.comentarios,
            'proxima_accion_fecha': self.proxima_accion_fecha.isoformat() if self.proxima_accion_fecha else None,
            'proxima_accion_nota': self.proxima_accion_nota,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
