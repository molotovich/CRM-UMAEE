from app import create_app
from models import db, Usuario

app = create_app()
with app.app_context():
    u = Usuario.query.filter_by(email='dev@umaee.edu.mx').first()
    if not u:
        u = Usuario(nombre_completo='Desarrollador (Test)', email='dev@umaee.edu.mx', rol='SUPERADMIN')
        u.set_password('dev123')
        db.session.add(u)
        db.session.commit()
        print("Created dev account: dev@umaee.edu.mx / dev123")
    else:
        u.rol = 'SUPERADMIN'
        u.set_password('dev123')
        db.session.commit()
        print("Updated dev account: dev@umaee.edu.mx / dev123")
