from app import create_app
from models import db, Prospecto, Seguimiento, EscuelaProcedencia, Usuario
from datetime import datetime, date

app = create_app()

with app.app_context():
    # Recreate database with new schema
    db.drop_all()
    db.create_all()

    # Initial Users (Salespeople)
    u1 = Usuario(nombre_completo="Elena Rodriguez", email="elena@umaee.edu.mx", rol="VENDEDOR")
    u2 = Usuario(nombre_completo="Marcos Sanchez", email="marcos@umaee.edu.mx", rol="VENDEDOR")
    u3 = Usuario(nombre_completo="Admin General", email="admin@umaee.edu.mx", rol="SUPERADMIN")
    db.session.add_all([u1, u2, u3])
    db.session.commit()

    # Initial Schools
    e1 = EscuelaProcedencia(nombre_escuela="Preparatoria Estatal No. 1")
    e2 = EscuelaProcedencia(nombre_escuela="Colegio de Bachilleres (COBAY)")
    e3 = EscuelaProcedencia(nombre_escuela="CETIS 112")
    db.session.add_all([e1, e2, e3])
    db.session.commit()

    # Sample Prospects
    p1 = Prospecto(
        nombre='Juan Alberto', 
        apellido_paterno='Perez', 
        apellido_materno='Gomez',
        sexo='M',
        fecha_captura=date.today(),
        turno='MATUTINO',
        email='juan.perez@ejemplo.com', 
        telefono='9991234567',
        id_escuela=e1.id_escuela,
        semestre=6,
        promedio=8.5,
        carrera_interes='Derecho',
        fase_crm='NUEVO',
        origen_prospecto='WEB',
        id_vendedor_asignado=u1.id_usuario
    )
    
    p2 = Prospecto(
        nombre='Maria', 
        apellido_paterno='Lopez', 
        apellido_materno='Ruiz',
        sexo='F',
        fecha_captura=date.today(),
        turno='VESPERTINO',
        email='maria.lopez@ejemplo.com', 
        telefono='9997654321',
        id_escuela=e2.id_escuela,
        semestre=6,
        promedio=9.0,
        carrera_interes='Medicina',
        fase_crm='CONTACTADO',
        origen_prospecto='SALONEO',
        id_vendedor_asignado=u2.id_usuario
    )

    p3 = Prospecto(
        nombre='Pedro', 
        apellido_paterno='Ramirez', 
        apellido_materno='Sosa',
        sexo='M',
        fecha_captura=date.today(),
        turno='MATUTINO',
        email='pedro.ramirez@ejemplo.com', 
        telefono='9990001122',
        id_escuela=e3.id_escuela,
        semestre=6,
        promedio=7.5,
        carrera_interes='Ingeniería',
        fase_crm='PERDIDO',
        origen_prospecto='TELEFONO',
        id_vendedor_asignado=u1.id_usuario,
        razon_perdido='Inscrito en otra universidad'
    )

    db.session.add_all([p1, p2, p3])
    db.session.commit()

    # Add a follow-up for p2
    s1 = Seguimiento(
        id_prospecto=p2.id_prospecto,
        tipo_contacto='LLAMADA',
        comentarios='Interesada en becas, se le envió info por correo.'
    )
    db.session.add(s1)
    db.session.commit()
    
    print("Database recreated and seed data created successfully.")
