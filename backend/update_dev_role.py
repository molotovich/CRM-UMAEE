from app import create_app
from models import db, Usuario

app = create_app()
with app.app_context():
    u = Usuario.query.filter_by(email='dev@umaee.edu.mx').first()
    if not u:
        u = Usuario(nombre_completo='Desarrollador (Test)', email='dev@umaee.edu.mx', rol='DESARROLLADOR')
        u.set_password('dev123')
        db.session.add(u)
        db.session.commit()
        print("Created dev account with role DESARROLLADOR")
    else:
        u.rol = 'DESARROLLADOR'
        db.session.commit()
        print("Updated dev account to role DESARROLLADOR")
